# ruff: noqa: TRY004
"""Explicit, deterministic YAML serialization for the reconciliation layer.

Only YAML-safe primitives are produced or consumed. Enums serialize as their
string values; no ``!!python/object`` tags are used. Malformed documents
raise ``ValueError`` deterministically by API contract (mirroring
``cpg_tree.knowledge.serialization`` and ``cpg_tree.views.manifest``).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from cpg_tree.reconciliation.model import (
    ConflictRepresentation,
    ConflictResolution,
    ConflictStatus,
    EvidenceClass,
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReconciledCandidate,
    ReviewStatus,
    SourceConflict,
    SourceEvidenceStatus,
    SourceRepresentation,
)

_TOP_KEYS = frozenset({"schema", "schema_version", "protocol", "version", "candidates", "conflicts"})
_CANDIDATE_KEYS = frozenset(
    {
        "candidate_id",
        "from",
        "to",
        "relation",
        "presentation_role",
        "branch_label",
        "evidence_quote",
        "fragment_ids",
        "page",
        "evidence_class",
        "review_status",
        "reconciliation_status",
        "source_representation",
        "source_location",
        "source_conflict_ids",
        "source_evidence_status",
        "reviewer_notes",
        "reconciliation_notes",
    }
)
_CONFLICT_KEYS = frozenset({"conflict_id", "topic", "status", "resolution", "representations", "notes"})
_REPRESENTATION_KEYS = frozenset({"representation", "page", "statement", "verification"})

_SCHEMA_NAME = "relationship-reconciliation"
_SCHEMA_VERSION = 2


def load_reconciliation(path: Path) -> ReconciliationInventory:
    """Load and structurally validate a reconciliation document."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"malformed reconciliation document at {path}: {error}") from error
    if not isinstance(data, Mapping):
        raise ValueError(f"reconciliation document at {path} must be a mapping")
    unknown = set(data) - _TOP_KEYS
    if unknown:
        raise ValueError(
            f"reconciliation document at {path} has unknown keys: {sorted(unknown)}"
        )
    if data.get("schema") != _SCHEMA_NAME:
        raise ValueError(
            f"reconciliation document at {path} must declare schema: {_SCHEMA_NAME}"
        )
    if data.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(
            f"reconciliation document at {path} must declare schema_version: {_SCHEMA_VERSION}"
        )
    protocol = _required_string(data, "protocol", path)
    version = _required_string(data, "version", path)
    candidates = tuple(
        _candidate_from_data(entry, path, index)
        for index, entry in enumerate(_required_list(data, "candidates", path))
    )
    conflicts = tuple(
        _conflict_from_data(entry, path, index)
        for index, entry in enumerate(_required_list(data, "conflicts", path))
    )
    return ReconciliationInventory(
        protocol=protocol,
        version=version,
        candidates=candidates,
        conflicts=conflicts,
    )


def dump_reconciliation(inventory: ReconciliationInventory) -> str:
    """Serialize a reconciliation inventory deterministically (YAML-safe)."""
    document: dict[str, object] = {
        "schema": _SCHEMA_NAME,
        "schema_version": _SCHEMA_VERSION,
        "protocol": inventory.protocol,
        "version": inventory.version,
        "candidates": [_candidate_to_dict(candidate) for candidate in inventory.candidates],
        "conflicts": [_conflict_to_dict(conflict) for conflict in inventory.conflicts],
    }
    return yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=True,
        width=88,
    )


def write_reconciliation(inventory: ReconciliationInventory, path: Path) -> None:
    """Write a reconciliation inventory to a file (UTF-8, trailing newline)."""
    path.write_text(dump_reconciliation(inventory), encoding="utf-8")


def _candidate_from_data(raw: object, path: Path, index: int) -> ReconciledCandidate:
    if not isinstance(raw, Mapping):
        raise ValueError(f"candidate {index} of {path} must be a mapping")
    unknown = set(raw) - _CANDIDATE_KEYS
    if unknown:
        raise ValueError(f"candidate {index} of {path} has unknown keys: {sorted(unknown)}")
    label = f"candidate {index} of {path}"
    to_refs = _string_or_list(raw.get("to"), path, label, "to")
    return ReconciledCandidate(
        candidate_id=_required_string(raw, "candidate_id", path, label),
        from_ref=_required_string(raw, "from", path, label),
        to_refs=to_refs,
        relation=_required_string(raw, "relation", path, label),
        presentation_role=_enum_value(raw, "presentation_role", PresentationRole, path, label),
        branch_label=_optional_string(raw, "branch_label", path, label),
        evidence_quote=_required_string(raw, "evidence_quote", path, label),
        fragment_ids=_string_list(raw.get("fragment_ids"), path, label, "fragment_ids"),
        page=_required_string(raw, "page", path, label),
        evidence_class=_enum_value(raw, "evidence_class", EvidenceClass, path, label),
        review_status=_enum_value(raw, "review_status", ReviewStatus, path, label),
        reconciliation_status=_enum_value(
            raw, "reconciliation_status", ReconciliationStatus, path, label
        ),
        source_representation=_enum_value(
            raw, "source_representation", SourceRepresentation, path, label
        ),
        source_location=_optional_string(raw, "source_location", path, label),
        source_conflict_ids=_string_list(
            raw.get("source_conflict_ids"), path, label, "source_conflict_ids"
        ),
        source_evidence_status=_enum_value(
            raw, "source_evidence_status", SourceEvidenceStatus, path, label
        ),
        reviewer_notes=_required_string(raw, "reviewer_notes", path, label),
        reconciliation_notes=_required_string(raw, "reconciliation_notes", path, label),
    )


