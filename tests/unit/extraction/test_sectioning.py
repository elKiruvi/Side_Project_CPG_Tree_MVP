"""Tests for the generic deterministic section-heading detector."""

from __future__ import annotations

from cpg_tree.extraction import detect_section

LONG_UPPERCASE = "A" * 101


def test_uppercase_line_is_candidate() -> None:
    assert detect_section("TRATAMIENTO ANTIBIÓTICO EMPÍRICO") == "TRATAMIENTO ANTIBIÓTICO EMPÍRICO"


def test_lowercase_line_is_not_candidate() -> None:
    assert detect_section("some body text") is None


def test_mixed_case_line_is_not_candidate() -> None:
    assert detect_section("Página 4 de 7") is None


def test_empty_text_has_no_candidate() -> None:
    assert detect_section("") is None


def test_punctuation_only_lines_have_no_candidate() -> None:
    assert detect_section(".:-") is None


def test_uppercase_line_over_max_length_is_not_candidate() -> None:
    assert detect_section(LONG_UPPERCASE) is None


def test_trailing_punctuation_is_stripped() -> None:
    assert detect_section("PLAN DE EGRESO.") == "PLAN DE EGRESO"


def test_numbered_heading_is_candidate() -> None:
    assert detect_section("1. RECOMENDACIONES PARA EL DIAGNÓSTICO") == (
        "1. RECOMENDACIONES PARA EL DIAGNÓSTICO"
    )


def test_first_candidate_wins() -> None:
    text = "FIRST HEADING\nSECOND HEADING\nbody text"
    assert detect_section(text) == "FIRST HEADING"


def test_candidate_preceded_by_body_text_is_detected() -> None:
    text = "body text with lowercase letters\nLATER HEADING"
    assert detect_section(text) == "LATER HEADING"
