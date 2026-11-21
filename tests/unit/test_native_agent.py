"""Phase C: native tool agent + OpenAI tool schema."""

from __future__ import annotations

from typing import Any, Dict, List

from ami.llm.native_agent import NativeToolAgent, client_supports_native_tools
from ami.llm.tool_schema import headspace_tools_to_openai


class _Tool:
    def __init__(self, name: str, description: str, arg_schema: dict, method):
        self.name = name
        self.description = description
        self.arg_schema = arg_schema
        self.method = method


class _MockNativeClient:
    def __init__(self, script: List[Dict[str, Any]]):
        self.script = list(script)
        self.calls = 0

    def chat_with_tools(self, messages, tools, **kwargs):
        if not self.script:
            return {"content": "done", "tool_calls": []}
        step = self.script.pop(0)
        self.calls += 1
        return step


def test_headspace_tools_to_openai_shape():
    tools = [
        _Tool(
            "ping",
            "Ping tool",
            {"msg": {"type": "string", "required": True}},
            lambda msg: f"p:{msg}",
        )
    ]
    openai = headspace_tools_to_openai(tools)
    assert openai[0]["type"] == "function"
    assert openai[0]["function"]["name"] == "ping"
    assert "msg" in openai[0]["function"]["parameters"]["properties"]
    assert "msg" in openai[0]["function"]["parameters"]["required"]


def test_native_agent_runs_tool_then_finishes(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # Config uses home .ami for convos
    from ami.core.config import Config

    Config._instance = None
    Config._file_observer = None
    Config._count = 0

    def ping(msg: str) -> str:
        return f"pong:{msg}"

    tools = [
        _Tool("ping", "echo", {"msg": {"type": "string", "required": True}}, ping),
    ]
    client = _MockNativeClient(
        [
            {
                "content": None,
                "tool_calls": [{"id": "1", "name": "ping", "arguments": {"msg": "hi"}}],
            },
            {"content": "All set.", "tool_calls": []},
        ]
    )
    assert client_supports_native_tools(client)
    agent = NativeToolAgent(client, "testspace")
    result = agent.run("ping hi", tools, max_steps=4)
    assert any(s.get("action", {}).get("action") == "ping" for s in result.steps)
    assert any("pong:hi" in str(s.get("observation", "")) for s in result.steps)
    assert result.steps[-1]["action"]["action"] == "TASK COMPLETE"


def test_provider_factory_prefers_native(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from ami.core.config import Config

    Config._instance = None
    Config._file_observer = None
    Config._count = 0

    from ami.llm.provider import LLMProvider
    from ami.llm.native_agent import NativeToolAgent

    class _C:
        def chat_with_tools(self, *a, **k):
            return {"content": "x", "tool_calls": []}

        logs = type("L", (), {"debug": lambda *a, **k: None})()

    p = LLMProvider(_C())
    agent = p.as_funccalling_toa_agent("corespace")
    assert isinstance(agent, NativeToolAgent)
