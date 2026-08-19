"""Declarative step conditions.

A condition is a small object — an operator, a reference, and a value — never a
string of code. Workflow definitions come from templates, the API and
eventually from models, so "evaluate this expression" is the one thing this
must not offer.
"""

from __future__ import annotations

from typing import Any

from jarvis.autonomous_workflows.refs import ReferenceError, is_reference, resolve_reference

# Operators.
ALWAYS = "always"
EQUALS = "equals"
NOT_EQUALS = "not_equals"
TRUTHY = "truthy"
FALSY = "falsy"
CONTAINS = "contains"
IN = "in"
GREATER_THAN = "greater_than"
LESS_THAN = "less_than"
EXISTS = "exists"
MISSING = "missing"
ALL_OF = "all_of"
ANY_OF = "any_of"
NOT = "not"

OPERATORS = (
    ALWAYS,
    EQUALS,
    NOT_EQUALS,
    TRUTHY,
    FALSY,
    CONTAINS,
    IN,
    GREATER_THAN,
    LESS_THAN,
    EXISTS,
    MISSING,
    ALL_OF,
    ANY_OF,
    NOT,
)
COMBINATORS = (ALL_OF, ANY_OF, NOT)
MAX_NESTING = 5


class ConditionError(ValueError):
    """A condition that cannot be evaluated as written."""


def validate(condition: dict[str, Any], *, _depth: int = 0) -> None:
    if not condition:
        return
    if not isinstance(condition, dict):
        raise ConditionError("a condition must be an object")
    if _depth > MAX_NESTING:
        raise ConditionError(f"conditions may not nest deeper than {MAX_NESTING}")
    operator = str(condition.get("op") or "").strip()
    if operator not in OPERATORS:
        raise ConditionError(
            f"unknown condition operator {operator!r}; allowed: {', '.join(OPERATORS)}"
        )
    if operator in (ALL_OF, ANY_OF):
        clauses = condition.get("conditions")
        if not isinstance(clauses, list) or not clauses:
            raise ConditionError(f"{operator} needs a non-empty conditions list")
        for clause in clauses:
            validate(clause, _depth=_depth + 1)
        return
    if operator == NOT:
        inner = condition.get("condition")
        if not isinstance(inner, dict):
            raise ConditionError("not needs a condition")
        validate(inner, _depth=_depth + 1)
        return
    if operator == ALWAYS:
        return
    ref = condition.get("ref")
    if not is_reference(str(ref or "")):
        raise ConditionError(f"{operator} needs a ref like ${{steps.x.output.y}}, got {ref!r}")


def evaluate(
    condition: dict[str, Any],
    *,
    inputs: dict[str, Any],
    context: dict[str, Any],
    step_outputs: dict[str, Any],
    _depth: int = 0,
) -> bool:
    """Whether a step should run. An empty condition means yes."""
    if not condition:
        return True
    validate(condition, _depth=_depth)
    operator = str(condition.get("op")).strip()

    if operator == ALWAYS:
        return True
    if operator == ALL_OF:
        return all(
            evaluate(
                c, inputs=inputs, context=context, step_outputs=step_outputs, _depth=_depth + 1
            )
            for c in condition["conditions"]
        )
    if operator == ANY_OF:
        return any(
            evaluate(
                c, inputs=inputs, context=context, step_outputs=step_outputs, _depth=_depth + 1
            )
            for c in condition["conditions"]
        )
    if operator == NOT:
        return not evaluate(
            condition["condition"],
            inputs=inputs,
            context=context,
            step_outputs=step_outputs,
            _depth=_depth + 1,
        )

    missing = object()
    try:
        actual = resolve_reference(
            str(condition["ref"]), inputs=inputs, context=context, step_outputs=step_outputs
        )
    except ReferenceError:
        actual = missing

    if operator == EXISTS:
        return actual is not missing
    if operator == MISSING:
        return actual is missing
    if actual is missing:
        # A comparison against something that is not there is false, not an error:
        # a conditional step should be skipped, not crash the workflow.
        return False

    expected = condition.get("value")
    if operator == EQUALS:
        return actual == expected
    if operator == NOT_EQUALS:
        return actual != expected
    if operator == TRUTHY:
        return bool(actual)
    if operator == FALSY:
        return not bool(actual)
    if operator == CONTAINS:
        try:
            return expected in actual
        except TypeError:
            return False
    if operator == IN:
        try:
            return actual in expected
        except TypeError:
            return False
    if operator in (GREATER_THAN, LESS_THAN):
        try:
            left, right = float(actual), float(expected)
        except (TypeError, ValueError):
            return False
        return left > right if operator == GREATER_THAN else left < right
    return False


def describe(condition: dict[str, Any]) -> str:
    """A readable form, so a skipped step can say why."""
    if not condition:
        return "always"
    operator = str(condition.get("op") or "?")
    if operator in (ALL_OF, ANY_OF):
        joined = " and " if operator == ALL_OF else " or "
        return "(" + joined.join(describe(c) for c in condition.get("conditions") or []) + ")"
    if operator == NOT:
        return f"not {describe(condition.get('condition') or {})}"
    if operator == ALWAYS:
        return "always"
    ref = condition.get("ref")
    if operator in (EXISTS, MISSING, TRUTHY, FALSY):
        return f"{ref} {operator}"
    return f"{ref} {operator} {condition.get('value')!r}"
