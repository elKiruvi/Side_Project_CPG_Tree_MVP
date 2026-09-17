"""Tests for Provenance, SourceFragment, and ValidationItem invariants."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import (
    DerivationState,
    Provenance,
    SourceFragment,
    ValidationItem,
    ValidationItemStatus,
)


def test_provenance_construction() -> None:
    provenance = Provenance(
        derivation=DerivationState.SOURCE_STATED,
        fragment_refs=("frag_1", "frag_2"),
        reviewer="reviewer_x",
        reviewed_at="2026-09-16",
        notes="verbatim transcription",
    )
    assert provenance.derivation is DerivationState.SOURCE_STATED
    assert provenance.fragment_refs == ("frag_1", "frag_2")
    assert provenance.reviewer == "reviewer_x"
    assert provenance.reviewed_at == "2026-09-16"


def test_provenance_defaults_are_explicitly_empty() -> None:
    provenance = Provenance(derivation=DerivationState.EXTRACTED)
    assert provenance.fragment_refs == ()
    assert provenance.reviewer is None
    assert provenance.reviewed_at is None
    assert provenance.notes is None


def test_provenance_rejects_invalid_fragment_ref() -> None:
    with pytest.raises(ValueError, match="must match"):
        Provenance(
            derivation=DerivationState.EXTRACTED,
            fragment_refs=("bad ref",),
        )


def test_provenance_rejects_invalid_review_date() -> None:
    with pytest.raises(ValueError, match="ISO-8601"):
        Provenance(
            derivation=DerivationState.EXTRACTED,
            reviewed_at="not-a-date",
        )


def test_source_fragment_construction() -> None:
    fragment = SourceFragment(
        id="frag_1",
        document_id="doc_1",
        page=3,
        section="Diagnosis",
        verbatim_text="some verbatim source text",
    )
    assert fragment.document_id == "doc_1"
    assert fragment.page == 3
    assert fragment.section == "Diagnosis"
    assert fragment.verbatim_text == "some verbatim source text"


def test_source_fragment_requires_identifier() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        SourceFragment(id="")


def test_source_fragment_rejects_invalid_document_id() -> None:
    with pytest.raises(ValueError, match="must match"):
        SourceFragment(id="frag_1", document_id="doc one")


def test_validation_item_construction() -> None:
    item = ValidationItem(
        id="vi_1",
        category="ambiguity",
        description="source text is ambiguous",
        severity="high",
        related_ids=("rule_x",),
    )
    assert item.category == "ambiguity"
    assert item.severity == "high"
    assert item.related_ids == ("rule_x",)
    assert item.status is ValidationItemStatus.OPEN


def test_validation_item_requires_category() -> None:
    with pytest.raises(ValueError, match="category must not be empty"):
        ValidationItem(id="vi_1", category="", description="x")


def test_validation_item_requires_description() -> None:
    with pytest.raises(ValueError, match="description must not be empty"):
        ValidationItem(id="vi_1", category="ambiguity", description="")


def test_validation_item_rejects_invalid_related_id() -> None:
    with pytest.raises(ValueError, match="must match"):
        ValidationItem(
            id="vi_1",
            category="ambiguity",
            description="x",
            related_ids=("bad ref",),
        )
