"""Tests for the deterministic evaluation result renderer."""

from __future__ import annotations

from dataclasses import replace

from cpg_tree.engine import Case, evaluate_package
from cpg_tree.knowledge import (
    Action,
    ActionType,
    Condition,
    ConditionKind,
    DerivationState,
    ProtocolVersion,
    Provenance,
    Rule,
)
from cpg_tree.views.results import evaluation_to_json, render_evaluation


def _evaluate(package: ProtocolVersion, inputs: dict[str, object]) -> object:
    return evaluate_package(package, Case.from_inputs(inputs))


def test_matched_rule_renders_declared_action(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {"count_x": 101, "flag_y": True, "category_z": "gamma"})
    text = render_evaluation(
        result,
        synthetic_package,
        Case.from_inputs({"count_x": 101, "flag_y": True, "category_z": "gamma"}),
    )
    assert "rule_composite" in text and "MATCHED" in text
    assert "act_request: REQUEST_TEST" in text
    assert "prescribe" not in text.split("alternatives")[0].lower() or "declared actions" in text
    assert "Note: deterministic mechanical evaluation" in text


def test_not_matched_rule_renders_outcome(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {"flag_y": False})
    text = render_evaluation(result, synthetic_package, Case.from_inputs({"flag_y": False}))
    assert "rule_alternatives" in text and "NOT_MATCHED" in text
    assert "declared actions" not in text


def test_not_applicable_rule_explains_scope(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {"count_x": 1, "flag_y": True})
    text = render_evaluation(
        result, synthetic_package, Case.from_inputs({"count_x": 1, "flag_y": True})
    )
    assert "NOT_APPLICABLE" in text
    assert "applies_to evaluated FALSE" in text


def test_excepted_rule_explains_exception(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {"count_x": 101, "flag_y": True, "category_z": "alpha"})
    text = render_evaluation(
        result,
        synthetic_package,
        Case.from_inputs({"count_x": 101, "flag_y": True, "category_z": "alpha"}),
    )
    assert "EXCEPTED" in text
    assert "condition TRUE but an exception evaluated TRUE" in text


def test_indeterminate_rule_preserves_unknown(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {})
    text = render_evaluation(result, synthetic_package, Case.from_inputs({}))
    assert "rule_alternatives" in text and "INDETERMINATE" in text
    assert "required information is UNKNOWN" in text


def test_indeterminate_via_exception_unknown(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {"count_x": 101, "flag_y": True})
    text = render_evaluation(
        result, synthetic_package, Case.from_inputs({"count_x": 101, "flag_y": True})
    )
    assert "rule_composite" in text and "INDETERMINATE" in text
    assert "an exception evaluated UNKNOWN" in text


def test_multiple_prescribe_actions_render_as_alternatives(
    synthetic_package: ProtocolVersion,
) -> None:
    result = _evaluate(synthetic_package, {"flag_y": True})
    text = render_evaluation(result, synthetic_package, Case.from_inputs({"flag_y": True}))
    alternatives_block = text[text.index("rule_alternatives") :]
    assert "multiple PRESCRIBE = alternatives declared by the source" in alternatives_block
    assert "act_prescribe_a" in alternatives_block and "[alternative]" in alternatives_block
    assert "act_prescribe_b" in alternatives_block
    assert "this tool never selects one" in alternatives_block


def test_alternatives_are_marked_in_json(synthetic_package: ProtocolVersion) -> None:
    result = _evaluate(synthetic_package, {"flag_y": True})
    data = evaluation_to_json(result, synthetic_package, Case.from_inputs({"flag_y": True}))
    by_id = {entry["rule_id"]: entry for entry in data["rule_results"]}
    groups = [action["group"] for action in by_id["rule_alternatives"]["actions"]]
    assert groups == ["alternatives", "alternatives"]
    assert by_id["rule_alternatives"]["outcome"] == "MATCHED"


def test_single_prescribe_is_not_an_alternative_group(
    synthetic_package: ProtocolVersion,
) -> None:
    package = replace(
        synthetic_package,
        actions={
            **synthetic_package.actions,
            "act_single": Action(id="act_single", type=ActionType.PRESCRIBE, label="Única"),
        },
        rules={
            **synthetic_package.rules,
            "rule_single": Rule(
                id="rule_single",
                condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
                action_refs=("act_single",),
                provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
            ),
        },
    )
    result = _evaluate(package, {"flag_y": True})
    data = evaluation_to_json(result, package, Case.from_inputs({"flag_y": True}))
    by_id = {entry["rule_id"]: entry for entry in data["rule_results"]}
    assert [a["group"] for a in by_id["rule_single"]["actions"]] == ["declared"]


def test_unresolved_derivation_is_flagged(synthetic_package: ProtocolVersion) -> None:
    rule = Rule(
        id="rule_unresolved",
        condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
        action_refs=(),
        provenance=Provenance(DerivationState.UNRESOLVED),
    )
    package = replace(synthetic_package, rules={**synthetic_package.rules, "rule_unresolved": rule})
    result = _evaluate(package, {"flag_y": True})
    text = render_evaluation(result, package, Case.from_inputs({"flag_y": True}))
    assert "UNRESOLVED derivation — not validated knowledge" in text


def test_show_expressions_renders_condition_structure(
    synthetic_package: ProtocolVersion,
) -> None:
    case = Case.from_inputs({"count_x": 101, "flag_y": True, "category_z": "gamma"})
    result = evaluate_package(synthetic_package, case)
    text = render_evaluation(result, synthetic_package, case, show_expressions=True)
    assert "condition → TRUE" in text
    assert "count_x > 100" in text
    assert "applies_to → TRUE" in text


def test_json_schema_is_stable_and_deterministic(
    synthetic_package: ProtocolVersion,
) -> None:
    case = Case.from_inputs({"count_x": 101, "flag_y": True})
    result = evaluate_package(synthetic_package, case)
    first = evaluation_to_json(result, synthetic_package, case)
    second = evaluation_to_json(result, synthetic_package, case)
    assert first == second
    assert list(first) == ["protocol_id", "version", "case_values", "rule_results"]
    assert first["case_values"] == {"count_x": 101, "flag_y": True}
    entry = first["rule_results"][0]
    assert list(entry) == [
        "rule_id",
        "outcome",
        "applies_to_result",
        "condition_result",
        "exception_results",
        "action_refs",
        "actions",
        "validation_status",
        "derivation",
    ]


def test_rule_results_follow_engine_order(synthetic_package: ProtocolVersion) -> None:
    case = Case.from_inputs({"flag_y": True})
    result = evaluate_package(synthetic_package, case)
    data = evaluation_to_json(result, synthetic_package, case)
    rule_ids = [entry["rule_id"] for entry in data["rule_results"]]
    assert rule_ids == sorted(rule_ids)
