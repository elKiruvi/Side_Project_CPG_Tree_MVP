"""The validation layer must remain protocol-agnostic."""

from __future__ import annotations

from pathlib import Path

from cpg_tree.knowledge import ProtocolVersion
from cpg_tree.validation import validate_package

VALIDATION_PACKAGE = Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "validation"

FORBIDDEN_SOURCE_STRINGS = (
    "CT-PL-193",
    "CT-PL-197",
    "neumonía",
    "neumonia",
    "pielonefritis",
    "bacteriuria",
    "community-acquired",
    "urinary tract",
)


def test_validation_source_contains_no_protocol_specific_strings() -> None:
    for source_file in VALIDATION_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SOURCE_STRINGS:
            assert forbidden not in content, f"{source_file} contains {forbidden!r}"


def test_third_protocol_package_validates_with_generic_validator(
    valid_package: ProtocolVersion,
) -> None:
    report = validate_package(valid_package)
    assert report.protocol_id == "TEST-PL-999"
    assert report.is_valid()
