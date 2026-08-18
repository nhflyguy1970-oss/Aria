"""Input/output contract validation for skills.

Deliberately a small, explicit subset of JSON Schema rather than a dependency:
enough to reject malformed input before any action runs, and to say precisely
what was wrong without echoing the offending values back.
"""

from __future__ import annotations

from typing import Any

_TYPES: dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


class ContractError(ValueError):
    """Input or output that does not satisfy the declared contract."""


def _type_ok(value: Any, declared: str) -> bool:
    expected = _TYPES.get(declared)
    if expected is None:
        return True
    if declared == "integer" and isinstance(value, bool):
        return False  # bool is an int in Python; a schema asking for an integer means one
    if declared == "number" and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def validate_payload(
    payload: dict[str, Any],
    schema: dict[str, Any],
    *,
    label: str = "input",
    allow_extra: bool = False,
) -> dict[str, Any]:
    """Validate and return the accepted payload.

    Undeclared parameters are rejected rather than passed through, so a caller
    cannot quietly alter a skill's behaviour with a parameter it never declared.
    """
    if not isinstance(payload, dict):
        raise ContractError(f"{label} must be an object")
    if not schema:
        return dict(payload)

    properties = schema.get("properties") or {}
    required = schema.get("required") or []

    missing = [name for name in required if name not in payload]
    if missing:
        raise ContractError(f"{label} is missing required field(s): {', '.join(sorted(missing))}")

    if properties and not (allow_extra or schema.get("additionalProperties", False)):
        extra = [name for name in payload if name not in properties]
        if extra:
            raise ContractError(f"{label} has undeclared field(s): {', '.join(sorted(extra))}")

    for name, spec in properties.items():
        if name not in payload:
            continue
        value = payload[name]
        declared = (spec or {}).get("type")
        if declared and not _type_ok(value, declared):
            raise ContractError(
                f"{label} field {name!r} must be of type {declared}, got {type(value).__name__}"
            )
        choices = (spec or {}).get("enum")
        if choices and value not in choices:
            raise ContractError(
                f"{label} field {name!r} must be one of: {', '.join(map(str, choices))}"
            )
        minimum = (spec or {}).get("minimum")
        if minimum is not None and isinstance(value, (int, float)) and value < minimum:
            raise ContractError(f"{label} field {name!r} must be >= {minimum}")
        max_len = (spec or {}).get("maxLength")
        if max_len is not None and isinstance(value, str) and len(value) > max_len:
            raise ContractError(f"{label} field {name!r} exceeds maxLength {max_len}")

    return dict(payload)


def apply_defaults(payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload or {})
    for name, spec in (schema.get("properties") or {}).items():
        if name not in out and isinstance(spec, dict) and "default" in spec:
            out[name] = spec["default"]
    return out
