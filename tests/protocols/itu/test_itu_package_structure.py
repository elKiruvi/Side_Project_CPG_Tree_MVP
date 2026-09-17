"""Structure tests for the ITU CT-PL-197 v06 knowledge package.

These tests verify counts, provenance completeness, the builder/YAML authority
contract, the exact Phase 3 validator outcome, the v3 semantic corrections
(bacteriuria unification, infection vs suspicion, pediatric evidence-only
scope, treatment alternatives, first-trimester ambiguity), and the
source-faithful strict/inclusive threshold inventory. They contain no clinical
assumptions: everything is derived from the source package.
"""

from __future__ import annotations

from pathlib import Path

from cpg_tree.knowledge import ProtocolVersion, dump_package, load_package
from cpg_tree.knowledge.conditions import Condition, LogicalOperand
from cpg_tree.knowledge.enums import ActionType, ConditionKind, DerivationState
from cpg_tree.protocols.itu_v06 import (
    DOCUMENT_ID,
    SHA256,
    build_itu_package,
)
from cpg_tree.validation import validate_package

EXPECTED_VARIABLES = 76
EXPECTED_RULES = 60
EXPECTED_ACTIONS = 45
EXPECTED_TEST_CASES = 93
EXPECTED_FRAGMENTS = 84
EXPECTED_VALIDATION_ITEMS = 12
EXPECTED_DOCUMENTS = 1

HOSPITALIZACION_CRITERIOS_ADULTOS = 8
FR_BGN_FACTORES = 3
UMBRAL_TAS_EGRESO = 90
UMBRAL_FC_EGRESO = 100
UMBRAL_FR_EGRESO = 24
UMBRAL_SATO2_EGRESO = 90
UMBRAL_PAO2_EGRESO = 60
UMBRAL_AFEBRIL_HORAS = 48
UMBRAL_FIEBRE_HORAS = 72

ARTIFACT_PATH = (
    Path(__file__).resolve().parents[3] / "protocols" / "CT-PL-197" / "v06" / "package.yaml"
)

GENERIC_LAYERS = (
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "engine",
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "validation",
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "extraction",
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "knowledge",
)


def test_package_counts_match_the_plan() -> None:
    package = build_itu_package()
    assert len(package.variables) == EXPECTED_VARIABLES
    assert len(package.rules) == EXPECTED_RULES
    assert len(package.actions) == EXPECTED_ACTIONS
    assert len(package.test_cases) == EXPECTED_TEST_CASES
    assert len(package.fragments) == EXPECTED_FRAGMENTS
    assert len(package.validation_items) == EXPECTED_VALIDATION_ITEMS
    assert len(package.documents) == EXPECTED_DOCUMENTS


def test_metadata_matches_the_source() -> None:
    package = build_itu_package()
    assert package.protocol.id == "CT-PL-197"
    assert package.version == "v06"
    assert package.approval_date == "2025-09-30"


def test_document_identity_matches_source_sha256() -> None:
    package = build_itu_package()
    document = package.documents[DOCUMENT_ID]
    assert document.sha256 == SHA256
    assert document.document_id == DOCUMENT_ID


def test_validate_package_has_exact_expected_findings() -> None:
    package = build_itu_package()
    report = validate_package(package)
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 0
    assert report.findings == ()


def test_validation_items_are_open_and_not_findings() -> None:
    package = build_itu_package()
    report = validate_package(package)
    assert len(package.validation_items) == EXPECTED_VALIDATION_ITEMS
    for item in package.validation_items.values():
        assert item.status.value == "OPEN"
    assert len(report.findings) == 0


def test_every_rule_has_provenance() -> None:
    package = build_itu_package()
    for rule in package.rules.values():
        assert rule.provenance is not None
        assert rule.provenance.fragment_refs


def test_every_variable_has_provenance() -> None:
    package = build_itu_package()
    for variable in package.variables.values():
        assert variable.provenance is not None
        assert variable.provenance.fragment_refs


def test_every_action_has_provenance() -> None:
    package = build_itu_package()
    for action in package.actions.values():
        assert action.provenance is not None
        assert action.provenance.fragment_refs


def test_fragments_anchor_to_the_itu_document() -> None:
    package = build_itu_package()
    for fragment in package.fragments.values():
        assert fragment.document_id == DOCUMENT_ID
        assert fragment.verbatim_text and fragment.verbatim_text.strip()


def test_builder_dump_is_deterministic() -> None:
    first = dump_package(build_itu_package())
    second = dump_package(build_itu_package())
    assert first == second


def test_yaml_artifact_matches_builder_exactly() -> None:
    assert ARTIFACT_PATH.is_file()
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")
    assert artifact_text == dump_package(build_itu_package())


def test_yaml_artifact_round_trips_to_the_builder_package() -> None:
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")
    loaded = load_package(artifact_text)
    assert loaded == build_itu_package()


def test_yaml_artifact_round_trip_is_stable() -> None:
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8")
    assert load_package(artifact_text) == load_package(artifact_text)


