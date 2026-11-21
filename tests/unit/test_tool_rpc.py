"""P3: direct headspace tool RPC (no nested agent loop)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ami.core.interaction import InteractionStore, SpanKind
from ami.headspace.headspace import Headspace, ami_tool, collect_tool_methods
from ami.headspace.headspace_instructions import HeadspaceInstruction
from ami.headspace.hub import DelegationHub


class _Worker(Headspace):
    @ami_tool
    def ping(self, msg: str) -> str:
        """Echo a message."""
        return f"pong:{msg}"

    @ami_tool
    def add(self, a: int, b: int) -> str:
        """Add two ints."""
        return str(a + b)

    def query(self, prompt: str) -> HeadspaceInstruction:
        # Should NOT be called by call_tool
        return HeadspaceInstruction(
            instructions=[],
            observation=f"FULL_AGENT:{prompt}",
            name="worker",
            steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "q"}],
        )


class _Entry(Headspace):
    @ami_tool
    def local_only(self, x: str) -> str:
        """Local tool."""
        return f"local:{x}"


def test_hub_call_tool_invokes_method_without_query(tmp_path: Path):
    store = InteractionStore(root=tmp_path)
    turn = store.start_turn(session_id="s", human_text="ping", entry_headspace="entry")
    hub = DelegationHub(max_depth=3)
    hub.bind_turn(turn)

    worker = _Worker.__new__(_Worker)
    _Worker._hs_name = "worker"
    entry = _Entry.__new__(_Entry)
    _Entry._hs_name = "entry"
    hub.register("worker", worker)
    hub.register("entry", entry)

    result = hub.call_tool("worker", "ping", {"msg": "hi"}, from_headspace="entry")
    assert result.ok
    assert result.kind == "tool"
    assert result.observation == "pong:hi"
    assert result.steps == 1
    # must not have run full agent
    assert "FULL_AGENT" not in result.observation
    assert any(s.kind == SpanKind.TOOL for s in turn.spans)
    assert "worker" in turn.route_summary or "ping" in turn.route_summary


def test_hub_call_tool_unknown_tool_and_headspace():
    hub = DelegationHub()
    worker = _Worker.__new__(_Worker)
    hub.register("worker", worker)

    r = hub.call_tool("nope", "ping", {"msg": "x"})
    assert r.ok is False
    assert "Unknown" in r.observation

    r2 = hub.call_tool("worker", "missing", {})
    assert r2.ok is False
    assert "ping" in r2.observation or "not found" in r2.observation.lower()


def test_hub_call_tool_parses_json_args_string(tmp_path: Path):
    hub = DelegationHub()
    worker = _Worker.__new__(_Worker)
    hub.register("worker", worker)
    r = hub.call_tool("worker", "add", '{"a": 2, "b": 3}')
    assert r.ok
    assert r.observation == "5"


def test_hub_call_tool_refuses_peer_meta_tools():
    hub = DelegationHub()
    worker = _Worker.__new__(_Worker)
    hub.register("worker", worker)
    # worker inherits ask_headspace etc.
    r = hub.call_tool("worker", "ask_headspace", {"headspace_name": "x", "question": "y"})
    assert r.ok is False
    assert "refused" in r.observation.lower() or "meta" in r.observation.lower() or "not allowed" in r.observation.lower()


def test_headspace_call_headspace_tool_ami_tool(tmp_path: Path):
    hub = DelegationHub()
    turn = InteractionStore(root=tmp_path).start_turn(
        session_id="t", human_text="x", entry_headspace="entry"
    )
    hub.bind_turn(turn)

    worker = _Worker.__new__(_Worker)
    entry = _Entry.__new__(_Entry)
    hub.register("worker", worker)
    hub.register("entry", entry)
    entry.bind_hub(hub)

    names = {m.__name__ for m in collect_tool_methods(entry)}
    assert "call_headspace_tool" in names
    assert "list_headspace_tools" in names

    listed = entry.list_headspace_tools("worker")
    assert "ping" in listed
    assert "add" in listed

    out = entry.call_headspace_tool("worker", "ping", '{"msg": "z"}')
    assert "pong:z" in out
    assert "tool→" in out or "tool" in out
