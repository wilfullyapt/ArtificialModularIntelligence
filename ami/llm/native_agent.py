"""Native OpenAI-style tool-calling agent with TAO text fallback."""

from __future__ import annotations

import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core import Config, LogBase
from ..headspace import HeadspaceInstruction
from .tool_schema import headspace_tools_to_openai

NATIVE_SYSTEM = """You are an AMI headspace tool agent for domain '{name}'.
Use tools to fulfill the user request. Prefer the cheapest correct action:
1. Domain tools on this headspace when they fit.
2. list_headspace_tools + call_headspace_tool for known peer tools (no nested agent).
3. ask_headspace only for open questions; do_headspace only when the peer must multi-step reason.
When done, stop calling tools and give a short final answer (or empty if the last tool observation is enough).
"""


class NativeToolAgent(LogBase):
    """
    Loop using client.chat_with_tools(messages, openai_tools) when available.

    Expected return shape from chat_with_tools:
      {
        "content": str | None,
        "tool_calls": [ {"id": str, "name": str, "arguments": dict|str}, ... ]
      }
    """

    def __init__(self, client: Any, headspace_name: str):
        super().__init__()
        self.client = client
        self.name = headspace_name
        self.steps: List[Dict[str, Any]] = []
        self.logfile = Config().convos_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{headspace_name}_native.log"

    def _log_steps(self) -> None:
        try:
            with open(self.logfile, "w", encoding="utf-8") as f:
                json.dump(self.steps, f, indent=2, default=str)
        except OSError as exc:
            self.logs.error(f"Failed to write native agent log: {exc}")

    def _run_tool(self, tools: List[Any], name: str, arguments: Any) -> str:
        tool = next((t for t in tools if getattr(t, "name", None) == name), None)
        if tool is None:
            return f"Tool not found: {name}"
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError as exc:
                return f"Invalid tool arguments JSON: {exc}"
        if not isinstance(arguments, dict):
            arguments = {}
        try:
            result = tool.method(**arguments) if arguments else tool.method()
            if hasattr(result, "observation"):
                return str(result.observation)
            return str(result)
        except TypeError as exc:
            return f"Tool arg error: {exc}"
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"

    def run(self, prompt: str, tools: List[Any], max_steps: int = 6) -> HeadspaceInstruction:
        openai_tools = headspace_tools_to_openai(tools)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": NATIVE_SYSTEM.format(name=self.name)},
            {"role": "user", "content": prompt},
        ]
        self.steps = []

        try:
            for _ in range(max_steps):
                resp = self.client.chat_with_tools(messages, openai_tools)
                content = (resp or {}).get("content")
                tool_calls = (resp or {}).get("tool_calls") or []
                if not tool_calls:
                    if content:
                        self.steps.append(
                            {
                                "thought": "final",
                                "action": {"action": "TASK COMPLETE"},
                                "observation": str(content).strip(),
                            }
                        )
                    else:
                        self.steps.append(
                            {
                                "thought": "final",
                                "action": {"action": "TASK COMPLETE"},
                                "observation": self.steps[-1]["observation"]
                                if self.steps
                                else "Task complete",
                            }
                        )
                    break

                # Assistant turn with tool calls
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": [],
                }
                for i, tc in enumerate(tool_calls):
                    tc_id = tc.get("id") or f"call_{i}"
                    name = tc.get("name") or ""
                    args = tc.get("arguments") or {}
                    assistant_msg["tool_calls"].append(
                        {
                            "id": tc_id,
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": args if isinstance(args, str) else json.dumps(args),
                            },
                        }
                    )
                messages.append(assistant_msg)

                for i, tc in enumerate(tool_calls):
                    tc_id = tc.get("id") or f"call_{i}"
                    name = tc.get("name") or ""
                    args = tc.get("arguments") or {}
                    obs = self._run_tool(tools, name, args)
                    self.steps.append(
                        {
                            "thought": f"native tool {name}",
                            "action": {"action": name, "args": args if isinstance(args, dict) else {}},
                            "observation": obs,
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "content": obs,
                        }
                    )
            else:
                self.logs.warning("Native agent max_steps reached")
                if self.steps and self.steps[-1].get("action", {}).get("action") != "TASK COMPLETE":
                    self.steps.append(
                        {
                            "thought": "max steps",
                            "action": {"action": "TASK COMPLETE"},
                            "observation": self.steps[-1].get("observation", "Max steps"),
                        }
                    )
        except Exception as exc:
            traceback.print_exc()
            self.logs.error(f"Native tool agent error: {exc}")
            self.steps.append(
                {
                    "thought": "error",
                    "action": {"action": "TASK COMPLETE"},
                    "observation": f"Native agent error: {exc}",
                }
            )
        finally:
            self._log_steps()

        return HeadspaceInstruction.from_steps(self.steps, self.name)


def client_supports_native_tools(client: Any) -> bool:
    return callable(getattr(client, "chat_with_tools", None))
