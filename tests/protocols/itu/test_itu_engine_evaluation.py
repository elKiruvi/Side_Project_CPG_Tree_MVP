"""Engine-evaluation tests for the ITU package.

These tests exercise the ITU package through the unchanged generic engine:
test-case harness, determinism, purity, shared-expression construction
invariants, UNKNOWN preservation, exception semantics, NOT_APPLICABLE
population gating, and the declarative treatment-alternative contract.
"""

from __future__ import annotations

from cpg_tree.engine import Case, RuleOutcome, evaluate_package, run_test_cases
from cpg_tree.knowledge import TruthValue, dump_package
from cpg_tree.protocols.itu_v06 import build_itu_package

EXPECTED_TEST_CASES = 93


def test_all_package_test_cases_pass() -> None:
    outcomes = run_test_cases(build_itu_package())
    assert len(outcomes) == EXPECTED_TEST_CASES
    assert all(outcome.passed for outcome in outcomes)


def test_repeated_package_evaluation_is_equal() -> None:
    package = build_itu_package()
    case = Case.from_inputs(
        {"itu_alta": True, "hospitalizado": True, "colonizacion_blee": True}
    )
    first = evaluate_package(package, case)
    second = evaluate_package(package, case)
    assert first == second
    assert first.rule_results == second.rule_results


def test_package_evaluation_does_not_mutate_the_package() -> None:
    package = build_itu_package()
    before = dump_package(package)
    case = Case.from_inputs({"itu_baja": True})
    evaluate_package(package, case)
    assert dump_package(package) == before


def test_hospitalization_expression_is_shared_by_construction() -> None:
    package = build_itu_package()
    hospitalizacion = package.rules["rule_hospitalizacion"].condition
    assert package.rules["rule_analisis_sangre"].applies_to is hospitalizacion


def test_analisis_sangre_condition_is_established_infection() -> None:
    package = build_itu_package()
    condition = package.rules["rule_analisis_sangre"].condition
    assert condition.variable_ref == "infeccion_urinaria"


def test_urocultivo_rule_carries_sample_restriction_actions() -> None:
    package = build_itu_package()
    case = Case.from_inputs({"sospecha_itu": True, "mujer": False})
    result = evaluate_package(package, case)
    urocultivo = next(
        item for item in result.rule_results if item.rule_id == "rule_urocultivo_indicado"
    )
    assert urocultivo.outcome is RuleOutcome.MATCHED
    assert urocultivo.action_refs == ("act_urocultivo", "act_restriccion_muestra_previa")


def test_ba_indication_and_table_row_share_the_same_condition() -> None:
    package = build_itu_package()
    assert (
        package.rules["rule_tto_ba_indicado"].condition
        == package.rules["rule_t1_ba_row"].condition
    )


def test_missing_data_preserves_unknown_not_false() -> None:
    package = build_itu_package()
    case = Case.from_inputs({"choque_septico": None})
    result = evaluate_package(package, case)
    hospitalizacion = next(
        item for item in result.rule_results if item.rule_id == "rule_hospitalizacion"
    )
    assert hospitalizacion.outcome is RuleOutcome.INDETERMINATE
    assert hospitalizacion.condition_result is TruthValue.UNKNOWN


def test_amikacina_exception_projects_from_excepted_in_shock() -> None:
    package = build_itu_package()
    case = Case.from_inputs(
        {
            "itu_alta": True,
            "hospitalizado": True,
            "colonizacion_blee": True,
            "choque_septico": True,
        }
    )
    result = evaluate_package(package, case)
    by_id = {item.rule_id: item for item in result.rule_results}
    amikacina = by_id["rule_t1_alta_hosp_con_fr_amikacina"]
    meropenem = by_id["rule_t1_alta_hosp_con_fr_meropenem"]
    assert amikacina.outcome is RuleOutcome.EXCEPTED
    assert amikacina.action_refs == ()
    assert meropenem.outcome is RuleOutcome.MATCHED
    assert meropenem.action_refs == ("act_meropenem",)


def test_pregnancy_rules_are_not_applicable_to_non_pregnant() -> None:
    package = build_itu_package()
    case = Case.from_inputs({"gestante": False, "itu_alta": True, "itu_baja": True})
    result = evaluate_package(package, case)
    by_id = {item.rule_id: item for item in result.rule_results}
    assert by_id["rule_t2_ba_gestante"].outcome is RuleOutcome.NOT_APPLICABLE
    assert by_id["rule_t2_itu_baja_gestante"].outcome is RuleOutcome.NOT_APPLICABLE
    assert by_id["rule_t2_preventiva_alta"].outcome is RuleOutcome.NOT_APPLICABLE


