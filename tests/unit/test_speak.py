"""P4 thin-speak path (no LLM)."""

from __future__ import annotations

from pathlib import Path

from ami.ai.speak import last_useful_observation, should_use_thin_speak, thin_speak
from ami.core.interaction import InteractionStore, SpanKind, SpanStatus


def test_last_useful_observation_prefers_last_obs():
    steps = [
        {"thought": "t1", "action": {"action": "x"}, "observation": "first"},
        {"thought": "t2", "action": {"action": "TASK COMPLETE"}, "observation": "Eggs added to Groceries."},
    ]
    assert last_useful_observation(steps) == "Eggs added to Groceries."


def test_thin_speak_strips_peer_result_prefix():
    text = thin_speak(steps=[{"observation": "[tool→markdown ok] milk added | steps=1 | spans=1"}])
    assert text == "milk added"


def test_thin_speak_from_turn_spans(tmp_path: Path):
    turn = InteractionStore(root=tmp_path).start_turn(
        session_id="s", human_text="add milk", entry_headspace="corespace"
    )
    sid = turn.begin_span(
        kind=SpanKind.TOOL,
        headspace="markdown",
        name="add_to_list",
        input_summary="milk",
        parent_span_id=turn.root_span_id,
    )
    turn.end_span(sid, status=SpanStatus.OK, output_summary="milk added to Groceries")
    assert thin_speak(turn=turn) == "milk added to Groceries"


def test_should_use_thin_modes():
    steps = [{"observation": "Done."}]
    assert should_use_thin_speak(mode="thin", steps=steps) is True
    assert should_use_thin_speak(mode="llm", steps=steps) is False
    assert should_use_thin_speak(mode="auto", steps=steps) is True
    long_steps = [{"observation": "x"} for _ in range(6)]
    long_steps[-1]["observation"] = "final"
    assert should_use_thin_speak(mode="auto", steps=long_steps) is False
