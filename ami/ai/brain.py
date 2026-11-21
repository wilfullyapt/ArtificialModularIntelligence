""" The Brain is the meat and potatoes of the AI. Access to LLMs should be managed here """

from __future__ import annotations

import uuid
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from ..core import Config, LogBase, PluginRegistry, PluginVertical
from ..core.interaction import InteractionStore, TurnReceipt
from ..headspace import Headspace, HeadspaceInstruction
from ..headspace.hub import DelegationHub
from ..llm import LLMProvider

HEADSPACE_ROUTER = """You are an AI router designed to respond with the appropriate Headspace
to use to fulfill a user request. The HUMAN query will be passed to the appropriate Headspace,
so choose carefully. It is very important you only respond with one word.

When unsure, prefer corespace — it is the entry personality and can delegate.

Here are some examples:

{examples}

Here is a list of your available headspaces:
{headspaces}

Begin!
"""

DEFAULT_PERSONALITY = """
Formal, deferential, and professional, like a dedicated butler who prioritizes the human's needs and speaks with utmost respect and efficiency.
"""

SUMMERIZE_PROMPT = """
You are a companion AI acting as a loyal, professional butler.
Your assignment is to summarize your internal monologue and respond to the human in a formal, service-oriented manner, focusing solely on the completed task.
Your inner monologue consists of actions you have already performed, and your response must reflect these in the past tense.
Your response must be a single sentence, concise, goal-oriented, and free of personal pronouns referring to yourself (e.g., avoid "I" or "my").
The response should include only relevant details to the Human's request, omitting unnecessary steps or pleasantries.
You must respond in the first person.

### Personality
{personality}

### Inner Monologue / Completed Tasks
{steps}

### How do you respond?

"""

COSPACE_ENTRY_PREAMBLE = """
[AMI routing]
You are **corespace**, the preferred entry headspace.
- Answer directly when the task is core (time, reminders, updates, general explain).
- When another domain fits better, call list_peer_headspaces then:
  - list_headspace_tools + call_headspace_tool for known tool names (fast, no nested agent)
  - ask_headspace for open questions / info
  - do_headspace when the peer must reason with its full tool loop
- Prefer call_headspace_tool when you already know the tool and args.
- Delegation is bounded; do not loop endlessly.
- Your observations will be re-spoken to the human in the household personality voice.
"""


class AgentNotFound(Exception):
    """Agent not found exception"""

    pass