def test_package_survives_full_serialization_round_trip() -> None:
    package: ProtocolVersion = load_package(dump_package(build_itu_package()))
    assert package == build_itu_package()


def test_derived_decision_inputs_are_absent() -> None:
    package = build_itu_package()
    forbidden = {
        "indicacion_hospitalizacion",
        "indicacion_egreso",
        "indicacion_tto_ba",
        "fr_bgn_resistentes",
        "itu_alta_hospitalaria",
        "itu_alta_ambulatoria",
        "diagnostico_itu",
        "recuento_significativo_colonias",
        "muestra_antes_primera_dosis_antibiotico",
    }
    assert forbidden.isdisjoint(package.variables)


def test_bacteriuria_concept_is_unified() -> None:
    package = build_itu_package()
    assert "bacteriuria_significativa" in package.variables
    assert "recuento_significativo_colonias" not in package.variables
    variable = package.variables["bacteriuria_significativa"]
    assert variable.provenance is not None
    assert set(variable.provenance.fragment_refs) == {
        "frag_p1_def_ba",
        "frag_p1_def_itu",
        "frag_p1_def_itu_bajo",
        "frag_p1_def_itu_alto",
    }
    assert variable.provenance.derivation is DerivationState.NORMALIZED
    assert variable.provenance.notes


def test_infection_variable_replaces_diagnostico_itu() -> None:
    package = build_itu_package()
    assert "infeccion_urinaria" in package.variables
    assert "diagnostico_itu" not in package.variables
    assert "sospecha_itu" in package.variables


def test_two_complicada_definitions_remain_distinct_rules() -> None:
    package = build_itu_package()
    assert "rule_def_itu_complicada_estructural" in package.rules
    assert "rule_def_itu_complicada_clinica" in package.rules
    estructural = package.rules["rule_def_itu_complicada_estructural"]
    clinica = package.rules["rule_def_itu_complicada_clinica"]
    assert estructural.condition is not clinica.condition
    assert estructural.provenance is not clinica.provenance


def test_pediatric_hospitalization_criterion_is_evidence_only() -> None:
    package = build_itu_package()
    assert "frag_p3_hosp_pediatrica" in package.fragments
    assert "rule_hosp_criterio_pediatrica" not in package.rules
    hospitalizacion = package.rules["rule_hospitalizacion"]
    assert len(hospitalizacion.condition.operands) == HOSPITALIZACION_CRITERIOS_ADULTOS
    assert all(
        "poblacion_pediatrica" not in _condition_refs(op)
        for op in hospitalizacion.condition.operands
    )


def test_no_prostatitis_education_action_exists() -> None:
    package = build_itu_package()
    for action in package.actions.values():
        assert action.type is not ActionType.EDUCATE


def test_treatment_alternatives_are_multiple_prescribe_refs() -> None:
    package = build_itu_package()
    rule = package.rules["rule_t1_itu_baja"]
    assert rule.action_refs == (
        "act_t1_nitrofurantoina",
        "act_t1_cefalexina",
        "act_t1_fosfomicina",
    )
    for ref in rule.action_refs:
        assert package.actions[ref].type is ActionType.PRESCRIBE


def test_sample_restriction_is_attached_to_urocultivo_rule() -> None:
    package = build_itu_package()
    rule = package.rules["rule_urocultivo_indicado"]
    assert rule.action_refs == ("act_urocultivo", "act_restriccion_muestra_previa")
    assert "rule_muestra_antes_antibiotico" not in package.rules
    assert "frag_p3_toma_muestra_antibiotico" in rule.provenance.fragment_refs


def test_ba_treatment_indication_requires_ba_context() -> None:
    package = build_itu_package()
    rule = package.rules["rule_tto_ba_indicado"]
    refs = _condition_refs(rule.condition)
    assert {"bacteriuria_significativa", "sin_signos_sintomas_itu"} <= refs
    assert package.rules["rule_t1_ba_row"].condition == rule.condition


def test_gestational_ultrasound_preserves_lithiasis_relation() -> None:
    package = build_itu_package()
    rule = package.rules["rule_ecografia_renal_gestante"]
    condition = rule.condition
    assert condition.operator.value == "OR"
    limbs = [_condition_refs(op) for op in condition.operands]
    assert {"pielonefritis"} in limbs
    assert {"mas_de_un_episodio_itu"} in limbs
    lithiasis_limb = condition.operands[2]
    assert lithiasis_limb.operator.value == "AND"
    inner = [_condition_refs(op) for op in lithiasis_limb.operands]
    assert {"sospecha_litiasis"} in inner
    assert {"hematuria", "dolor"} in inner
    assert rule.applies_to is not None
    assert _condition_refs(rule.applies_to) == {"gestante"}


def test_applies_to_used_as_population_gate() -> None:
    package = build_itu_package()
    hospitalizacion = package.rules["rule_hospitalizacion"].condition
    analisis = package.rules["rule_analisis_sangre"]
    assert analisis.applies_to is hospitalizacion
    assert _condition_refs(analisis.condition) == {"infeccion_urinaria"}
    hemocultivos = package.rules["rule_hemocultivos"]
    assert _condition_refs(hemocultivos.applies_to) == {"pielonefritis"}


