"""Engine-evaluation tests for the NAC package.

These tests exercise the NAC package through the unchanged generic engine:
test-case harness, determinism, purity, shared-expression construction
invariants, UNKNOWN preservation, and the discharge action set.
"""

from __future__ import annotations

from pathlib import Path

from cpg_tree.engine import Case, RuleOutcome, evaluate_package, run_test_cases
from cpg_tree.knowledge import TruthValue, dump_package
from cpg_tree.protocols.nac_v09 import build_nac_package

EXPECTED_TEST_CASES = 30
UCI_3DE_UMBRAL = 3
UCI_3DE_CRITERIOS = 9
HEMOCULTIVOS_UMBRAL = 2
HEMOCULTIVOS_CRITERIOS = 4
AFEBRIL_UMBRAL_HORAS = 48

GENERIC_LAYERS = (
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "engine",
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "validation",
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "extraction",
)


def test_all_package_test_cases_pass() -> None:
    outcomes = run_test_cases(build_nac_package())
    assert len(outcomes) == EXPECTED_TEST_CASES
    assert all(outcome.passed for outcome in outcomes)


def test_repeated_package_evaluation_is_equal() -> None:
    package = build_nac_package()
    case = Case.from_inputs({"inmunosuprimido": True, "curb65_score": 0, "bun": 31})
    first = evaluate_package(package, case)
    second = evaluate_package(package, case)
    assert first == second
    assert first.rule_results == second.rule_results


def test_package_evaluation_does_not_mutate_the_package() -> None:
    package = build_nac_package()
    before = dump_package(package)
    case = Case.from_inputs({"inmunosuprimido": True})
    evaluate_package(package, case)
    assert dump_package(package) == before


def test_hospitalization_expression_is_shared_by_construction() -> None:
    package = build_nac_package()
    hospitalizacion = package.rules["rule_hospitalizacion"].condition
    assert package.rules["rule_labs_hospitalizacion"].condition is hospitalizacion
    assert package.rules["rule_hemocultivos"].applies_to is hospitalizacion
    assert package.rules["rule_gram_cultivo_esputo"].condition.operands[1] is hospitalizacion


def test_hospitalization_rule_and_labs_rule_never_diverge() -> None:
    package = build_nac_package()
    case = Case.from_inputs(
        {
            "descompensacion_enfermedad_base": False,
            "inmunosuprimido": True,
            "sospecha_germenes_resistentes": False,
            "intolerancia_via_oral": False,
            "sepsis_origen_pulmonar": False,
            "choque_origen_pulmonar": False,
            "compromiso_multilobar": False,
            "derrame_pleural_rx": False,
            "curb65_score": 0,
            "factores_sociales": False,
            "requerimiento_oxigeno_suplementario": False,
        }
    )
    result = evaluate_package(package, case)
    by_id = {item.rule_id: item for item in result.rule_results}
    assert by_id["rule_hospitalizacion"].outcome is RuleOutcome.MATCHED
    assert by_id["rule_labs_hospitalizacion"].outcome is RuleOutcome.MATCHED


def test_discharge_rule_carries_exact_action_set() -> None:
    package = build_nac_package()
    case = Case.from_inputs(
        {
            "afebril_horas": 48,
            "pas_sistolica": 91,
            "fc": 99,
            "fr_respiratoria": 23,
            "saturacion_oxigeno": 91,
            "po2": 61,
            "tolera_via_oral": True,
            "comorbilidades_compensadas": True,
            "tratamiento_antibiotico_ambulatorio_asegurado": True,
            "condiciones_sociales_adecuadas": True,
        }
    )
    result = evaluate_package(package, case)
    egreso = next(item for item in result.rule_results if item.rule_id == "rule_plan_egreso")
    assert egreso.outcome is RuleOutcome.MATCHED
    assert egreso.action_refs == (
        "act_egreso",
        "act_educar_recaida",
        "act_cita_revision_4_semanas",
    )


def test_missing_data_preserves_unknown_not_false() -> None:
    package = build_nac_package()
    case = Case.from_inputs({"curb65_score": None, "inmunosuprimido": False})
    result = evaluate_package(package, case)
    hospitalizacion = next(
        item for item in result.rule_results if item.rule_id == "rule_hospitalizacion"
    )
    assert hospitalizacion.outcome is RuleOutcome.INDETERMINATE
    assert hospitalizacion.condition_result is TruthValue.UNKNOWN


def test_at_least_n_formula_is_preserved() -> None:
    package = build_nac_package()
    three_de = package.rules["rule_uci_criterios_3de"].condition
    assert three_de.operator.value == "AT_LEAST_N"
    assert three_de.threshold == UCI_3DE_UMBRAL
    assert len(three_de.operands) == UCI_3DE_CRITERIOS
    hemocultivos = package.rules["rule_hemocultivos"].condition
    two_of_four = hemocultivos.operands[1]
    assert two_of_four.operator.value == "AT_LEAST_N"
    assert two_of_four.threshold == HEMOCULTIVOS_UMBRAL
    assert len(two_of_four.operands) == HEMOCULTIVOS_CRITERIOS


def test_temporal_discharge_threshold_is_inclusive_48_hours() -> None:
    package = build_nac_package()
    temporal = package.rules["rule_plan_egreso"].condition.operands[0]
    assert temporal.kind.value == "TEMPORAL"
    assert temporal.temporal_operator.value == "AT_LEAST_FOR_LAST"
    assert temporal.duration_value == AFEBRIL_UMBRAL_HORAS
    assert temporal.duration_unit == "hours"


def test_generic_layers_do_not_import_protocols() -> None:
    for layer in GENERIC_LAYERS:
        for source_file in layer.rglob("*.py"):
            content = source_file.read_text(encoding="utf-8")
            assert "cpg_tree.protocols" not in content, (
                f"{source_file} imports the protocol knowledge layer"
            )


def test_unresolved_rule_is_mechanically_evaluated_without_validation_claim() -> None:
    package = build_nac_package()
    case = Case.from_inputs({"curb65_score": 2})
    result = evaluate_package(package, case)
    curb65 = next(
        item for item in result.rule_results if item.rule_id == "rule_hosp_criterio_curb65"
    )
    assert curb65.outcome is RuleOutcome.MATCHED
    assert curb65.provenance.derivation.value == "UNRESOLVED"
    assert curb65.validation_status.value == "UNRESOLVED"
