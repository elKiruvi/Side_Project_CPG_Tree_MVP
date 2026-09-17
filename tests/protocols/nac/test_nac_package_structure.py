"""Structure tests for the NAC CT-PL-193 v09 knowledge package.

These tests verify counts, provenance completeness, the builder/YAML
authority contract, and the exact Phase 3 validator outcome. They contain
no clinical assumptions: everything is derived from the source package.
"""

from __future__ import annotations

from pathlib import Path

from cpg_tree.knowledge import ProtocolVersion, dump_package, load_package
from cpg_tree.protocols.nac_v09 import (
    DOCUMENT_ID,
    SHA256,
    build_nac_package,
)
from cpg_tree.validation import FindingSeverity, validate_package

EXPECTED_VARIABLES = 66
EXPECTED_RULES = 42
EXPECTED_ACTIONS = 26
EXPECTED_TEST_CASES = 30
EXPECTED_FRAGMENTS = 35
EXPECTED_VALIDATION_ITEMS = 8

ARTIFACT_PATH = (
    Path(__file__).resolve().parents[3] / "protocols" / "CT-PL-193" / "v09" / "package.yaml"
)


def test_package_counts_match_the_plan() -> None:
    package = build_nac_package()
    assert len(package.variables) == EXPECTED_VARIABLES
    assert len(package.rules) == EXPECTED_RULES
    assert len(package.actions) == EXPECTED_ACTIONS
    assert len(package.test_cases) == EXPECTED_TEST_CASES
    assert len(package.fragments) == EXPECTED_FRAGMENTS
    assert len(package.validation_items) == EXPECTED_VALIDATION_ITEMS
    assert len(package.documents) == 1


def test_metadata_matches_the_source() -> None:
    package = build_nac_package()
    assert package.protocol.id == "CT-PL-193"
    assert package.version == "v09"
    assert package.approval_date == "2024-08-12"


def test_document_identity_matches_source_sha256() -> None:
    package = build_nac_package()
    document = package.documents[DOCUMENT_ID]
    assert document.sha256 == SHA256
    assert document.document_id == DOCUMENT_ID


def test_validate_package_has_exact_expected_findings() -> None:
    package = build_nac_package()
    report = validate_package(package)
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 2
    codes_and_paths = {
        (finding.code, finding.path) for finding in report.findings
    }
    assert codes_and_paths == {
        ("PROV.UNRESOLVED_NOT_EXECUTABLE", "rules.rule_hosp_criterio_curb65.provenance"),
        ("PROV.INFERRED_NOT_VALIDATED", "rules.rule_uci_bullet1.provenance"),
    }
    assert all(finding.severity is FindingSeverity.INFO for finding in report.findings)


def test_validation_items_are_open_and_not_findings() -> None:
    package = build_nac_package()
    report = validate_package(package)
    assert len(package.validation_items) == EXPECTED_VALIDATION_ITEMS
    for item in package.validation_items.values():
        assert item.status.value == "OPEN"
    assert len(report.findings) == 2


def test_every_rule_has_provenance() -> None:
    package = build_nac_package()
    for rule in package.rules.values():
        assert rule.provenance is not None
        assert rule.provenance.fragment_refs


def test_every_variable_has_provenance() -> None:
    package = build_nac_package()
    for variable in package.variables.values():
        assert variable.provenance is not None
        assert variable.provenance.fragment_refs


def test_every_action_has_provenance() -> None:
    package = build_nac_package()
    for action in package.actions.values():
        assert action.provenance is not None
        assert action.provenance.fragment_refs


def test_fragments_anchor_to_the_nac_document() -> None:
    package = build_nac_package()
    for fragment in package.fragments.values():
        assert fragment.document_id == DOCUMENT_ID
        assert fragment.verbatim_text and fragment.verbatim_text.strip()


def test_builder_dump_is_deterministic() -> None:
    first = dump_package(build_nac_package())
    second = dump_package(build_nac_package())
    assert first == second


def test_yaml_artifact_matches_builder_exactly() -> None:
    assert ARTIFACT_PATH.is_file()
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")
    assert artifact_text == dump_package(build_nac_package())


def test_yaml_artifact_round_trips_to_the_builder_package() -> None:
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")
    loaded = load_package(artifact_text)
    assert loaded == build_nac_package()


def test_yaml_artifact_round_trip_is_stable() -> None:
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")
    assert load_package(artifact_text) == load_package(artifact_text)


def test_derived_decision_inputs_are_absent() -> None:
    package = build_nac_package()
    forbidden = {
        "indicacion_hospitalizacion",
        "indicacion_toracentesis",
        "infeccion_parenquima_pulmonar",
        "sepsis_choque_origen_pulmonar",
        "recoge_muestra_espontanea",
        "expectora",
        "derrame_causa_aparente",
        "sospecha_sarscov2",
        "muestra_profunda",
    }
    assert forbidden.isdisjoint(package.variables)


def test_near_synonyms_are_distinct_variables() -> None:
    package = build_nac_package()
    assert "compromiso_multilobar" in package.variables
    assert "infiltrados_multilobares" in package.variables
    assert "falla_organica_multiple" in package.variables
    assert "falla_organica_multisistemica" in package.variables
    assert (
        package.variables["compromiso_multilobar"].provenance
        is not package.variables["infiltrados_multilobares"].provenance
    )


def test_curb65_variable_and_rule_are_unresolved() -> None:
    package = build_nac_package()
    variable = package.variables["curb65_score"]
    assert variable.provenance.derivation.value == "UNRESOLVED"
    rule = package.rules["rule_hosp_criterio_curb65"]
    assert rule.provenance.derivation.value == "UNRESOLVED"
    assert rule.validation_status.value == "UNRESOLVED"


def test_uci_bullet1_is_inferred() -> None:
    package = build_nac_package()
    rule = package.rules["rule_uci_bullet1"]
    assert rule.provenance.derivation.value == "INFERRED"


def test_unresolved_derivation_never_upgraded_to_validated_status() -> None:
    package = build_nac_package()
    for rule in package.rules.values():
        if rule.provenance.derivation.value == "UNRESOLVED":
            assert rule.validation_status.value in {"UNRESOLVED", "DRAFT", "EXTRACTED"}


def test_package_survives_full_serialization_round_trip() -> None:
    package: ProtocolVersion = load_package(dump_package(build_nac_package()))
    assert package == build_nac_package()