def test_not_applicable_is_distinct_from_not_matched() -> None:
    package = build_itu_package()
    case = Case.from_inputs(
        {
            "gestante": False,
            "itu_alta": True,
            "pielonefritis": True,
            "hospitalizado": True,
        }
    )
    result = evaluate_package(package, case)
    by_id = {item.rule_id: item for item in result.rule_results}
    assert by_id["rule_ecografia_renal_gestante"].outcome is RuleOutcome.NOT_APPLICABLE
    assert by_id["rule_t1_alta_ambulatoria"].outcome is RuleOutcome.NOT_MATCHED


def test_gestational_ultrasound_pain_alone_does_not_trigger() -> None:
    package = build_itu_package()
    case = Case.from_inputs(
        {
            "gestante": True,
            "dolor": True,
            "sospecha_litiasis": False,
            "pielonefritis": False,
            "mas_de_un_episodio_itu": False,
            "hematuria": False,
        }
    )
    result = evaluate_package(package, case)
    rule = next(
        item for item in result.rule_results if item.rule_id == "rule_ecografia_renal_gestante"
    )
    assert rule.outcome is RuleOutcome.NOT_MATCHED
    assert rule.condition_result is TruthValue.FALSE


def test_suspicion_does_not_activate_established_infection_rules() -> None:
    package = build_itu_package()
    case = Case.from_inputs(
        {"sospecha_itu": True, "infeccion_urinaria": False, "choque_septico": True}
    )
    result = evaluate_package(package, case)
    by_id = {item.rule_id: item for item in result.rule_results}
    assert by_id["rule_imagen_urgente"].outcome is RuleOutcome.NOT_MATCHED
    assert by_id["rule_analisis_sangre"].condition_result is TruthValue.FALSE


def test_temporal_discharge_threshold_is_inclusive_48_hours() -> None:
    package = build_itu_package()
    case = Case.from_inputs({"afebril_horas": 48})
    result = evaluate_package(package, case)
    afebril = next(
        item for item in result.rule_results if item.rule_id == "rule_egreso_afebril_48h"
    )
    assert afebril.outcome is RuleOutcome.MATCHED


def test_treatment_alternatives_are_never_selected_by_the_engine() -> None:
    package = build_itu_package()
    case = Case.from_inputs({"itu_baja": True})
    result = evaluate_package(package, case)
    baja = next(item for item in result.rule_results if item.rule_id == "rule_t1_itu_baja")
    assert baja.outcome is RuleOutcome.MATCHED
    assert baja.action_refs == (
        "act_t1_nitrofurantoina",
        "act_t1_cefalexina",
        "act_t1_fosfomicina",
    )


def test_fr_bgn_expression_is_reused_across_treatment_rules() -> None:
    package = build_itu_package()
    shared = package.rules["rule_fr_bgn_resistentes"].condition
    assert package.rules["rule_t1_alta_hosp_con_fr_piperacilina"].condition.operands[2] is shared
    assert package.rules["rule_t1_alta_hosp_con_fr_amikacina"].condition.operands[2] is shared
    assert package.rules["rule_t1_alta_hosp_con_fr_meropenem"].condition.operands[2] is shared
    assert package.rules["rule_t1_alta_hosp_sin_fr"].condition.operands[2].operands[0] is shared
    assert package.rules["rule_t2_itu_alta_gestante_cefazolina"].condition.operands[1].operands[0] is shared
    assert package.rules["rule_t2_itu_alta_gestante_piperacilina"].condition.operands[1] is shared
    assert package.rules["rule_t2_itu_alta_gestante_meropenem"].condition.operands[1] is shared


def test_every_rule_has_a_non_empty_condition() -> None:
    package = build_itu_package()
    for rule in package.rules.values():
        assert rule.condition is not None
        assert hasattr(rule.condition, "operands") or hasattr(rule.condition, "variable_ref")


def test_unresolved_unknown_never_becomes_false_in_ba_indication() -> None:
    package = build_itu_package()
    case = Case.from_inputs(
        {
            "bacteriuria_significativa": None,
            "sin_signos_sintomas_itu": True,
            "gestante": True,
            "procedimiento_invasivo_vias_urinarias": False,
        }
    )
    result = evaluate_package(package, case)
    rule = next(item for item in result.rule_results if item.rule_id == "rule_tto_ba_indicado")
    assert rule.outcome is RuleOutcome.INDETERMINATE
    assert rule.condition_result is TruthValue.UNKNOWN
