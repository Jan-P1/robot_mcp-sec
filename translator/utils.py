from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]


def _format_value(value: Any) -> str:
    """Format a Python value into a compact LTL atom-friendly representation."""
    if isinstance(value, str):
        return value.replace(" ", "_").replace("'", "")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "_".join(str(v) for v in value)
    return str(value)


def _tool_call_to_atom(tool_call: ToolCall) -> str:
    """Convert a single tool call to a propositional atom-like string."""
    name = tool_call.tool_name
    args = tool_call.arguments or {}

    # General fallback atom that includes sorted args for deterministic output
    if not args:
        return name

    parts = []
    for k in sorted(args.keys()):
        parts.append(f"{k}_{_format_value(args[k])}")
    return f"{name}__{'__'.join(parts)}"


def translate_tool_calls_to_LTL(tool_calls: List[ToolCall]) -> str:
    """
    Translate a sequence of tool calls into an LTL conjunction that enforces
    the observed order using eventuality (F) and next (X) operators.

    Example for calls [a, b, c]:
        F(a) & F(X(b)) & F(X(X(c)))

    Returns:
        "true" for empty input.
    """
    if not tool_calls:
        return "true"

    clauses: List[str] = []
    for i, tc in enumerate(tool_calls):
        atom = _tool_call_to_atom(tc)
        next_prefix = "X(" * i
        next_suffix = ")" * i
        clauses.append(f"{next_prefix}{atom}{next_suffix}")

    return " & ".join(clauses)

    