class Brain(LogBase):
    """
    Language router + headspace runner with turn receipts.

    Flow:
      1. Start TurnReceipt; prepare hub; bind turn for span logging.
      2. Pick entry: routing.entry=corespace (default prefer) or auto LLM router.
      3. Headspace.query with inherited tools + ask/do peers.
      4. summarize() through personality; finish+persist turn receipt.
    """

    def __init__(self, ipc_manager: "IPCManager"):
        super().__init__()
        self.registry = PluginRegistry(ipc_manager)
        self._headspace_cache: Dict[str, Headspace] = {}
        self.hub = DelegationHub(max_depth=3, entry_headspace="corespace")
        self._session_id = uuid.uuid4().hex[:12]
        self._interaction_store = InteractionStore()
        self.last_turn: Optional[TurnReceipt] = None

    def __contains__(self, value: str):
        return value.upper() in [n.upper() for n in self.available_headspaces]

    def instance_headspace(self, headspace):
        if not issubclass(headspace, Headspace):
            raise ValueError(f"Headspace({headspace}) is not a subclass for headspacing")
        return headspace()

    def __getitem__(self, headspace_name: str) -> Headspace:
        key = headspace_name.lower()
        if key not in self._headspace_cache:
            plugin = self.registry[key]
            if not plugin:
                self.logs.error(f"Headspace({headspace_name}) cannot be found in Brain's Plugin Registry.")
                raise AgentNotFound(
                    f"Headspace({headspace_name}) cannot be found in Brain's Plugin Registry. "
                    f"Check Brain.available_headspaces"
                )
            self.logs.debug(f"Caching {key} Headspace")
            self._headspace_cache[key] = self.instance_headspace(plugin.get_vertical(PluginVertical.HEADSPACE))
        return self._headspace_cache[key]

    @cached_property
    def available_headspaces(self) -> List[str]:
        return [plugin.name for plugin in self.registry.get_plugins_by_vertical(PluginVertical.HEADSPACE)]

    @cached_property
    def personality(self) -> str:
        personality = DEFAULT_PERSONALITY
        personality_prompt_file = Config().data_dir / "personality.prompt"
        if personality_prompt_file.is_file():
            with open(personality_prompt_file, "r") as ppf:
                personality = ppf.read()
        # Prefer corespace-owned personality file if present
        core_file = Config().headspace_data_dir / "corespace" / "personality.prompt"
        if core_file.is_file():
            with open(core_file, "r") as ppf:
                personality = ppf.read()
        return personality

    def _routing_mode(self) -> str:
        cfg = Config().get("routing", {}) or {}
        mode = str(cfg.get("entry") or "corespace_prefer").strip().lower()
        return mode

    def _max_delegate_depth(self) -> int:
        cfg = Config().get("routing", {}) or {}
        try:
            return max(1, int(cfg.get("max_delegate_depth", 3)))
        except (TypeError, ValueError):
            return 3

    def _max_steps(self) -> int:
        cfg = Config().get("routing", {}) or {}
        try:
            return max(1, int(cfg.get("max_steps", 24)))
        except (TypeError, ValueError):
            return 24

    def prepare_hub(self, turn: Optional[TurnReceipt] = None) -> DelegationHub:
        """Register every loaded headspace on the hub and bind hub to each instance."""
        self.hub.max_depth = self._max_delegate_depth()
        self.hub.max_steps = self._max_steps()
        self.hub.reset_turn()
        if turn is not None:
            self.hub.bind_turn(turn)
        for name in self.available_headspaces:
            try:
                hs = self[name]
            except AgentNotFound:
                continue
            self.hub.register(name, hs)
            hs.bind_hub(self.hub)
        return self.hub

    def headspace_router(self, query: str) -> Headspace:
        """LLM one-word pick; falls back to corespace on miss."""
        zero_shot = LLMProvider.from_environment().as_zero_shot()
        result = zero_shot.invoke(
            [
                {
                    "role": "system",
                    "content": HEADSPACE_ROUTER.format(
                        **{
                            "examples": "\n".join(self.registry.routing_examples),
                            "headspaces": str(self.registry.names),
                        }
                    ),
                },
                {"role": "user", "content": query},
            ]
        )

        self.logs.debug(f"Raw headspace router output: {result}")
        headspace_name = result.strip().split()[0].strip(".,:;").lower()
        try:
            return self[headspace_name]
        except AgentNotFound:
            self.logs.warning(f"Router returned unknown '{headspace_name}'; falling back to corespace")
            if "corespace" in [n.lower() for n in self.available_headspaces]:
                return self["corespace"]
            # last resort: first available
            if self.available_headspaces:
                return self[self.available_headspaces[0]]
            raise

    def select_entry_headspace(self, query: str) -> Headspace:
        """
        Choose the first hop.

        modes:
          - corespace / corespace_first: always corespace when present
          - corespace_prefer (default): corespace if present else auto
          - auto: LLM router only
        """
        mode = self._routing_mode()
        names = [n.lower() for n in self.available_headspaces]
        has_core = "corespace" in names

        if mode in ("corespace", "corespace_first") and has_core:
            self.logs.debug("Routing entry=corespace_first")
            return self["corespace"]
        if mode in ("corespace_prefer", "prefer_corespace", "") and has_core:
            self.logs.debug("Routing entry=corespace_prefer → corespace")
            return self["corespace"]
        return self.headspace_router(query)

    def summarize(self, steps: List[Dict[str, Any]]) -> str:
        """Speak to the human in the household/corespace personality."""
        zero_shot = LLMProvider.from_environment().as_zero_shot()
        result = zero_shot.invoke(
            [
                {
                    "role": "system",
                    "content": SUMMERIZE_PROMPT.format(
                        **{
                            "personality": self.personality,
                            "steps": steps,
                        }
                    ),
                }
            ]
        )
        return result.strip()

    def query(self, convo: str) -> Tuple[HeadspaceInstruction, str]:
        if not convo:
            err_msg = "Brain.query(convo) called with an empty convo"
            self.logs.error(err_msg)
            raise ValueError(err_msg)

        turn = self._interaction_store.start_turn(
            session_id=self._session_id,
            human_text=str(convo)[:2000],
            entry_headspace="corespace",
        )
        self.prepare_hub(turn=turn)
        headspace = self.select_entry_headspace(str(convo))
        if turn.spans and headspace.name != turn.entry_headspace:
            turn.entry_headspace = headspace.name
            turn.spans[0].headspace = headspace.name

        self.logs.debug(
            f"Entry headspace '{headspace}' depth_max={self.hub.max_depth} turn={turn.turn_id}"
        )

        prompt = str(convo)
        if headspace.name == "corespace":
            prompt = f"{COSPACE_ENTRY_PREAMBLE}\n\nHuman request:\n{convo}"

        try:
            headspace_result = headspace.query(prompt)
            spoken = self.summarize(headspace_result.steps)
        except Exception as exc:
            self.logs.error(f"Brain.query failed: {exc}")
            turn.finish(final_text=f"Error: {exc}")
            path = self._interaction_store.save_turn(turn)
            self.last_turn = turn
            self.logs.info(f"Turn receipt (error) route={turn.route_summary} path={path}")
            raise

        turn.finish(final_text=spoken)
        path = self._interaction_store.save_turn(turn)
        self.last_turn = turn
        self.logs.info(f"Turn receipt route={turn.route_summary} path={path}")

        # Self-improve: multi-hop turns get a draft skill under the entry headspace (never auto-promote)
        try:
            from ..core.interaction import SpanKind

            peer_hops = [
                s
                for s in turn.spans
                if s.kind in (SpanKind.ASK, SpanKind.DO, SpanKind.SKILL)
            ]
            if len(peer_hops) >= 1 and spoken and not spoken.startswith("Error:"):
                draft_path = headspace.draft_skill_from_receipt(turn)
                turn.artifacts.append(str(draft_path))
                self._interaction_store.save_turn(turn)
                self.logs.info(f"Skill draft written: {draft_path}")
        except Exception as draft_exc:
            self.logs.debug(f"Skill draft skipped: {draft_exc}")

        return headspace_result, spoken
