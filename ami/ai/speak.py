"""P4 thin speak — turn observations into human text without a second LLM call."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


def last_useful_observation(steps: Optional[Sequence[Dict[str, Any]]]) -> str:
    """
    Pull the best human-facing string from agent steps.

    Prefers the last non-empty observation; falls back to TASK COMPLETE thought.
    """
    if not steps:
        return ""
    last_obs = ""
    for step in steps:
        if not isinstance(step, dict):
            continue
        obs = step.get("observation")
        if obs is None:
            continue
        if isinstance(obs, dict):
            obs = obs.get("observation") or obs.get("message") or str(obs)
        text = str(obs).strip()
        if text and text.upper() != "NONE":
            last_obs = text
    if last_obs:
        return last_obs
    # fallback: last thought
    for step in reversed(list(steps)):
        if not isinstance(step, dict):
            continue
        thought = step.get("thought")
        if thought and str(thought).strip():
            return str(thought).strip()
    return ""


def observations_from_turn(turn: Any) -> List[str]:
    """Collect ok span output_summaries (ask/do/tool/skill) in order."""
    out: List[str] = []
    spans = getattr(turn, "spans", None) or []
    for span in spans:
        kind = getattr(span, "kind", None)
        kind_v = getattr(kind, "value", kind)
        if kind_v not in ("ask", "do", "tool", "skill"):
            continue
        status = getattr(span, "status", None)
        status_v = getattr(status, "value", status)
        if status_v not in (None, "ok", "OK"):
            # still include error messages briefly
            pass
        text = (getattr(span, "output_summary", None) or "").strip()
        if text:
            out.append(text)
    return out


def thin_speak(
    *,
    steps: Optional[Sequence[Dict[str, Any]]] = None,
    turn: Any = None,
    max_chars: int = 400,
) -> str:
    """
    Compose a single spoken line from receipt/steps — no LLM.

    Priority: last agent observation → last peer/tool span output → empty.
    """
    text = last_useful_observation(steps)
    if not text and turn is not None:
        span_obs = observations_from_turn(turn)
        if span_obs:
            text = span_obs[-1]
    text = (text or "").strip()
    # strip common agent junk prefixes
    for prefix in ("[delegated→", "[ask→", "[do→", "[tool→"):
        if text.startswith(prefix) and "]" in text:
            text = text.split("]", 1)[-1].strip()
            # drop trailing " | steps=N | spans=N"
            if " | steps=" in text:
                text = text.split(" | steps=")[0].strip()
            break
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def should_use_thin_speak(
    *,
    mode: str,
    steps: Optional[Sequence[Dict[str, Any]]] = None,
    turn: Any = None,
    max_chars: int = 400,
) -> bool:
    """
    mode:
      thin — always thin
      llm  — never thin
      auto — thin when a short clear observation exists
    """
    m = (mode or "auto").strip().lower()
    if m in ("llm", "summarize", "full"):
        return False
    if m in ("thin", "template", "receipt"):
        return True
    # auto
    candidate = thin_speak(steps=steps, turn=turn, max_chars=max_chars)
    if not candidate:
        return False
    if len(candidate) > max_chars:
        return False
    # multi-step agent with many actions → prefer llm polish
    if steps and len(steps) > 4:
        return False
    return True
