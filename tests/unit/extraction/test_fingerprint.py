"""Tests for deterministic content fingerprinting."""

from __future__ import annotations

import pytest

from cpg_tree.extraction import document_id_from_sha256, fingerprint_bytes

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
VALID_SHA256 = "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882"


def test_fingerprint_is_deterministic() -> None:
    data = b"some source bytes"
    assert fingerprint_bytes(data) == fingerprint_bytes(data)


def test_fingerprint_of_empty_bytes() -> None:
    assert fingerprint_bytes(b"") == EMPTY_SHA256


def test_different_bytes_produce_different_hashes() -> None:
    assert fingerprint_bytes(b"alpha") != fingerprint_bytes(b"beta")


def test_document_id_derives_from_sha256_prefix() -> None:
    document_id = document_id_from_sha256(VALID_SHA256)
    assert document_id == f"doc-{VALID_SHA256[:16]}"


def test_same_bytes_produce_same_document_id() -> None:
    assert document_id_from_sha256(fingerprint_bytes(b"alpha")) == document_id_from_sha256(
        fingerprint_bytes(b"alpha")
    )


@pytest.mark.parametrize(
    "invalid_sha256",
    ["3a1654", "Z" * 64, "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f588"],
)
def test_document_id_rejects_invalid_sha256(invalid_sha256: str) -> None:
    with pytest.raises(ValueError, match="64-character"):
        document_id_from_sha256(invalid_sha256)
