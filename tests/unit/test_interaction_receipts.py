"""P0: Interaction / Turn / Span receipt spine (no LLM)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ami.core.interaction import (
    InteractionStore,
    SpanKind,
    SpanStatus,
    TurnReceipt,
)


def test_turn_opens_with_root_span_and_route_grows(tmp_path: Path):
    store = InteractionStore(root=tmp_path)
    turn = store.start_turn(session_id="sess1", human_text="add milk", entry_headspace="corespace")

    assert turn.turn_id
    assert turn.session_id == "sess1"
    assert turn.human_text == "add milk"
    assert turn.entry_headspace == "corespace"
    assert len(turn.spans) == 1
    root = turn.spans[0]
    assert root.kind == SpanKind.ENTRY
    assert root.headspace == "corespace"
    assert root.parent_span_id is None
    assert root.status == SpanStatus.OK

    tool_id = turn.begin_span(
        kind=SpanKind.TOOL,
        headspace="markdown",
        name="add_to_list",
        input_summary="milk",
        parent_span_id=root.span_id,
    )
    turn.end_span(tool_id, status=SpanStatus.OK, output_summary="added milk")

    assert "corespace" in turn.route_summary
    assert "markdown" in turn.route_summary or "add_to_list" in turn.route_summary
    assert turn.spans[-1].status == SpanStatus.OK
    assert turn.spans[-1].ended_at is not None


def test_turn_persist_and_reload(tmp_path: Path):
    store = InteractionStore(root=tmp_path)
    turn = store.start_turn(session_id="s2", human_text="who is home?", entry_headspace="corespace")
    ask_id = turn.begin_span(
        kind=SpanKind.ASK,
        headspace="neighbors",
        name="ask_headspace",
        input_summary="who is home?",
        parent_span_id=turn.spans[0].span_id,
    )
    turn.end_span(ask_id, status=SpanStatus.OK, output_summary="2 peers")
    turn.finish(final_text="Two neighbors are present.", route_extra=None)
    path = store.save_turn(turn)

    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["human_text"] == "who is home?"
    assert data["final_text"].startswith("Two neighbors")
    assert any(s["kind"] == "ask" for s in data["spans"])

    loaded = store.load_turn(turn.session_id, turn.turn_id)
    assert loaded.turn_id == turn.turn_id
    assert loaded.final_text == turn.final_text
    assert loaded.route_summary == turn.route_summary
    assert len(loaded.spans) == len(turn.spans)


def test_peer_result_carries_observation_and_nested_span_ids():
    from ami.headspace.hub import PeerResult

    pr = PeerResult(
        ok=True,
        observation="worked:fold",
        target="worker",
        kind="do",
        span_ids=["a", "b"],
    )
    assert pr.ok is True
    assert "fold" in pr.observation
    assert "do→worker" in pr.as_tool_string()
    assert "ok" in pr.as_tool_string()
    assert "fold" in pr.as_tool_string()


def test_hub_ask_and_do_emit_spans_and_return_peer_result(tmp_path: Path):
    from ami.headspace.headspace import Headspace
    from ami.headspace.headspace_instructions import HeadspaceInstruction
    from ami.headspace.hub import DelegationHub

    store = InteractionStore(root=tmp_path)
    turn = store.start_turn(session_id="s3", human_text="task", entry_headspace="corespace")
    hub = DelegationHub(max_depth=3, max_steps=8)
    hub.bind_turn(turn)

    class _Worker(Headspace):
        def query(self, prompt: str) -> HeadspaceInstruction:
            return HeadspaceInstruction(
                instructions=[],
                observation=f"worked:{prompt}",
                name="worker",
                steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "w"}],
            )

    worker = _Worker.__new__(_Worker)
    hub.register("worker", worker)

    ask = hub.ask("worker", "status?", from_headspace="corespace")
    assert ask.ok
    assert "worked:status?" in ask.observation
    assert any(s.kind == SpanKind.ASK for s in turn.spans)

    do = hub.do("worker", "fold laundry", from_headspace="corespace")
    assert do.ok
    assert "worked:fold laundry" in do.observation
    assert any(s.kind == SpanKind.DO for s in turn.spans)

    # depth unwound
    assert hub.depth == 0
    # route shows peer hops
    assert "worker" in turn.route_summary


def test_hub_ask_unknown_is_not_ok_peer_result():
    from ami.headspace.hub import DelegationHub

    hub = DelegationHub(max_depth=2)
    result = hub.ask("nope", "x", from_headspace="corespace")
    assert result.ok is False
    assert "Unknown" in result.observation or "unknown" in result.observation.lower()


def test_headspace_ask_do_tools_use_hub(tmp_path: Path):
    from ami.headspace.headspace import Headspace, ami_tool
    from ami.headspace.headspace_instructions import HeadspaceInstruction
    from ami.headspace.hub import DelegationHub

    store = InteractionStore(root=tmp_path)
    turn = store.start_turn(session_id="s4", human_text="x", entry_headspace="alpha")
    hub = DelegationHub(max_depth=3)
    hub.bind_turn(turn)

    class _Worker(Headspace):
        def query(self, prompt: str) -> HeadspaceInstruction:
            return HeadspaceInstruction(
                instructions=[],
                observation=f"ans:{prompt}",
                name="worker",
                steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "w"}],
            )

    class _Alpha(Headspace):
        @ami_tool
        def alpha_only(self, x: str) -> str:
            """Alpha domain tool."""
            return f"alpha:{x}"

    worker = _Worker.__new__(_Worker)
    alpha = _Alpha.__new__(_Alpha)
    hub.register("worker", worker)
    hub.register("alpha", alpha)
    alpha.bind_hub(hub)

    names = {t.name for t in alpha.tools}
    assert "ask_headspace" in names
    assert "do_headspace" in names
    # backward compat
    assert "delegate_to_headspace" in names

    out = alpha.ask_headspace("worker", "ping")
    assert "ans:ping" in out
    out2 = alpha.do_headspace("worker", "act")
    assert "ans:act" in out2
