"""P2: per-headspace skills loader + draft-from-receipt (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ami.headspace.skills import (
    Skill,
    SkillStore,
    draft_skill_markdown,
    match_skills,
    parse_skill_markdown,
    seed_default_skills,
)


SAMPLE = """---
id: grocery-list-house
version: 1
headspace: markdown
triggers: ["grocery", "shopping list", "milk"]
tools: ["add_to_list", "list_lists"]
peers: []
status: active
source: human
---

# Grocery list (house)

1. Prefer list name \"Groceries\"
2. Add one item per tool call
"""


def test_parse_skill_markdown_frontmatter_and_body():
    skill = parse_skill_markdown(SAMPLE, path=Path("grocery-list-house.md"))
    assert skill.id == "grocery-list-house"
    assert skill.version == 1
    assert skill.headspace == "markdown"
    assert "grocery" in skill.triggers
    assert "add_to_list" in skill.tools
    assert skill.status == "active"
    assert "Groceries" in skill.body
    assert skill.is_active


def test_match_skills_by_trigger_substring():
    skills = [
        parse_skill_markdown(SAMPLE, path=Path("a.md")),
        parse_skill_markdown(
            """---
id: mesh-announce
version: 1
headspace: neighbors
triggers: ["who is home", "neighbors", "mesh"]
status: active
---
Announce before listing.
""",
            path=Path("b.md"),
        ),
    ]
    hit = match_skills(skills, "add milk to the grocery list")
    assert [s.id for s in hit] == ["grocery-list-house"]
    hit2 = match_skills(skills, "who is home on the mesh?")
    assert [s.id for s in hit2] == ["mesh-announce"]
    assert match_skills(skills, "what time is it") == []


def test_skill_store_loads_active_from_filespace(tmp_path: Path):
    root = tmp_path / "skills"
    root.mkdir()
    (root / "grocery-list-house.md").write_text(SAMPLE, encoding="utf-8")
    (root / "drafts").mkdir()
    (root / "drafts" / "wip.md").write_text(
        """---
id: wip
status: draft
triggers: ["wip"]
---
draft only
""",
        encoding="utf-8",
    )
    (root / "retired.md").write_text(
        """---
id: old
status: retired
triggers: ["old"]
---
gone
""",
        encoding="utf-8",
    )

    store = SkillStore(root)
    active = store.list_active()
    assert len(active) == 1
    assert active[0].id == "grocery-list-house"
    matched = store.match("shopping list please")
    assert matched[0].id == "grocery-list-house"
    assert store.render_for_prompt(matched).startswith("## Active skills")


def test_seed_default_skills_copies_once(tmp_path: Path):
    defaults = tmp_path / "defaults"
    defaults.mkdir()
    (defaults / "routing.md").write_text(
        """---
id: corespace-routing
version: 1
headspace: corespace
triggers: ["help", "what can you"]
status: active
source: builtin
---
Use ask for info, do for actions.
""",
        encoding="utf-8",
    )
    dest = tmp_path / "data" / "skills"
    n = seed_default_skills(defaults, dest)
    assert n == 1
    assert (dest / "routing.md").is_file()
    # second seed does not overwrite
    (dest / "routing.md").write_text("user-edited", encoding="utf-8")
    n2 = seed_default_skills(defaults, dest)
    assert n2 == 0
    assert (dest / "routing.md").read_text(encoding="utf-8") == "user-edited"


def test_draft_skill_from_turn_receipt(tmp_path: Path):
    from ami.core.interaction import InteractionStore, SpanKind, SpanStatus

    store = InteractionStore(root=tmp_path / "convos")
    turn = store.start_turn(session_id="s1", human_text="add eggs to groceries", entry_headspace="corespace")
    sid = turn.begin_span(
        kind=SpanKind.DO,
        headspace="markdown",
        name="do_headspace",
        input_summary="add eggs",
        parent_span_id=turn.root_span_id,
    )
    turn.end_span(sid, status=SpanStatus.OK, output_summary="added eggs")
    turn.finish(final_text="Eggs are on the grocery list.")

    md = draft_skill_markdown(turn, headspace="markdown")
    assert "status: draft" in md
    assert "add eggs" in md.lower() or "groceries" in md.lower()
    assert "route" in md.lower() or "→" in md

    skills = SkillStore(tmp_path / "hs" / "skills")
    path = skills.write_draft(md, suggested_id="from-turn")
    assert path.is_file()
    assert path.parent.name == "drafts"
    drafts = skills.list_drafts()
    assert len(drafts) == 1
    assert drafts[0].status == "draft"


def test_primitive_skills_dir_and_headspace_tools(tmp_path: Path):
    from ami.headspace.headspace import Headspace, ami_tool, collect_tool_methods
    from ami.headspace.headspace_instructions import HeadspaceInstruction

    class _Alpha(Headspace):
        @ami_tool
        def alpha_only(self, x: str) -> str:
            """Alpha tool."""
            return f"alpha:{x}"

        def query(self, prompt: str) -> HeadspaceInstruction:
            skills_block = self.skills_prompt_block(prompt)
            return HeadspaceInstruction(
                instructions=[],
                observation=f"skills={bool(skills_block)}:{prompt[:20]}",
                name="alpha",
                steps=[{"action": {"action": "TASK COMPLETE"}, "thought": "t"}],
            )

    _Alpha._hs_name = "alpha"
    alpha = _Alpha.__new__(_Alpha)
    # Avoid Config singleton: pin filespace on the instance
    data = tmp_path / "alpha"
    data.mkdir(parents=True)
    alpha.__dict__["filespace"] = data

    skills_dir = alpha.skills_dir
    assert skills_dir.name == "skills"
    assert skills_dir.is_dir()
    (skills_dir / "t.md").write_text(
        """---
id: alpha-t
version: 1
headspace: alpha
triggers: ["alpha special"]
status: active
---
Do the alpha special thing.
""",
        encoding="utf-8",
    )

    names = {m.__name__ for m in collect_tool_methods(alpha)}
    assert "list_skills" in names
    assert "promote_skill_draft" in names

    listed = alpha.list_skills()
    assert "alpha-t" in listed

    block = alpha.skills_prompt_block("please run alpha special now")
    assert "alpha-t" in block or "alpha special" in block.lower()

    from ami.core.interaction import InteractionStore

    istore = InteractionStore(root=tmp_path / "c")
    turn = istore.start_turn(session_id="x", human_text="alpha special task", entry_headspace="alpha")
    turn.finish(final_text="done")
    path = alpha.draft_skill_from_receipt(turn)
    assert Path(path).is_file()
