"""Tests for the derived decision-tree projection."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    LogicalOperator,
    ProtocolVersion,
    Provenance,
    Rule,
    load_package,
)
from cpg_tree.views.tree import (
    build_projection,
    projection_to_json,
    render_projection,
)

SHARED_USES = 3
_MIN_REAL_SHARED_USES = 2

FLAG_TRUE = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True)
FLAG_FALSE = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=False)
COMPARE_GT = Condition(
    kind=ConditionKind.COMPARISON,
    variable_ref="count_x",
    operator=ComparisonOperator.GT,
    operand=100,
)
COMPARE_SPAN = Condition(
    kind=ConditionKind.COMPARISON,
    variable_ref="span_t",
    operator=ComparisonOperator.GE,
    operand=1,
)
SHARED_CONDITION = LogicalExpression(
    operator=LogicalOperator.AND,
    operands=(COMPARE_SPAN, FLAG_FALSE),
)


def _package_with_shared_condition(base: ProtocolVersion) -> ProtocolVersion:
    """Two extra rules sharing one whole condition, plus shared applies_to."""
    extra = Rule(
        id="rule_zzz_extra",
        condition=SHARED_CONDITION,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
    )
    scope_rule = Rule(
        id="rule_zzz_scoped",
        condition=COMPARE_GT,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
        applies_to=SHARED_CONDITION,
    )
    scoped_twin = Rule(
        id="rule_zzz_scoped_twin",
        condition=COMPARE_SPAN,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
        applies_to=SHARED_CONDITION,
    )
    return replace(
        base,
        rules={
            **base.rules,
            "rule_zzz_extra": extra,
            "rule_zzz_scoped": scope_rule,
            "rule_zzz_scoped_twin": scoped_twin,
        },
    )


def test_projection_roots_and_rules_are_sorted(synthetic_package: ProtocolVersion) -> None:
    projection = build_projection(synthetic_package)
    assert projection.protocol_id == "TEST-PL-999"
    assert projection.version == "v01"
    assert [rule.rule_id for rule in projection.rules] == [
        "rule_alternatives",
        "rule_composite",
    ]


def test_no_shared_entries_when_nothing_repeats(
    synthetic_package: ProtocolVersion,
) -> None:
    projection = build_projection(synthetic_package)
    assert projection.shared_expressions == ()
    assert projection.rules[1].applies_to_shared_id is None


def test_shared_condition_merged_once_with_stable_id(
    synthetic_package: ProtocolVersion,
) -> None:
    package = _package_with_shared_condition(synthetic_package)
    projection = build_projection(package)
    # SHARED_CONDITION appears as condition (rule_zzz_extra) and as applies_to
    # of two rules: three occurrences, one shared entry.
    assert len(projection.shared_expressions) == 1
    shared = projection.shared_expressions[0]
    assert shared.id == "shared-01"
    assert shared.usage_count == SHARED_USES
    assert shared.first_rule_id == "rule_zzz_extra"
    assert shared.first_position == "condition"
    text = render_projection(projection, package)
    assert f"shared-01 — used {SHARED_USES} time(s)" in text
    assert "span_t >= 1" in text


def test_later_occurrences_render_as_references(
    synthetic_package: ProtocolVersion,
) -> None:
    package = _package_with_shared_condition(synthetic_package)
    projection = build_projection(package)
    text = render_projection(projection, package)
    assert "@shared-01 (first seen in rule_zzz_extra)" in text
    extra = next(r for r in projection.rules if r.rule_id == "rule_zzz_extra")
    assert extra.condition_shared_id == "shared-01"
    twin = next(r for r in projection.rules if r.rule_id == "rule_zzz_scoped_twin")
    assert twin.applies_to_shared_id == "shared-01"


def test_shared_ids_are_stable_and_deterministic(
    synthetic_package: ProtocolVersion,
) -> None:
    package = _package_with_shared_condition(synthetic_package)
    first = build_projection(package)
    second = build_projection(package)
    assert first == second
    assert render_projection(first, package) == render_projection(second, package)
    assert projection_to_json(first) == projection_to_json(second)


def test_projection_contains_no_invented_nodes(synthetic_package: ProtocolVersion) -> None:
    projection = build_projection(synthetic_package)
    for rule in projection.rules:
        canonical = synthetic_package.rules[rule.rule_id]
        assert rule.action_refs == canonical.action_refs
        assert rule.fragment_refs == canonical.provenance.fragment_refs
        assert rule.condition == canonical.condition
        assert rule.applies_to == canonical.applies_to
        assert rule.exceptions == canonical.exceptions


def test_exception_positions_are_referenced(synthetic_package: ProtocolVersion) -> None:
    membership = Condition(
        kind=ConditionKind.MEMBERSHIP,
        variable_ref="category_z",
        values=("alpha", "beta"),
    )
    first = Rule(
        id="rule_aaa_first",
        condition=membership,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
    )
    package = replace(
        synthetic_package,
        rules={**synthetic_package.rules, "rule_aaa_first": first},
    )
    projection = build_projection(package)
    composite = next(r for r in projection.rules if r.rule_id == "rule_composite")
    assert composite.exception_shared_ids == ("shared-01",)


def test_json_schema_is_stable(synthetic_package: ProtocolVersion) -> None:
    package = _package_with_shared_condition(synthetic_package)
    data = projection_to_json(build_projection(package))
    assert list(data) == ["protocol_id", "version", "shared_expressions", "rules"]
    shared = data["shared_expressions"][0]
    assert list(shared) == [
        "id",
        "fingerprint",
        "usage_count",
        "first_rule_id",
        "first_position",
        "expression",
    ]
    assert shared["expression"]["operator"] == "AND"
    assert shared["expression"]["operands"][0]["kind"] == "COMPARISON"
    rule_entry = data["rules"][0]
    assert list(rule_entry) == [
        "rule_id",
        "validation_status",
        "derivation",
        "applies_to",
        "applies_to_shared_id",
        "condition",
        "condition_shared_id",
        "exceptions",
        "exception_shared_ids",
        "action_refs",
        "fragment_refs",
    ]
    assert rule_entry["fragment_refs"] == ["frag_1"]


def test_projection_on_real_packages_yields_shared_groups() -> None:
    for relative in (
        "protocols/CT-PL-193/v09/package.yaml",
        "protocols/CT-PL-197/v06/package.yaml",
    ):
        package = load_package(Path(relative).read_text(encoding="utf-8"))
        projection = build_projection(package)
        assert projection.protocol_id == package.protocol.id
        assert [rule.rule_id for rule in projection.rules] == sorted(package.rules)
        for entry in projection.shared_expressions:
            assert entry.usage_count >= _MIN_REAL_SHARED_USES
            assert entry.id == f"shared-{int(entry.id.split('-')[1]):02d}"
