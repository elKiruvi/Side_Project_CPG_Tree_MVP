"""Invariant tests for package validation.

Each test verifies one guarantee: the exact finding code, severity, path, and
related ids produced by ``validate_package`` for a specific violation. All
packages are synthetic and carry no clinical content.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from unit.validation.conftest import (
    DOCUMENT_ID,
    FRAGMENT_ID,
    VALID_SHA256,
    make_fragment,
    make_rule,
    make_validation_item,
)

from cpg_tree.knowledge import (
    Action,
    ActionType,
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    LogicalOperator,
    ProtocolVersion,
    Provenance,
    SourceDocument,
    TestCase,
    TruthValue,
    ValidationStatus,
    dump_package,
)
from cpg_tree.validation import (
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
    dump_report,
    load_report,
    validate_package,
)
from cpg_tree.validation.model import finding_sort_key

ERROR = FindingSeverity.ERROR
WARNING = FindingSeverity.WARNING
INFO = FindingSeverity.INFO


def _by_code(report: ValidationReport) -> dict[str, list[ValidationFinding]]:
    grouped: dict[str, list[ValidationFinding]] = {}
    for finding in report.findings:
        grouped.setdefault(finding.code, []).append(finding)
    return grouped


def _only(report: ValidationReport, code: str) -> ValidationFinding:
    grouped = _by_code(report)
    assert set(grouped) == {code}, f"expected only {code}; got {set(grouped)}"
    (finding,) = grouped[code]
    return finding


def _rule_with(valid_package: ProtocolVersion, **changes: Any) -> ProtocolVersion:
    return replace(valid_package, rules={"rule_x": make_rule(**changes)})


def test_valid_package_has_no_findings(valid_package: ProtocolVersion) -> None:
    report = validate_package(valid_package)
    assert report.findings == ()
    assert report.is_valid()
    assert report.protocol_id == "TEST-PL-999"
    assert report.version == "v01"


def test_unknown_fragment_ref_is_an_error(valid_package: ProtocolVersion) -> None:
    package = _rule_with(valid_package, fragment_refs=("frag_missing",))
    finding = _only(validate_package(package), "REF.UNKNOWN_FRAGMENT")
    assert finding.severity is ERROR
    assert finding.path == "rules.rule_x.provenance"
    assert finding.related_ids == ("frag_missing",)


def test_unknown_fragment_ref_on_action_is_an_error(valid_package: ProtocolVersion) -> None:
    action = Action(
        id="act_decide",
        type=ActionType.DECISION,
        provenance=Provenance(
            derivation=DerivationState.SOURCE_STATED,
            fragment_refs=("frag_missing",),
        ),
    )
    package = replace(valid_package, actions={"act_decide": action})
    finding = _only(validate_package(package), "REF.UNKNOWN_FRAGMENT")
    assert finding.severity is ERROR
    assert finding.path == "actions.act_decide.provenance"
    assert finding.related_ids == ("frag_missing",)


def test_unknown_action_ref_is_an_error(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        rules={"rule_x": make_rule()},
        actions={"act_other": Action(id="act_other", type=ActionType.DECISION)},
    )
    finding = _only(validate_package(package), "REF.UNKNOWN_ACTION")
    assert finding.severity is ERROR
    assert finding.path == "rules.rule_x"
    assert finding.related_ids == ("act_decide",)


def test_unknown_variable_ref_in_condition_is_an_error(
    valid_package: ProtocolVersion,
) -> None:
    rule = replace(
        make_rule(),
        condition=Condition(kind=ConditionKind.FLAG, variable_ref="missing_var", expected=True),
    )
    package = replace(valid_package, rules={"rule_x": rule})
    finding = _only(validate_package(package), "REF.UNKNOWN_VARIABLE")
    assert finding.severity is ERROR
    assert finding.path == "rules.rule_x"
    assert finding.related_ids == ("missing_var",)


def test_unknown_variable_ref_in_applies_to_is_an_error(
    valid_package: ProtocolVersion,
) -> None:
    rule = replace(
        make_rule(),
        applies_to=Condition(kind=ConditionKind.FLAG, variable_ref="missing_var", expected=True),
    )
    package = replace(valid_package, rules={"rule_x": rule})
    finding = _only(validate_package(package), "REF.UNKNOWN_VARIABLE")
    assert finding.related_ids == ("missing_var",)


def test_unknown_variable_ref_in_exceptions_is_an_error(
    valid_package: ProtocolVersion,
) -> None:
    rule = replace(
        make_rule(),
        exceptions=(
            Condition(kind=ConditionKind.FLAG, variable_ref="missing_var", expected=False),
        ),
    )
    package = replace(valid_package, rules={"rule_x": rule})
    finding = _only(validate_package(package), "REF.UNKNOWN_VARIABLE")
    assert finding.related_ids == ("missing_var",)


def test_unknown_variable_ref_in_nested_expression_is_an_error(
    valid_package: ProtocolVersion,
) -> None:
    rule = replace(
        make_rule(),
        condition=LogicalExpression(
            operator=LogicalOperator.AND,
            operands=(
                Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
                Condition(kind=ConditionKind.FLAG, variable_ref="missing_var", expected=True),
            ),
        ),
    )
    package = replace(valid_package, rules={"rule_x": rule})
    finding = _only(validate_package(package), "REF.UNKNOWN_VARIABLE")
    assert finding.related_ids == ("missing_var",)


def test_unknown_test_case_input_is_an_error(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        test_cases={"tc_1": TestCase(id="tc_1", inputs={"missing_var": True})},
    )
    finding = _only(validate_package(package), "REF.UNKNOWN_TEST_CASE_INPUT")
    assert finding.severity is ERROR
    assert finding.path == "test_cases.tc_1"
    assert finding.related_ids == ("missing_var",)


def test_unknown_test_case_expected_rule_is_an_error(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        test_cases={
            "tc_1": TestCase(id="tc_1", expected_results={"missing_rule": TruthValue.TRUE})
        },
    )
    finding = _only(validate_package(package), "REF.UNKNOWN_TEST_CASE_RULE")
    assert finding.severity is ERROR
    assert finding.path == "test_cases.tc_1"
    assert finding.related_ids == ("missing_rule",)


def test_unknown_validation_item_related_id_is_an_error(
    valid_package: ProtocolVersion,
) -> None:
    package = replace(
        valid_package,
        validation_items={"vi_1": make_validation_item(related_ids=("missing_thing",))},
    )
    finding = _only(validate_package(package), "REF.UNKNOWN_RELATED_ID")
    assert finding.severity is ERROR
    assert finding.path == "validation_items.vi_1"
    assert finding.related_ids == ("missing_thing",)


def test_known_validation_item_related_id_is_accepted(
    valid_package: ProtocolVersion,
) -> None:
    package = replace(
        valid_package,
        validation_items={"vi_1": make_validation_item(related_ids=("rule_x", FRAGMENT_ID))},
    )
    assert validate_package(package).findings == ()


def test_no_documents_declared_is_a_warning(valid_package: ProtocolVersion) -> None:
    package = replace(valid_package, documents={})
    finding = _only(validate_package(package), "PROV.NO_DOCUMENTS_DECLARED")
    assert finding.severity is WARNING
    assert finding.path is None
    assert finding.related_ids == ()


def test_fragment_without_document_is_a_warning(valid_package: ProtocolVersion) -> None:
    package = replace(valid_package, fragments={"frag_1": make_fragment(document_id=None)})
    finding = _only(validate_package(package), "PROV.FRAGMENT_WITHOUT_DOCUMENT")
    assert finding.severity is WARNING
    assert finding.path == "fragments.frag_1"


def test_unknown_fragment_document_is_an_error(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        fragments={"frag_1": make_fragment(document_id="doc-0000000000000000")},
    )
    finding = _only(validate_package(package), "PROV.UNKNOWN_DOCUMENT")
    assert finding.severity is ERROR
    assert finding.path == "fragments.frag_1"
    assert finding.related_ids == ("doc-0000000000000000",)


def test_source_stated_requires_references(valid_package: ProtocolVersion) -> None:
    package = _rule_with(valid_package, fragment_refs=())
    finding = _only(validate_package(package), "PROV.SOURCE_STATED_NO_REFERENCE")
    assert finding.severity is ERROR
    assert finding.path == "rules.rule_x.provenance"
    assert finding.related_ids == ()


@pytest.mark.parametrize("verbatim_text", [None, "", "   "])
def test_source_stated_requires_nonempty_verbatim_evidence(
    valid_package: ProtocolVersion,
    verbatim_text: str | None,
) -> None:
    package = replace(
        valid_package,
        fragments={"frag_1": make_fragment(verbatim_text=verbatim_text)},
    )
    finding = _only(validate_package(package), "PROV.SOURCE_STATED_EMPTY_EVIDENCE")
    assert finding.severity is ERROR
    assert finding.path == "rules.rule_x.provenance"
    assert finding.related_ids == (FRAGMENT_ID,)


def test_normalized_requires_references(valid_package: ProtocolVersion) -> None:
    package = _rule_with(
        valid_package,
        derivation=DerivationState.NORMALIZED,
        fragment_refs=(),
        notes="unit conversion applied",
    )
    finding = _only(validate_package(package), "PROV.NORMALIZED_NO_REFERENCE")
    assert finding.severity is ERROR
    assert finding.path == "rules.rule_x.provenance"


def test_normalized_without_notes_is_a_warning(valid_package: ProtocolVersion) -> None:
    package = _rule_with(valid_package, derivation=DerivationState.NORMALIZED)
    finding = _only(validate_package(package), "PROV.NORMALIZED_NO_TRANSFORMATION_NOTE")
    assert finding.severity is WARNING
    assert finding.path == "rules.rule_x.provenance"


def test_normalized_with_references_and_notes_is_valid(
    valid_package: ProtocolVersion,
) -> None:
    package = _rule_with(
        valid_package,
        derivation=DerivationState.NORMALIZED,
        notes="unit conversion applied",
    )
    assert validate_package(package).findings == ()


def test_extracted_without_references_is_a_warning(valid_package: ProtocolVersion) -> None:
    package = _rule_with(
        valid_package,
        derivation=DerivationState.EXTRACTED,
        fragment_refs=(),
    )
    finding = _only(validate_package(package), "PROV.EXTRACTED_NO_REFERENCE")
    assert finding.severity is WARNING
    assert finding.path == "rules.rule_x.provenance"


def test_extracted_with_references_is_valid(valid_package: ProtocolVersion) -> None:
    package = _rule_with(valid_package, derivation=DerivationState.EXTRACTED)
    assert validate_package(package).findings == ()


def test_inferred_is_informational_only(valid_package: ProtocolVersion) -> None:
    package = _rule_with(valid_package, derivation=DerivationState.INFERRED)
    report = validate_package(package)
    finding = _only(report, "PROV.INFERRED_NOT_VALIDATED")
    assert finding.severity is INFO
    assert finding.path == "rules.rule_x.provenance"
    assert report.is_valid()


def test_unresolved_is_informational_and_non_executable(valid_package: ProtocolVersion) -> None:
    package = _rule_with(valid_package, derivation=DerivationState.UNRESOLVED)
    report = validate_package(package)
    finding = _only(report, "PROV.UNRESOLVED_NOT_EXECUTABLE")
    assert finding.severity is INFO
    assert finding.path == "rules.rule_x.provenance"
    assert report.is_valid()


@pytest.mark.parametrize(
    "validation_status",
    [ValidationStatus.REVIEWED, ValidationStatus.VALIDATED],
)
def test_unresolved_conflicting_status_is_an_error(
    valid_package: ProtocolVersion,
    validation_status: ValidationStatus,
) -> None:
    package = _rule_with(
        valid_package,
        derivation=DerivationState.UNRESOLVED,
        validation_status=validation_status,
    )
    report = validate_package(package)
    grouped = _by_code(report)
    assert set(grouped) == {
        "PROV.UNRESOLVED_CONFLICTING_STATUS",
        "PROV.UNRESOLVED_NOT_EXECUTABLE",
    }
    conflict = grouped["PROV.UNRESOLVED_CONFLICTING_STATUS"][0]
    assert conflict.severity is ERROR
    assert conflict.path == "rules.rule_x.provenance"
    assert conflict.related_ids == ("rule_x",)
    assert not report.is_valid()


def test_multiple_fragment_references_are_valid(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        fragments={
            "frag_1": make_fragment(),
            "frag_2": make_fragment(fragment_id="frag_2", page=2, verbatim_text="other text"),
        },
        rules={"rule_x": make_rule(fragment_refs=("frag_1", "frag_2"))},
    )
    assert validate_package(package).findings == ()


def test_multiple_documents_are_valid(valid_package: ProtocolVersion) -> None:
    other_document_id = "doc-800af94bc0654138"
    package = replace(
        valid_package,
        documents={
            DOCUMENT_ID: SourceDocument(
                document_id=DOCUMENT_ID,
                filename="first.pdf",
                sha256=VALID_SHA256,
            ),
            other_document_id: SourceDocument(
                document_id=other_document_id,
                filename="second.pdf",
                sha256=VALID_SHA256,
            ),
        },
        fragments={
            "frag_1": make_fragment(),
            "frag_2": make_fragment(
                fragment_id="frag_2",
                document_id=other_document_id,
                page=2,
                verbatim_text="second document text",
            ),
        },
        rules={"rule_x": make_rule(fragment_refs=("frag_1", "frag_2"))},
    )
    assert validate_package(package).findings == ()


def test_validation_is_deterministic(valid_package: ProtocolVersion) -> None:
    first = validate_package(valid_package)
    second = validate_package(valid_package)
    assert first == second
    assert dump_report(first) == dump_report(second)


def test_findings_are_canonically_ordered(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        fragments={"frag_1": make_fragment(document_id=None)},
        actions={
            "act_other": Action(id="act_other", type=ActionType.DECISION),
        },
        rules={"rule_x": make_rule()},
    )
    report = validate_package(package)
    assert len(report.findings) > 1
    assert list(report.findings) == sorted(report.findings, key=finding_sort_key)


def test_report_round_trips_through_yaml(valid_package: ProtocolVersion) -> None:
    package = replace(
        valid_package,
        fragments={"frag_1": make_fragment(document_id=None)},
    )
    report = validate_package(package)
    assert load_report(dump_report(report)) == report


def test_validation_does_not_mutate_package(valid_package: ProtocolVersion) -> None:
    before = dump_package(valid_package)
    validate_package(valid_package)
    assert dump_package(valid_package) == before