def test_every_rule_has_a_condition() -> None:
    package = build_itu_package()
    for rule in package.rules.values():
        assert rule.condition is not None


def test_validation_statuses_are_extracted() -> None:
    package = build_itu_package()
    for rule in package.rules.values():
        assert rule.validation_status.value == "EXTRACTED"


def test_derivations_are_source_stated_or_normalized() -> None:
    package = build_itu_package()
    allowed = {DerivationState.SOURCE_STATED, DerivationState.NORMALIZED}
    for rule in package.rules.values():
        assert rule.provenance.derivation in allowed
    for action in package.actions.values():
        assert action.provenance is not None
        assert action.provenance.derivation in allowed
    for normalized in (
        rule.provenance
        for rule in package.rules.values()
        if rule.provenance.derivation is DerivationState.NORMALIZED
    ):
        assert normalized.notes


def test_negative_source_flags_are_preserved() -> None:
    package = build_itu_package()
    expected = {
        "sin_signos_sintomas_itu",
        "sin_leucorrea",
        "sin_irritacion_vaginal",
        "sin_fiebre",
        "sin_dolor_lumbar",
        "sin_compromiso_sistemico",
        "germen_resistente_sin_opcion_ambulatoria",
        "sintomas_no_explicados_otra_patologia",
        "ausencia_piuria_sedimento",
    }
    assert expected <= set(package.variables)


def test_strict_and_inclusive_thresholds_are_exact() -> None:
    package = build_itu_package()
    assert package.rules["rule_egreso_tas"].condition.operator.value == "GT"
    assert package.rules["rule_egreso_tas"].condition.operand == UMBRAL_TAS_EGRESO
    assert package.rules["rule_egreso_fc"].condition.operator.value == "LT"
    assert package.rules["rule_egreso_fc"].condition.operand == UMBRAL_FC_EGRESO
    assert package.rules["rule_egreso_fr"].condition.operator.value == "LT"
    assert package.rules["rule_egreso_fr"].condition.operand == UMBRAL_FR_EGRESO
    sato2 = package.rules["rule_egreso_sato2_pao2"].condition.operands
    assert sato2[0].operator.value == "GT" and sato2[0].operand == UMBRAL_SATO2_EGRESO
    assert sato2[1].operator.value == "GT" and sato2[1].operand == UMBRAL_PAO2_EGRESO
    assert package.rules["rule_piuria_mayor_10"].condition.operator.value == "GT"
    assert (
        package.rules["rule_urocultivo_positivo_1e5"].condition.operands[0].operator.value == "GE"
    )
    assert (
        package.rules["rule_urocultivo_positivo_1e3"].condition.operands[0].operator.value == "GE"
    )
    assert (
        package.rules["rule_urocultivo_positivo_1e2"].condition.operands[0].operator.value == "GE"
    )


def test_temporal_conditions_use_hours_duration() -> None:
    package = build_itu_package()
    afebril = package.rules["rule_egreso_afebril_48h"].condition
    assert afebril.kind is ConditionKind.TEMPORAL
    assert afebril.duration_value == UMBRAL_AFEBRIL_HORAS
    assert afebril.duration_unit == "hours"
    fiebre = package.rules["rule_imagen_urgente"].condition.operands[1].operands[3].operands[0]
    assert fiebre.kind is ConditionKind.TEMPORAL
    assert fiebre.duration_value == UMBRAL_FIEBRE_HORAS
    assert fiebre.duration_unit == "hours"


def test_generic_layers_do_not_import_protocols() -> None:
    for layer in GENERIC_LAYERS:
        for source_file in layer.rglob("*.py"):
            content = source_file.read_text(encoding="utf-8")
            assert "cpg_tree.protocols" not in content, (
                f"{source_file} imports the protocol knowledge layer"
            )


def test_fr_bgn_is_a_shared_expression_not_a_variable() -> None:
    package = build_itu_package()
    assert "fr_bgn_resistentes" not in package.variables
    shared = package.rules["rule_fr_bgn_resistentes"].condition
    assert shared.operator.value == "OR"
    assert len(shared.operands) == FR_BGN_FACTORES
    piperacilina = package.rules["rule_t1_alta_hosp_con_fr_piperacilina"]
    assert piperacilina.condition.operands[2] is shared
    sin_fr = package.rules["rule_t1_alta_hosp_sin_fr"]
    assert sin_fr.condition.operands[2].operands[0] is shared


def test_first_trimester_restriction_is_not_medication_specific() -> None:
    package = build_itu_package()
    item = package.validation_items["vi_evitar_primer_trimestre_ambiguedad"]
    assert item.category == "ambiguity"
    for action in package.actions.values():
        payload = action.payload or {}
        assert "evitar_primer_trimestre" not in payload


def _condition_refs(operand: LogicalOperand) -> set[str]:
    if isinstance(operand, Condition):
        return {operand.variable_ref}
    refs: set[str] = set()
    for child in operand.operands:
        refs.update(_condition_refs(child))
    return refs
