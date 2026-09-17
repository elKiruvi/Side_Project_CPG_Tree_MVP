"""Tests for the deterministic inspection views."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import ProtocolVersion
from cpg_tree.validation import validate_package
from cpg_tree.views.inspection import (
    build_summary,
    render_rule_detail,
    render_rules,
    render_summary,
    render_variables,
    rules_to_json,
    summary_to_json,
    variables_to_json,
)

EXPECTED_RULES_WITH_EVIDENCE = 2


def test_summary_exposes_only_package_facts(synthetic_package: ProtocolVersion) -> None:
    summary = build_summary(synthetic_package)
    assert summary.protocol_id == "TEST-PL-999"
    assert summary.version == "v01"
    assert summary.name == "Synthetic Protocol"
    assert summary.description == "Synthetic scope statement for view tests"
    assert summary.approval_date == "2026-01-01"
    assert summary.counts == {
        "documents": 1,
        "fragments": 1,
        "variables": 4,
        "rules": 2,
        "actions": 3,
        "test_cases": 1,
        "validation_items": 1,
    }
    assert summary.rules_with_evidence == EXPECTED_RULES_WITH_EVIDENCE
    assert summary.rules_without_evidence == 0
    assert summary.variables_with_evidence == 1
    assert summary.actions_with_evidence == 0
    assert summary.fragments_with_page == 1
    assert summary.fragments_with_document == 1
    assert summary.fragments_with_text == 1
    assert summary.derivation_counts == {"NORMALIZED": 1, "SOURCE_STATED": 1}
    assert summary.status_counts == {"EXTRACTED": 2}
    assert summary.variable_derivation_counts == {"SOURCE_STATED": 1}
    assert summary.action_derivation_counts == {}
    assert summary.validation_item_status_counts == {"OPEN": 1}


def test_summary_without_report_marks_validation_as_not_run(
    synthetic_package: ProtocolVersion,
) -> None:
    text = render_summary(build_summary(synthetic_package))
    assert "Validation : not run" in text


def test_summary_with_report_includes_counts_and_note(
    synthetic_package: ProtocolVersion,
) -> None:
    report = validate_package(synthetic_package)
    text = render_summary(build_summary(synthetic_package, report))
    assert f"valid: {'yes' if report.is_valid() else 'no'}" in text
    assert "not mean clinical validation" in text
    assert "document_id" in text or "doc-0123456789abcdef" in text


def test_render_summary_is_deterministic(synthetic_package: ProtocolVersion) -> None:
    report = validate_package(synthetic_package)
    first = render_summary(build_summary(synthetic_package, report))
    second = render_summary(build_summary(synthetic_package, report))
    assert first == second


def test_render_summary_shows_element_level_provenance_coverage(
    synthetic_package: ProtocolVersion,
) -> None:
    text = render_summary(build_summary(synthetic_package))
    assert "rules with source evidence: 2/2" in text
    assert "variables with source evidence: 1/4" in text
    assert "actions with source evidence: 0/3" in text
    assert "fragments with document: 1" in text
    assert "fragments with verbatim text: 1" in text
    assert "derivation (variables): SOURCE_STATED=1" in text
    assert "validation items: OPEN=1" in text


def test_summary_to_json_schema_is_stable(synthetic_package: ProtocolVersion) -> None:
    report = validate_package(synthetic_package)
    data = summary_to_json(build_summary(synthetic_package, report))
    assert list(data) == [
        "protocol_id",
        "name",
        "description",
        "version",
        "approval_date",
        "change_summary",
        "documents",
        "counts",
        "rules_with_evidence",
        "rules_without_evidence",
        "variables_with_evidence",
        "actions_with_evidence",
        "fragments_with_page",
        "fragments_with_document",
        "fragments_with_text",
        "derivation_counts",
        "status_counts",
        "variable_derivation_counts",
        "action_derivation_counts",
        "validation_item_status_counts",
        "validation",
    ]
    assert data["validation"] == {
        "valid": report.is_valid(),
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
    }


def test_render_variables_are_sorted_and_complete(synthetic_package: ProtocolVersion) -> None:
    text = render_variables(synthetic_package)
    assert text.index("category_z") < text.index("count_x") < text.index("flag_y")
    assert "label: Count X" in text
    assert "unit: cells" in text
    assert "allowed: alpha, beta, gamma" in text
    assert "derivation: SOURCE_STATED" in text
    assert "fragments: frag_1" in text


def test_variables_to_json_is_sorted(synthetic_package: ProtocolVersion) -> None:
    data = variables_to_json(synthetic_package)
    assert [entry["id"] for entry in data["variables"]] == [
        "category_z",
        "count_x",
        "flag_y",
        "span_t",
    ]


def test_render_rules_list_is_sorted(synthetic_package: ProtocolVersion) -> None:
    text = render_rules(synthetic_package)
    assert text.index("rule_alternatives") < text.index("rule_composite")
    assert "applies_to: yes" in text
    assert "exceptions: 1" in text


def test_render_rule_detail_shows_evaluation_order(
    synthetic_package: ProtocolVersion,
) -> None:
    text = render_rule_detail(synthetic_package, "rule_composite")
    assert "applies_to -> condition -> exceptions" in text
    assert "AND(" in text
    assert "category_z IN {alpha, beta}" in text
    assert "act_request: REQUEST_TEST" in text


def test_render_rule_detail_unknown_rule_fails(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(ValueError, match="unknown rule 'nope'"):
        render_rule_detail(synthetic_package, "nope")


def test_rules_to_json_includes_convenience_text(
    synthetic_package: ProtocolVersion,
) -> None:
    data = rules_to_json(synthetic_package)
    by_id = {entry["id"]: entry for entry in data["rules"]}
    assert "AND(" in by_id["rule_composite"]["condition_text"]
    assert "AND(" in by_id["rule_composite"]["applies_to_text"]
    assert len(by_id["rule_composite"]["exception_texts"]) == 1
