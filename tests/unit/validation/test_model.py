"""Tests for the validation report model and its YAML serialization."""

from __future__ import annotations

import pytest
import yaml
from yaml.constructor import ConstructorError

from cpg_tree.validation import (
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
    dump_report,
    load_report,
)

PROTOCOL_ID = "TEST-PL-999"
VERSION = "v01"


def _finding(
    code: str = "A",
    severity: FindingSeverity = FindingSeverity.INFO,
    path: str | None = None,
    related_ids: tuple[str, ...] = (),
) -> ValidationFinding:
    return ValidationFinding(
        code=code,
        severity=severity,
        message=f"message for {code}",
        path=path,
        related_ids=related_ids,
    )


def test_finding_construction() -> None:
    finding = _finding(code="REF.UNKNOWN_FRAGMENT", severity=FindingSeverity.ERROR)
    assert finding.code == "REF.UNKNOWN_FRAGMENT"
    assert finding.severity is FindingSeverity.ERROR
    assert finding.path is None
    assert finding.related_ids == ()


def test_finding_requires_code() -> None:
    with pytest.raises(ValueError, match="code"):
        ValidationFinding(code="", severity=FindingSeverity.INFO, message="x")


def test_finding_requires_message() -> None:
    with pytest.raises(ValueError, match="message"):
        ValidationFinding(code="A", severity=FindingSeverity.INFO, message="")


def test_report_construction_and_counts() -> None:
    report = ValidationReport(
        protocol_id=PROTOCOL_ID,
        version=VERSION,
        findings=(
            _finding("ERR.ONE", FindingSeverity.ERROR),
            _finding("WARN.ONE", FindingSeverity.WARNING),
            _finding("WARN.TWO", FindingSeverity.WARNING),
            _finding("INFO.ONE", FindingSeverity.INFO),
        ),
    )
    assert report.error_count == 1
    assert report.warning_count == 2
    assert report.info_count == 1
    assert not report.is_valid()


def test_report_requires_protocol_id() -> None:
    with pytest.raises(ValueError, match="protocol_id"):
        ValidationReport(protocol_id="", version=VERSION)


def test_report_requires_version() -> None:
    with pytest.raises(ValueError, match="version"):
        ValidationReport(protocol_id=PROTOCOL_ID, version="")


def test_report_is_valid_without_errors() -> None:
    report = ValidationReport(
        protocol_id=PROTOCOL_ID,
        version=VERSION,
        findings=(
            _finding("WARN.ONE", FindingSeverity.WARNING),
            _finding("INFO.ONE", FindingSeverity.INFO),
        ),
    )
    assert report.is_valid()


def test_empty_report_is_valid() -> None:
    report = ValidationReport(protocol_id=PROTOCOL_ID, version=VERSION)
    assert report.findings == ()
    assert report.is_valid()


def test_dump_round_trip_equality() -> None:
    report = ValidationReport(
        protocol_id=PROTOCOL_ID,
        version=VERSION,
        findings=(
            _finding("PROV.NO_DOCUMENTS_DECLARED", FindingSeverity.WARNING),
            _finding(
                "REF.UNKNOWN_FRAGMENT",
                FindingSeverity.ERROR,
                "rules.rule_x.provenance",
                ("frag_1",),
            ),
        ),
    )
    assert load_report(dump_report(report)) == report


def test_dump_is_deterministic() -> None:
    report = ValidationReport(
        protocol_id=PROTOCOL_ID,
        version=VERSION,
        findings=(
            _finding("REF.UNKNOWN_ACTION", FindingSeverity.ERROR, "rules.rule_x"),
            _finding("PROV.INFERRED_NOT_VALIDATED", FindingSeverity.INFO),
        ),
    )
    assert dump_report(report) == dump_report(report)


def test_dump_contains_no_python_object_tags() -> None:
    report = ValidationReport(protocol_id=PROTOCOL_ID, version=VERSION, findings=(_finding(),))
    assert "!!python" not in dump_report(report)


def test_dump_sorts_findings_canonically() -> None:
    first = _finding("REF.Z", FindingSeverity.ERROR, "rules.rule_x")
    second = _finding("PROV.A", FindingSeverity.INFO)
    report = ValidationReport(
        protocol_id=PROTOCOL_ID,
        version=VERSION,
        findings=(first, second),
    )
    text = dump_report(report)
    assert text.index("code: PROV.A") < text.index("code: REF.Z")


def test_dump_emits_related_ids_and_path() -> None:
    report = ValidationReport(
        protocol_id=PROTOCOL_ID,
        version=VERSION,
        findings=(_finding("A", FindingSeverity.ERROR, "rules.rule_x.provenance", ("frag_1", "frag_2")),),
    )
    data = yaml.safe_load(dump_report(report))
    finding = data["findings"][0]
    assert finding["code"] == "A"
    assert finding["severity"] == "ERROR"
    assert finding["path"] == "rules.rule_x.provenance"
    assert finding["related_ids"] == ["frag_1", "frag_2"]


def test_load_rejects_unsafe_python_tags() -> None:
    with pytest.raises(ConstructorError):
        load_report("protocol_id: !!python/object:os.system []\nversion: v01\n")


def test_load_rejects_non_mapping_root() -> None:
    with pytest.raises(ValueError, match="root must be a mapping"):
        load_report("- just\n- a\n- list\n")


def test_load_rejects_missing_protocol_id() -> None:
    with pytest.raises(ValueError, match="protocol_id"):
        load_report("version: v01\n")


def test_load_rejects_missing_version() -> None:
    with pytest.raises(ValueError, match="version"):
        load_report("protocol_id: TEST-PL-999\n")


def test_load_rejects_non_list_findings() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        load_report("protocol_id: TEST-PL-999\nversion: v01\nfindings: single\n")


def test_load_rejects_non_mapping_finding() -> None:
    with pytest.raises(ValueError, match="must be a mapping"):
        load_report("protocol_id: TEST-PL-999\nversion: v01\nfindings: [plain]\n")


def test_load_rejects_finding_without_code() -> None:
    with pytest.raises(ValueError, match="code"):
        load_report(
            "protocol_id: TEST-PL-999\nversion: v01\n"
            "findings: [{severity: INFO, message: x}]\n"
        )


def test_load_rejects_finding_without_severity() -> None:
    with pytest.raises(ValueError, match="severity"):
        load_report(
            "protocol_id: TEST-PL-999\nversion: v01\n"
            "findings: [{code: A, message: x}]\n"
        )


def test_load_rejects_finding_with_invalid_severity() -> None:
    with pytest.raises(ValueError):
        load_report(
            "protocol_id: TEST-PL-999\nversion: v01\n"
            "findings: [{code: A, severity: CRITICAL, message: x}]\n"
        )


def test_load_rejects_finding_without_message() -> None:
    with pytest.raises(ValueError, match="message"):
        load_report(
            "protocol_id: TEST-PL-999\nversion: v01\n"
            "findings: [{code: A, severity: INFO}]\n"
        )


def test_load_rejects_scalar_related_ids() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        load_report(
            "protocol_id: TEST-PL-999\nversion: v01\n"
            "findings: [{code: A, severity: INFO, message: x, related_ids: single}]\n"
        )
