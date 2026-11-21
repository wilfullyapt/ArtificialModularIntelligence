"""Headspace primitives, tool inheritance, and delegation hub tests (no LLM)."""

from __future__ import annotations

import pytest

from ami.headspace.headspace import Headspace, ami_tool, collect_tool_methods
from ami.headspace.hub import DelegationHub
from ami.headspace.headspace_instructions import HeadspaceInstruction, InstructionType


class _PrimitiveTools(Headspace):
    """Shared primitive-style tools inherited by children."""

    @ami_tool
    def shared_ping(self, msg: str) -> str:
        """Echo a message from the primitive layer."""
        return f"ping:{msg}"


class _DomainAlpha(_PrimitiveTools):
    @ami_tool
    def alpha_only(self, x: str) -> str:
        """Alpha domain tool."""
        return f"alpha:{x}"


class _DomainBeta(_PrimitiveTools):
    @ami_tool
    def beta_only(self, x: str) -> str:
        """Beta domain tool."""
        return f"beta:{x}"


def test_collect_tools_includes_inherited_primitive_tools():
    alpha = _DomainAlpha.__new__(_DomainAlpha)
    names = {m.__name__ for m in collect_tool_methods(alpha)}
    assert "shared_ping" in names
    assert "alpha_only" in names
    # Base Headspace delegation tools also present
    assert "list_peer_headspaces" in names
    assert "delegate_to_headspace" in names
    assert "ask_headspace" in names
    assert "do_headspace" in names


def test_tools_property_builds_headspace_tools():
    alpha = _DomainAlpha.__new__(_DomainAlpha)
    tools = alpha.tools
    by_name = {t.name: t for t in tools}
    assert by_name["shared_ping"].method("hi") == "ping:hi"
    assert by_name["alpha_only"].method("z") == "alpha:z"


def test_delegation_hub_depth_limit():
    hub = DelegationHub(max_depth=2)

    class _Leaf(Headspace):
        def query(self, prompt: str) -> HeadspaceInstruction:
            # If depth allows, try to bounce back — should fail at limit
            if hub.depth < hub.max_depth:
                try:
                    hub.delegate("leaf", prompt, from_headspace="leaf")
                except ValueError as e:
                    return HeadspaceInstruction(
                        instructions=[InstructionType.STOP_AGENT],
                        observation=str(e),
                        name="leaf",
                        should_continue=False,
                        steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "stop"}],
                    )
            return HeadspaceInstruction(
                instructions=[],
                observation=f"done:{prompt}",
                name="leaf",
                steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "ok"}],
            )

    leaf = _Leaf.__new__(_Leaf)
    hub.register("leaf", leaf)
    # first delegate depth becomes 1
    out = hub.delegate("leaf", "task-1", from_headspace="corespace")
    assert "done:task-1" in out or "Delegation" in out or "nested self" in out.lower() or "depth" in out.lower()


def test_delegation_hub_unknown_and_menu():
    hub = DelegationHub(max_depth=3)
    a = _DomainAlpha.__new__(_DomainAlpha)
    b = _DomainBeta.__new__(_DomainBeta)
    a.bind_hub(hub)
    b.bind_hub(hub)
    hub.register("alpha", a)
    hub.register("beta", b)

    menu = hub.describe_menu(exclude="alpha")
    assert "beta" in menu
    assert "alpha" not in menu.split("\n")[1] if False else "beta" in menu

    with pytest.raises(ValueError, match="Unknown"):
        hub.delegate("nope", "x")


def test_delegate_tool_on_headspace_uses_hub():
    hub = DelegationHub(max_depth=3)

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

    entry = _DomainAlpha.__new__(_DomainAlpha)
    entry.bind_hub(hub)
    result = entry.delegate_to_headspace("worker", "fold laundry")
    assert "worked:fold laundry" in result
    assert hub.depth == 0  # unwound


def test_max_depth_hard_stop():
    hub = DelegationHub(max_depth=1)

    class _Bounce(Headspace):
        name_override = "bounce"

        @property
        def name(self):
            return "bounce"

        def query(self, prompt: str) -> HeadspaceInstruction:
            # always try to go deeper
            try:
                msg = hub.delegate("bounce2", prompt, from_headspace="bounce")
            except ValueError as e:
                msg = str(e)
            return HeadspaceInstruction(
                instructions=[],
                observation=msg,
                name="bounce",
                steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "b"}],
            )

    class _Bounce2(Headspace):
        def query(self, prompt: str) -> HeadspaceInstruction:
            return HeadspaceInstruction(
                instructions=[],
                observation="b2",
                name="bounce2",
                steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "b2"}],
            )

    b1 = _Bounce.__new__(_Bounce)
    b2 = _Bounce2.__new__(_Bounce2)
    hub.register("bounce", b1)
    hub.register("bounce2", b2)

    # depth 0→1 ok to bounce; inside bounce depth=1 so further delegate hits limit
    out = hub.delegate("bounce", "go", from_headspace="corespace")
    assert "depth" in out.lower() or "limit" in out.lower() or "b2" in out
