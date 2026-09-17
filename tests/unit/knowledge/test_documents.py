"""Tests for SourceDocument identity validation."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import SourceDocument

VALID_SHA256 = "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882"


def test_source_document_construction() -> None:
    document = SourceDocument(
        document_id="doc-3a1654757801b7b6",
        filename="protocol.pdf",
        sha256=VALID_SHA256,
        byte_size=1089336,
    )
    assert document.document_id == "doc-3a1654757801b7b6"
    assert document.file_format == "pdf"


def test_source_document_requires_identifier() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        SourceDocument(document_id="", filename="x.pdf", sha256=VALID_SHA256)


def test_source_document_requires_filename() -> None:
    with pytest.raises(ValueError, match="filename"):
        SourceDocument(document_id="doc-3a1654757801b7b6", filename="", sha256=VALID_SHA256)


@pytest.mark.parametrize(
    "invalid_sha256",
    ["abc", "Z" * 64, VALID_SHA256[:-1], VALID_SHA256 + "0"],
)
def test_source_document_rejects_invalid_sha256(invalid_sha256: str) -> None:
    with pytest.raises(ValueError, match="64-character"):
        SourceDocument(
            document_id="doc-3a1654757801b7b6",
            filename="x.pdf",
            sha256=invalid_sha256,
        )


def test_source_document_rejects_negative_byte_size() -> None:
    with pytest.raises(ValueError, match="not be negative"):
        SourceDocument(
            document_id="doc-3a1654757801b7b6",
            filename="x.pdf",
            sha256=VALID_SHA256,
            byte_size=-1,
        )


def test_source_document_allows_unknown_byte_size() -> None:
    document = SourceDocument(
        document_id="doc-3a1654757801b7b6",
        filename="x.pdf",
        sha256=VALID_SHA256,
    )
    assert document.byte_size is None
