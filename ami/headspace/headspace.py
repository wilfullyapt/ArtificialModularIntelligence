""" AMI Headspace Abstract Base Class and Core Funcionality """

from __future__ import annotations

import json
import typing
import inspect
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from functools import cached_property, wraps

import qrcode

from ..core import Config
from ..llm import LLMProvider

from .base import Primitive
from .headspace_instructions import HeadspaceInstruction
from .skills import SkillStore, draft_skill_markdown, seed_default_skills

if TYPE_CHECKING:
    from .hub import DelegationHub
    from ..core.interaction import TurnReceipt


def ami_tool(func):
    """Decorator marking a Headspace method as an LLM-callable tool."""

    @wraps(func)
    def wrapper():
        setattr(func, "is_tool", True)
        return func

    return wrapper()


def generate_qr_image(url) -> Path:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_img_path = Config().data_dir / "resources" / "img_dump" / "qr_code.png"
    qr_img_path.parent.mkdir(parents=True, exist_ok=True)

    img.save(qr_img_path)
    return qr_img_path


def get_param_type(annotation):
    """Convert Python type annotations to a JSON-compatible format."""
    # PEP 563 / from __future__ import annotations → often strings
    if isinstance(annotation, str):
        normalized = annotation.strip().lower().replace("typing.", "")
        if normalized in ("str", "string"):
            return "string"
        if normalized in ("int", "integer"):
            return "integer"
        if normalized in ("bool", "boolean"):
            return "boolean"
        if normalized.startswith("literal["):
            # crude: treat as string enum unknown
            return "string"
        # Optional[str] style
        if "str" in normalized:
            return "string"
        if "int" in normalized:
            return "integer"
        if "bool" in normalized:
            return "boolean"
        return "string"

    origin = typing.get_origin(annotation)
    if origin is typing.Literal:
        args = typing.get_args(annotation)
        return {"type": "string", "enum": list(args)}
    elif origin is typing.Union and len(typing.get_args(annotation)) == 2 and type(None) in typing.get_args(annotation):
        actual_type = next(a for a in typing.get_args(annotation) if a is not type(None))
        return get_param_type(actual_type)
    elif annotation is int:
        return "integer"
    elif annotation is str:
        return "string"
    elif annotation is bool:
        return "boolean"
    else:
        raise ValueError(f"Unsupported parameter type: {annotation}")


def extract_tool_info(func):
    """Extract name, description, and parameters from a tool function."""
    sig = inspect.signature(func)
    description = func.__doc__.strip().split("\n")[0] if func.__doc__ else ""
    parameters = {}
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        if param.annotation is inspect.Parameter.empty:
            raise ValueError(f"Parameter '{param_name}' in '{func.__name__}' has no type annotation")
        param_type = get_param_type(param.annotation)
        param_info = {"type": param_type}
        if param.default is not inspect.Parameter.empty:
            param_info["required"] = False
            param_info["default"] = param.default
        else:
            param_info["required"] = True
        parameters[param_name] = param_info
    return {
        "name": func.__name__,
        "description": description,
        "arg_schema": parameters,
    }


def collect_tool_methods(instance: Any) -> List[Callable]:
    """
    Collect @ami_tool methods from the instance MRO (inheritance-aware).

    Walks subclasses → bases so tools defined on shared primitive/mixin
    Headspace parents appear in children (menu hierarchy).
    """
    seen: set[str] = set()
    methods: List[Callable] = []
    for cls in type(instance).mro():
        if cls in (object, Primitive):
            continue
        # Skip pure infrastructure bases without headspace tools
        for name, obj in vars(cls).items():
            if name.startswith("_") or name in seen:
                continue
            if not callable(obj):
                continue
            # Class dict holds function; is_tool set by @ami_tool on the function
            if not getattr(obj, "is_tool", False):
                continue
            bound = getattr(instance, name)
            if not callable(bound) or not getattr(bound, "is_tool", False):
                # bound method may not carry attribute — check underlying
                if not getattr(obj, "is_tool", False):
                    continue
            seen.add(name)
            methods.append(bound if callable(bound) else obj)
    return methods


@dataclass
class HeadspaceTool:
    name: str
    description: str
    arg_schema: Dict[str, Dict[str, str | dict]]
    method: Callable

    def __str__(self) -> str:
        data = {
            "name": self.name,
            "description": self.description,
            "arg_schema": self.arg_schema,
        }
        return json.dumps(data, indent=2)

    @property
    def tool_string(self) -> str:
        return f"{self.name}({', '.join([f'{an}: {av}' for an, av in self.arg_schema.items()])}) - {self.description}"

    @classmethod
    def from_method(cls, method: Callable) -> "HeadspaceTool":
        tool_info = extract_tool_info(method)
        return cls(
            name=tool_info["name"],
            description=tool_info["description"],
            arg_schema=tool_info["arg_schema"],
            method=method,
        )