def _conflict_from_data(raw: object, path: Path, index: int) -> SourceConflict:
    if not isinstance(raw, Mapping):
        raise ValueError(f"conflict {index} of {path} must be a mapping")
    unknown = set(raw) - _CONFLICT_KEYS
    if unknown:
        raise ValueError(f"conflict {index} of {path} has unknown keys: {sorted(unknown)}")
    label = f"conflict {index} of {path}"
    raw_representations = _required_list(raw, "representations", path, label)
    representations = tuple(
        _representation_from_data(entry, path, label, rep_index)
        for rep_index, entry in enumerate(raw_representations)
    )
    return SourceConflict(
        conflict_id=_required_string(raw, "conflict_id", path, label),
        topic=_required_string(raw, "topic", path, label),
        status=_enum_value(raw, "status", ConflictStatus, path, label),
        resolution=_enum_value(raw, "resolution", ConflictResolution, path, label),
        representations=representations,
        notes=_required_string(raw, "notes", path, label),
    )


def _representation_from_data(
    raw: object,
    path: Path,
    parent: str,
    index: int,
) -> ConflictRepresentation:
    if not isinstance(raw, Mapping):
        raise ValueError(f"representation {index} of {parent} in {path} must be a mapping")
    unknown = set(raw) - _REPRESENTATION_KEYS
    if unknown:
        raise ValueError(
            f"representation {index} of {parent} in {path} has unknown keys: {sorted(unknown)}"
        )
    label = f"representation {index} of {parent} in {path}"
    page = raw.get("page")
    if page is not None and not isinstance(page, int):
        raise ValueError(f"{label}: 'page' must be an integer or null")
    return ConflictRepresentation(
        representation=_enum_value(raw, "representation", SourceRepresentation, path, label),
        page=page,
        statement=_required_string(raw, "statement", path, label),
        verification=_enum_value(raw, "verification", SourceEvidenceStatus, path, label),
    )


def _required_string(
    raw: Mapping[str, object],
    key: str,
    path: Path,
    label: str | None = None,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        where = label if label is not None else "document"
        raise ValueError(f"{where} of {path} requires a non-empty '{key}' string")
    return value


def _optional_string(
    raw: Mapping[str, object],
    key: str,
    path: Path,
    label: str,
) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} of {path}: '{key}' must be a string or null")
    return value


def _enum_value[T](
    raw: Mapping[str, object],
    key: str,
    enum_type: type[T],
    path: Path,
    label: str,
) -> T:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{label} of {path}: '{key}' must be a string")
    try:
        return enum_type(value)  # type: ignore[return-value]
    except ValueError as error:
        allowed = sorted(member.value for member in enum_type)  # type: ignore[attr-defined]
        raise ValueError(
            f"{label} of {path}: '{key}' has invalid value {value!r}; allowed: {allowed}"
        ) from error


def _string_or_list(
    raw: object,
    path: Path,
    label: str,
    field: str,
) -> tuple[str, ...]:
    if isinstance(raw, str) and raw.strip():
        return (raw,)
    if isinstance(raw, list):
        return _string_list(raw, path, label, field)
    raise ValueError(f"{label} of {path}: '{field}' must be a string or a list of strings")


def _string_list(
    raw: object,
    path: Path,
    label: str,
    field: str,
) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(entry, str) and entry for entry in raw):
        raise ValueError(f"{label} of {path}: '{field}' must be a list of non-empty strings")
    return tuple(raw)


def _required_list(
    raw: Mapping[str, object],
    key: str,
    path: Path,
    label: str | None = None,
) -> list[object]:
    value = raw.get(key)
    if not isinstance(value, list):
        where = label if label is not None else "document"
        raise ValueError(f"{where} of {path} requires a '{key}' list")
    return value


def _candidate_to_dict(candidate: ReconciledCandidate) -> dict[str, object]:
    return {
        "candidate_id": candidate.candidate_id,
        "from": candidate.from_ref,
        "to": list(candidate.to_refs) if len(candidate.to_refs) != 1 else candidate.to_refs[0],
        "relation": candidate.relation,
        "presentation_role": candidate.presentation_role.value,
        "branch_label": candidate.branch_label,
        "evidence_quote": candidate.evidence_quote,
        "fragment_ids": list(candidate.fragment_ids),
        "page": candidate.page,
        "evidence_class": candidate.evidence_class.value,
        "review_status": candidate.review_status.value,
        "reconciliation_status": candidate.reconciliation_status.value,
        "source_representation": candidate.source_representation.value,
        "source_location": candidate.source_location,
        "source_conflict_ids": list(candidate.source_conflict_ids),
        "source_evidence_status": candidate.source_evidence_status.value,
        "reviewer_notes": candidate.reviewer_notes,
        "reconciliation_notes": candidate.reconciliation_notes,
    }


def _conflict_to_dict(conflict: SourceConflict) -> dict[str, object]:
    return {
        "conflict_id": conflict.conflict_id,
        "topic": conflict.topic,
        "status": conflict.status.value,
        "resolution": conflict.resolution.value,
        "representations": [
            {
                "representation": representation.representation.value,
                "page": representation.page,
                "statement": representation.statement,
                "verification": representation.verification.value,
            }
            for representation in conflict.representations
        ],
        "notes": conflict.notes,
    }
