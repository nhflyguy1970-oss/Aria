"""Reference resolution for step inputs.

Deliberately not an expression language. A reference names a location in
workflow data — an input, a context value, or a previous step's output — and
nothing else. There is no evaluation, no attribute access into live objects and
no filesystem reach, because a workflow definition is data that arrives from
templates, the API and eventually models.
"""

from __future__ import annotations

import json
import re
from typing import Any

# ${input.topic} / ${context.summary} / ${steps.gather.output.text}
_REF = re.compile(r"\$\{([a-z_]+)((?:\.[A-Za-z0-9_\-]+)*)\}")

MAX_VALUE_BYTES = 65536
MAX_DEPTH = 8

INPUT = "input"
CONTEXT = "context"
STEPS = "steps"
NAMESPACES = (INPUT, CONTEXT, STEPS)


class ReferenceError(ValueError):
    """A reference that cannot be resolved, or that is not allowed."""


def _walk(value: Any, path: list[str], *, origin: str) -> Any:
    """Follow a plain-data path. Mappings and sequences only."""
    current = value
    for part in path:
        if isinstance(current, dict):
            if part not in current:
                raise ReferenceError(f"{origin}: no key {part!r}")
            current = current[part]
        elif isinstance(current, (list, tuple)):
            if not part.lstrip("-").isdigit():
                raise ReferenceError(f"{origin}: {part!r} is not a list index")
            index = int(part)
            if index >= len(current) or index < -len(current):
                raise ReferenceError(f"{origin}: index {index} out of range")
            current = current[index]
        else:
            # Never getattr: a reference must not reach into a live object.
            raise ReferenceError(f"{origin}: cannot index into {type(current).__name__}")
    return current


def resolve_reference(
    reference: str,
    *,
    inputs: dict[str, Any],
    context: dict[str, Any],
    step_outputs: dict[str, Any],
) -> Any:
    match = _REF.fullmatch((reference or "").strip())
    if not match:
        raise ReferenceError(f"malformed reference: {reference!r}")
    namespace = match.group(1)
    path = [p for p in match.group(2).split(".") if p]
    if namespace not in NAMESPACES:
        raise ReferenceError(f"unknown namespace {namespace!r}; allowed: {', '.join(NAMESPACES)}")
    if len(path) > MAX_DEPTH:
        raise ReferenceError(f"reference is deeper than {MAX_DEPTH} levels")

    root = {INPUT: inputs, CONTEXT: context, STEPS: step_outputs}[namespace]
    return _walk(root, path, origin=reference)


def is_reference(value: Any) -> bool:
    return isinstance(value, str) and bool(_REF.fullmatch(value.strip()))


def resolve_params(
    params: Any,
    *,
    inputs: dict[str, Any],
    context: dict[str, Any],
    step_outputs: dict[str, Any],
    _depth: int = 0,
) -> Any:
    """Replace references anywhere in a params structure.

    A whole-string reference keeps the referenced value's type; a reference
    embedded in text is substituted as text.
    """
    if _depth > MAX_DEPTH:
        raise ReferenceError("params nested too deeply")
    if isinstance(params, str):
        if is_reference(params):
            return _bounded(
                resolve_reference(params, inputs=inputs, context=context, step_outputs=step_outputs)
            )

        def _sub(m: re.Match) -> str:
            value = resolve_reference(
                m.group(0), inputs=inputs, context=context, step_outputs=step_outputs
            )
            return value if isinstance(value, str) else json.dumps(value, default=str)

        return _bounded(_REF.sub(_sub, params))
    if isinstance(params, dict):
        return {
            k: resolve_params(
                v, inputs=inputs, context=context, step_outputs=step_outputs, _depth=_depth + 1
            )
            for k, v in params.items()
        }
    if isinstance(params, list):
        return [
            resolve_params(
                v, inputs=inputs, context=context, step_outputs=step_outputs, _depth=_depth + 1
            )
            for v in params
        ]
    return params


def references_in(params: Any, found: list[str] | None = None) -> list[str]:
    """Every reference a params structure uses, for validation before running."""
    found = [] if found is None else found
    if isinstance(params, str):
        found.extend(m.group(0) for m in _REF.finditer(params))
    elif isinstance(params, dict):
        for value in params.values():
            references_in(value, found)
    elif isinstance(params, list):
        for value in params:
            references_in(value, found)
    return found


def _bounded(value: Any) -> Any:
    """Keep one step's output from becoming the next step's denial of service."""
    if isinstance(value, str) and len(value) > MAX_VALUE_BYTES:
        return value[:MAX_VALUE_BYTES]
    try:
        if len(json.dumps(value, default=str)) > MAX_VALUE_BYTES:
            return {"truncated": True, "preview": json.dumps(value, default=str)[:4096]}
    except (TypeError, ValueError):
        return str(value)[:MAX_VALUE_BYTES]
    return value
