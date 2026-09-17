"""Deterministic three-valued logic combinators (strong Kleene semantics).

Truth tables over ``TruthValue``:

- AND: FALSE if any operand is FALSE; UNKNOWN if none is FALSE and at least
  one is UNKNOWN; TRUE otherwise.
- OR: TRUE if any operand is TRUE; UNKNOWN if none is TRUE and at least one is
  UNKNOWN; FALSE otherwise.
- NOT: TRUE <-> FALSE; UNKNOWN stays UNKNOWN.
- AT_LEAST_N with t = count(TRUE), u = count(UNKNOWN), k = threshold:
  t >= k -> TRUE; t + u >= k -> UNKNOWN; otherwise FALSE.

The canonical model forbids empty operand tuples and out-of-range thresholds
at construction. The engine re-validates defensively and raises
``EngineConfigurationError`` rather than inventing semantics for shapes the
model never produces.
"""

from __future__ import annotations

from collections.abc import Sequence

from cpg_tree.engine.errors import EngineConfigurationError
from cpg_tree.knowledge.enums import TruthValue

_MIN_THRESHOLD = 1


def not3(value: TruthValue) -> TruthValue:
    """Negate one truth value: TRUE <-> FALSE, UNKNOWN stays UNKNOWN."""
    if value is TruthValue.TRUE:
        return TruthValue.FALSE
    if value is TruthValue.FALSE:
        return TruthValue.TRUE
    return TruthValue.UNKNOWN


def and3(values: Sequence[TruthValue]) -> TruthValue:
    """N-ary AND: FALSE dominates, then UNKNOWN, then TRUE."""
    _require_operands(values, "AND")
    if any(value is TruthValue.FALSE for value in values):
        return TruthValue.FALSE
    if any(value is TruthValue.UNKNOWN for value in values):
        return TruthValue.UNKNOWN
    return TruthValue.TRUE


def or3(values: Sequence[TruthValue]) -> TruthValue:
    """N-ary OR: TRUE dominates, then UNKNOWN, then FALSE."""
    _require_operands(values, "OR")
    if any(value is TruthValue.TRUE for value in values):
        return TruthValue.TRUE
    if any(value is TruthValue.UNKNOWN for value in values):
        return TruthValue.UNKNOWN
    return TruthValue.FALSE


def at_least_n3(values: Sequence[TruthValue], threshold: int | None) -> TruthValue:
    """AT_LEAST_N over the exact formula: t >= k -> TRUE; t + u >= k -> UNKNOWN."""
    _require_operands(values, "AT_LEAST_N")
    if isinstance(threshold, bool) or not isinstance(threshold, int):
        raise EngineConfigurationError("AT_LEAST_N threshold must be an integer")
    if not _MIN_THRESHOLD <= threshold <= len(values):
        raise EngineConfigurationError(
            "AT_LEAST_N threshold must be between 1 and the operand count"
        )
    true_count = sum(1 for value in values if value is TruthValue.TRUE)
    unknown_count = sum(1 for value in values if value is TruthValue.UNKNOWN)
    if true_count >= threshold:
        return TruthValue.TRUE
    if true_count + unknown_count >= threshold:
        return TruthValue.UNKNOWN
    return TruthValue.FALSE


def _require_operands(values: Sequence[TruthValue], operator: str) -> None:
    if not values:
        raise EngineConfigurationError(f"{operator} requires at least one operand")
