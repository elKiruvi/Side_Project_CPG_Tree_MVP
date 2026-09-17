# ruff: noqa: TRY004
"""Validation report model: findings about package traceability and integrity.

A ``ValidationReport`` describes whether the traceability machinery of a
knowledge package is internally consistent. It never evaluates conditions and
never claims clinical validity. ``is_valid`` means "no traceability errors",
nothing more.

Serialization is explicit and deterministic: only YAML-safe primitives are
produced or consumed, enums are serialized as their string values, and no
``!!python/object`` tags are used.

TRY004 is disabled for this module on purpose: deserialization of malformed
report documents raises ValueError by API contract, not TypeError, mirroring
``cpg_tree.knowledge.serialization``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import yaml


class FindingSeverity(StrEnum):
    """Severity of a validation finding.

    ERROR means the traceability machinery is broken and must be fixed before
    the package is used. WARNING means a gap worth attention. INFO is an
    informational flag that never invalidates the report.
    """

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One machine-readable validation outcome.

    ``code`` is a stable identifier shared with tests and tooling;
    ``path`` locates the offending element inside the package (for example
    ``rules.rule_x.provenance``); ``related_ids`` carries the identifiers the
    finding is about.
    """

    code: str
    severity: FindingSeverity
    message: str
    path: str | None = None
    related_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("ValidationFinding.code must not be empty")
        if not self.message:
            raise ValueError("ValidationFinding.message must not be empty")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Audit result for one protocol version.

    The report is a validation artifact, not the execution engine's data
    model: nothing should be built on top of it except validation tooling.
    """

    protocol_id: str
    version: str
    findings: tuple[ValidationFinding, ...] = ()

    def __post_init__(self) -> None:
        if not self.protocol_id:
            raise ValueError("ValidationReport.protocol_id must not be empty")
        if not self.version:
            raise ValueError("ValidationReport.version must not be empty")

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity is FindingSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity is FindingSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity is FindingSeverity.INFO)

    def is_valid(self) -> bool:
        """Return True when the traceability machinery is intact.

        This is a statement about provenance integrity only; it never means
        the package is clinically validated.
        """
        return self.error_count == 0


def finding_sort_key(finding: ValidationFinding) -> tuple[str, str, tuple[str, ...]]:
    """Canonical ordering key for findings: code, then path, then related ids."""
    return (finding.code, finding.path or "", finding.related_ids)


def dump_report(report: ValidationReport) -> str:
    """Serialize a ValidationReport into deterministic YAML text.

    Findings are emitted in canonical order regardless of construction order,
    so identical reports always produce byte-identical text.
    """
    findings = sorted(report.findings, key=finding_sort_key)
    data: dict[str, Any] = {
        "protocol_id": report.protocol_id,
        "version": report.version,
        "findings": [_finding_to_dict(finding) for finding in findings],
    }
    return str(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def load_report(text: str) -> ValidationReport:
    """Deserialize YAML text produced by dump_report back into a report."""
    data = yaml.safe_load(text)
    if not isinstance(data, Mapping):
        raise ValueError("report YAML root must be a mapping")
    protocol_id = data.get("protocol_id")
    if not isinstance(protocol_id, str) or not protocol_id:
        raise ValueError("report YAML requires a non-empty 'protocol_id' string")
    version = data.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("report YAML requires a non-empty 'version' string")
    findings_raw = data.get("findings", [])
    if not isinstance(findings_raw, (list, tuple)):
        raise ValueError(f"report 'findings' must be a list; got {type(findings_raw).__name__}")
    return ValidationReport(
        protocol_id=protocol_id,
        version=version,
        findings=tuple(_finding_from_dict(raw) for raw in findings_raw),
    )


def _finding_to_dict(finding: ValidationFinding) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code": finding.code,
        "severity": finding.severity.value,
        "message": finding.message,
    }
    if finding.path is not None:
        result["path"] = finding.path
    if finding.related_ids:
        result["related_ids"] = list(finding.related_ids)
    return result


def _finding_from_dict(data: object) -> ValidationFinding:
    if not isinstance(data, Mapping):
        raise ValueError(f"finding entry must be a mapping; got {type(data).__name__}")
    code = data.get("code")
    if not isinstance(code, str) or not code:
        raise ValueError("finding requires a non-empty 'code' string")
    severity = data.get("severity")
    if severity is None:
        raise ValueError("finding requires a 'severity' field")
    message = data.get("message")
    if not isinstance(message, str) or not message:
        raise ValueError("finding requires a non-empty 'message' string")
    path = data.get("path")
    if path is not None and not isinstance(path, str):
        raise ValueError("finding 'path' must be a string when present")
    related_ids = data.get("related_ids")
    return ValidationFinding(
        code=code,
        severity=FindingSeverity(severity),
        message=message,
        path=path,
        related_ids=_as_tuple(related_ids, "finding related_ids")
        if related_ids is not None
        else (),
    )


def _as_tuple(raw: object, field_name: str) -> tuple[Any, ...]:
    """Require a list-like value, so strings are never silently split."""
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{field_name} must be a list; got {type(raw).__name__}")
    return tuple(raw)
