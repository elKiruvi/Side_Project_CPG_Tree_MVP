"""Traceability tests: fine-grained fragment -> verbatim text -> source page
-> SourceDocument -> exact SHA-256.

The chain is demonstrable only when the Phase 2 extraction artifacts are
available locally (data/ is gitignored); these tests skip otherwise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.protocols.itu_v06 import DOCUMENT_ID, SHA256, build_itu_package

DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "02_intermediate" / DOCUMENT_ID

pytestmark = pytest.mark.skipif(
    not DATA_ROOT.is_dir(),
    reason="Phase 2 extraction artifacts are not available locally",
)


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_every_fragment_verbatim_text_is_in_its_source_page() -> None:
    package = build_itu_package()
    for fragment in package.fragments.values():
        page_file = DATA_ROOT / "pages" / f"page_{fragment.page:03d}.txt"
        assert page_file.is_file(), f"missing source page for {fragment.id}"
        page_text = _norm(page_file.read_text(encoding="utf-8"))
        fragment_text = _norm(fragment.verbatim_text or "")
        assert fragment_text, f"fragment {fragment.id} has no verbatim text"
        assert fragment_text in page_text, (
            f"fragment {fragment.id} verbatim text not found in {page_file.name}"
        )


def test_fragments_resolve_to_document_with_exact_sha256() -> None:
    package = build_itu_package()
    document = package.documents[DOCUMENT_ID]
    assert document.sha256 == SHA256
    for fragment in package.fragments.values():
        assert fragment.document_id == document.document_id


def test_extracted_source_document_matches_package_identity() -> None:
    source_file = DATA_ROOT / "source_document.yaml"
    assert source_file.is_file()
    content = source_file.read_text(encoding="utf-8")
    assert SHA256 in content
    assert DOCUMENT_ID in content


def test_no_fragment_cites_an_unknown_document() -> None:
    package = build_itu_package()
    for fragment in package.fragments.values():
        assert fragment.document_id in package.documents