class Headspace(Primitive):
    """
    AI-facing headspace: domain tools + optional peer delegation via a hub.

    Tools: mark methods with @ami_tool. Inherited tools from parent Headspace
    mixins/primitives are included (MRO collection).

    Delegation: when Brain attaches a DelegationHub, base tools
    list_peer_headspaces / delegate_to_headspace enable a bounded
    self-referential graph (max depth on the hub).
    """

    # Optional hub injected by Brain each turn
    _hub: Optional["DelegationHub"] = None

    def __new__(cls, *args, **kwargs):
        if cls is Headspace:
            raise TypeError("Headspace class cannot be instantiated directly.")
        return super().__new__(cls, *args, **kwargs)

    def __repr__(self):
        return f"<Headspace(name={self.name})>"

    def bind_hub(self, hub: Optional["DelegationHub"]) -> None:
        """Attach or clear the cross-headspace delegation hub for this turn."""
        self._hub = hub

    @cached_property
    def tool_names(self):
        return ", ".join([tool.name for tool in self.tools])

    @cached_property
    def tool_strings(self):
        return "\n".join([tool.tool_string for tool in self.tools])

    @property
    def tools(self) -> List[HeadspaceTool]:
        """All @ami_tool methods including inherited primitive/parent tools."""
        # Not cached_property: hub binding can change available base tools semantics
        methods = collect_tool_methods(self)
        return [HeadspaceTool.from_method(m) for m in methods]

    def append_visual(self, img_path: Path):
        print(f"Image appended to Headspace returning: {img_path}")

    # --- Skills (filespace/skills) ---

    def skill_store(self) -> SkillStore:
        """SkillStore rooted at this headspace filespace/skills (seeds builtins once)."""
        store = SkillStore(self.skills_dir)
        # Builtin defaults shipped beside the plugin package: <plugin>/skills/*.md
        try:
            plugin_dir = Path(__import__(self.__class__.__module__, fromlist=["*"]).__file__).resolve().parent
        except Exception:
            plugin_dir = None
        if plugin_dir is not None:
            defaults = plugin_dir / "skills"
            if defaults.is_dir():
                seed_default_skills(defaults, self.skills_dir)
        return store

    def skills_prompt_block(self, prompt: str) -> str:
        """Render matching active skills for injection into the agent prompt."""
        store = self.skill_store()
        matched = store.match(prompt)
        if not matched:
            return ""
        # Record skill use on bound turn if present
        hub = self._hub
        turn = getattr(hub, "turn", None) if hub is not None else None
        if turn is not None:
            from ..core.interaction import SpanKind, SpanStatus

            for sk in matched:
                sid = turn.begin_span(
                    kind=SpanKind.SKILL,
                    headspace=self.name,
                    name=sk.id,
                    input_summary=prompt[:200],
                    parent_span_id=turn.root_span_id,
                )
                turn.end_span(sid, status=SpanStatus.OK, output_summary=f"loaded skill {sk.id}")
        return store.render_for_prompt(matched)

    def draft_skill_from_receipt(self, turn: "TurnReceipt") -> str:
        """Write a draft skill markdown under skills/drafts/ from a turn receipt. Returns path."""
        store = self.skill_store()
        md = draft_skill_markdown(turn, headspace=self.name)
        path = store.write_draft(md, suggested_id=f"from-{getattr(turn, 'turn_id', 'turn')}")
        return str(path)

    @ami_tool
    def list_skills(self) -> str:
        """List active and draft skills for this headspace."""
        store = self.skill_store()
        active = store.list_active()
        drafts = store.list_drafts()
        lines = [f"Active ({len(active)}):"]
        for s in active:
            lines.append(f"  - {s.id} v{s.version} triggers={s.triggers}")
        lines.append(f"Drafts ({len(drafts)}):")
        for s in drafts:
            lines.append(f"  - {s.id} (draft)")
        if not active and not drafts:
            return "No skills yet. Defaults seed on first use when shipped under plugin/skills/."
        return "\n".join(lines)

    @ami_tool
    def promote_skill_draft(self, draft_id: str) -> str:
        """Promote a draft skill to active (human-in-the-loop confirm)."""
        store = self.skill_store()
        try:
            path = store.promote_draft(draft_id.strip())
            return f"Promoted draft '{draft_id}' → {path}"
        except FileNotFoundError as exc:
            return f"Promote failed: {exc}"
        except ValueError as exc:
            return f"Promote failed: {exc}"

    # --- Peer tools (available on every headspace when hub bound) ---

    @ami_tool
    def list_peer_headspaces(self) -> str:
        """List other headspaces and their tools so you can ask or do domain work."""
        if self._hub is None:
            return "Delegation hub not attached; cannot list peers."
        return self._hub.describe_menu(exclude=self.name)

    @ami_tool
    def ask_headspace(self, headspace_name: str, question: str) -> str:
        """
        Ask another headspace for information (prefer no side effects).
        Use for status, lookup, explain — not mutations.
        """
        if self._hub is None:
            return "Delegation hub not attached; cannot ask peers."
        result = self._hub.ask(headspace_name, question, from_headspace=self.name)
        return result.as_tool_string()

    @ami_tool
    def do_headspace(self, headspace_name: str, task: str) -> str:
        """
        Ask another headspace to perform a task (may use tools / mutate state).
        Prefer when the work clearly belongs to that domain plugin.
        """
        if self._hub is None:
            return "Delegation hub not attached; cannot do peer work."
        result = self._hub.do(headspace_name, task, from_headspace=self.name)
        return result.as_tool_string()

    @ami_tool
    def delegate_to_headspace(self, headspace_name: str, task: str) -> str:
        """
        Legacy alias for do_headspace (bounded depth). Prefer do_headspace or ask_headspace.
        """
        if self._hub is None:
            return "Delegation hub not attached; cannot delegate."
        try:
            return self._hub.delegate(headspace_name, task, from_headspace=self.name)
        except ValueError as exc:
            return f"Delegation failed: {exc}"

    def query(self, prompt: str) -> HeadspaceInstruction:
        """Process a user query with tools, peers, and matched skills."""
        skills_block = self.skills_prompt_block(prompt)
        full_prompt = f"{skills_block}\n\n{prompt}" if skills_block else prompt
        agent = LLMProvider.from_environment().as_funccalling_toa_agent(self.name)
        return agent.run(full_prompt, self.tools)
