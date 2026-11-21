"""OpenAI-compatible tool schema helpers for AMI HeadspaceTool objects."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def headspace_tools_to_openai(tools: Sequence[Any]) -> List[Dict[str, Any]]:
    """
    Convert AMI HeadspaceTool list to OpenAI/Ollama tools= payload.

    Each tool needs .name, .description, .arg_schema (dict of name -> {type, required?, ...}).
    """
    out: List[Dict[str, Any]] = []
    for tool in tools:
        name = getattr(tool, "name", None)
        if not name:
            continue
        description = getattr(tool, "description", "") or name
        arg_schema = getattr(tool, "arg_schema", None) or {}
        properties: Dict[str, Any] = {}
        required: List[str] = []
        if isinstance(arg_schema, dict):
            for arg_name, info in arg_schema.items():
                if not isinstance(info, dict):
                    properties[arg_name] = {"type": "string"}
                    required.append(arg_name)
                    continue
                typ = info.get("type", "string")
                if isinstance(typ, dict):
                    # enum form from get_param_type Literal
                    properties[arg_name] = typ
                else:
                    prop: Dict[str, Any] = {"type": typ if isinstance(typ, str) else "string"}
                    if "enum" in info:
                        prop["enum"] = info["enum"]
                    properties[arg_name] = prop
                if info.get("required", True) and "default" not in info:
                    required.append(arg_name)
        parameters: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters["required"] = required
        out.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )
    return out
