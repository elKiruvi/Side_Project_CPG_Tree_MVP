"""ITU CT-PL-197 v06 knowledge package builder.

Authoritative protocol-specific knowledge for the institutional protocol
"PROTOCOLO INFECCION DEL TRACTO URINARIO (ITU) Y BACTERIURIA ASINTOMATICA
EN POBLACION ADULTA" (code CT-PL-197, version 06, approved 30-sep-2025,
adult patients).

This module is the single source of truth for the ITU knowledge package.
``build_itu_package`` constructs the ProtocolVersion; the serialized YAML
artifact under ``protocols/CT-PL-197/v06/package.yaml`` is generated from it
and must never be edited independently.

Every variable, rule, action, and validation item carries provenance anchored
to fine-grained fragments of the extracted source document
(doc-800af94bc0654138, sha256 800af94b...). Known source limitations remain
explicit: the pediatric hospitalization bullet and prostatitis are preserved
as source evidence outside the adult executable scope, the first-trimester
avoidance note of Table 2 cannot be mapped to a specific medication from the
text layer, and history/calendar inputs are external clinical inputs that the
deterministic engine never computes.

TRV004 is disabled for this module on purpose: structural validation of the
canonical model raises ValueError by domain contract.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from cpg_tree.knowledge import (
    Action,
    ActionType,
    ComparisonOperator,
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    LogicalOperator,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    SourceDocument,
    SourceFragment,
    TemporalOperator,
    TestCase,
    TruthValue,
    ValidationItem,
    ValidationItemStatus,
    ValidationStatus,
    Variable,
    VariableType,
    dump_package,
)
from cpg_tree.knowledge.conditions import LogicalOperand
from cpg_tree.knowledge.types import Scalar

DOCUMENT_ID = "doc-800af94bc0654138"
SHA256 = "800af94bc0654138a8e213cd1e42ad2e6021a955226a142b36c5b3f24e24777a"
SOURCE_FILENAME = "CT-PL-197 PROTOCOLO INFECCION TRACTO URINARIO -ITU ADULTOS (v6-sep-2025).pdf"
SOURCE_BYTE_SIZE = 272638

T = TruthValue.TRUE
F = TruthValue.FALSE
U = TruthValue.UNKNOWN

EXTRACTED = ValidationStatus.EXTRACTED


def _fragment(
    fragment_id: str,
    page: int,
    section: str | None,
    verbatim_text: str,
) -> SourceFragment:
    return SourceFragment(
        id=fragment_id,
        document_id=DOCUMENT_ID,
        page=page,
        section=section,
        verbatim_text=verbatim_text,
    )


def _prov(
    derivation: DerivationState,
    fragment_refs: tuple[str, ...],
    notes: str | None = None,
) -> Provenance:
    return Provenance(derivation=derivation, fragment_refs=fragment_refs, notes=notes)


def _variable(  # noqa: PLR0913
    variable_id: str,
    label: str,
    variable_type: VariableType,
    provenance: Provenance,
    *,
    unit: str | None = None,
    allowed_values: tuple[str, ...] | None = None,
    description: str | None = None,
) -> Variable:
    return Variable(
        id=variable_id,
        label=label,
        type=variable_type,
        unit=unit,
        allowed_values=allowed_values,
        description=description,
        provenance=provenance,
    )


def _flag(variable_ref: str, expected: bool = True) -> Condition:
    return Condition(kind=ConditionKind.FLAG, variable_ref=variable_ref, expected=expected)


def _gt(variable_ref: str, operand: float) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=variable_ref,
        operator=ComparisonOperator.GT,
        operand=operand,
    )


def _lt(variable_ref: str, operand: float) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=variable_ref,
        operator=ComparisonOperator.LT,
        operand=operand,
    )


def _ge(variable_ref: str, operand: float) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=variable_ref,
        operator=ComparisonOperator.GE,
        operand=operand,
    )


def _membership(variable_ref: str, values: tuple[str, ...]) -> Condition:
    return Condition(kind=ConditionKind.MEMBERSHIP, variable_ref=variable_ref, values=values)


def _and(*operands: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(operator=LogicalOperator.AND, operands=operands)


def _or(*operands: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(operator=LogicalOperator.OR, operands=operands)


def _not(operand: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(operator=LogicalOperator.NOT, operands=(operand,))


def _temporal(variable_ref: str, duration_value: float, duration_unit: str) -> Condition:
    return Condition(
        kind=ConditionKind.TEMPORAL,
        variable_ref=variable_ref,
        temporal_operator=TemporalOperator.AT_LEAST_FOR_LAST,
        duration_value=duration_value,
        duration_unit=duration_unit,
    )


def _action(
    action_id: str,
    action_type: ActionType,
    provenance: Provenance,
    *,
    label: str | None = None,
    payload: dict[str, Scalar] | None = None,
) -> Action:
    return Action(
        id=action_id, type=action_type, label=label, payload=payload, provenance=provenance
    )


def _rule(  # noqa: PLR0913
    rule_id: str,
    condition: LogicalOperand,
    provenance: Provenance,
    *,
    action_refs: tuple[str, ...] = (),
    applies_to: LogicalOperand | None = None,
    exceptions: tuple[LogicalOperand, ...] = (),
    notes: str | None = None,
) -> Rule:
    return Rule(
        id=rule_id,
        condition=condition,
        action_refs=action_refs,
        provenance=provenance,
        applies_to=applies_to,
        exceptions=exceptions,
        validation_status=EXTRACTED,
        notes=notes,
    )


def build_itu_package() -> ProtocolVersion:
    """Build the complete ITU CT-PL-197 v06 knowledge package."""
    document = SourceDocument(
        document_id=DOCUMENT_ID,
        filename=SOURCE_FILENAME,
        sha256=SHA256,
        file_format="pdf",
        byte_size=SOURCE_BYTE_SIZE,
    )

    fragments = _build_fragments()
    variables = _build_variables()
    actions = _build_actions()
    expressions = _build_expressions()
    rules = _build_rules(expressions)
    validation_items = _build_validation_items()
    test_cases = _build_test_cases()

    return ProtocolVersion(
        protocol=Protocol(
            id="CT-PL-197",
            name="Protocolo infección del tracto urinario (ITU) y bacteriuria "
            "asintomática en población adulta",
            description="Atención de pacientes adultos con diagnóstico de bacteriuria "
            "asintomática o infección del tracto urinario",
        ),
        version="v06",
        approval_date="2025-09-30",
        change_summary=(
            "Se cambia nombre a protocolo Infección del Tracto Urinario Adultos. "
            "Se cambia definición de ITU complicada. Se actualizan recomendaciones "
            "de manejo según clasificación de ITU y factores de riesgo. Se dan "
            "consideraciones del manejo de la ITU en la gestante."
        ),
        documents={DOCUMENT_ID: document},
        fragments=fragments,
        variables=variables,
        actions=actions,
        rules=rules,
        validation_items=validation_items,
        test_cases=test_cases,
    )


def _build_fragments() -> dict[str, SourceFragment]:
    return {
        "frag_p1_metadata": _fragment(
            "frag_p1_metadata",
            1,
            "PROTOCOLO",
            "PROTOCOLO INFECCION DEL TRACTO URINARIO (ITU) Y BACTERIURIA "
            "ASINTOMATICA EN POBLACION ADULTA",
        ),
        "frag_p1_codigo_version": _fragment(
            "frag_p1_codigo_version",
            1,
            "PROTOCOLO",
            "Proceso: Cuidado y tratamiento Código: CT-PL-197 Versión: 06 "
            "Fecha aprobación: 30-sep-2025",
        ),
        "frag_p1_alcance": _fragment(
            "frag_p1_alcance",
            1,
            None,
            "2. ALCANCE: Esta guía aplica para todo el personal médico que "
            "interviene en la atención de pacientes adultos, excluyendo neonatos "
            "y niños con diagnóstico de bacteriuria asintomática o ITU.",
        ),
        "frag_p1_def_ba": _fragment(
            "frag_p1_def_ba",
            1,
            "3. DEFINICIONES",
            "Bacteriuria asintomática: Recuento significativo de colonias "
            "bacterianas en muestras de orina, colectadas apropiadamente, "
            "provenientes de pacientes sin signos o síntomas atribuibles a ITU.",
        ),
        "frag_p1_def_ba_cultivos": _fragment(
            "frag_p1_def_ba_cultivos",
            1,
            "3. DEFINICIONES",
            "Se requiere 2 urocultivos con el mismo patógeno y perfil de "
            "sensibilidad en mujeres no embarazadas, 1 en hombres y pacientes "
            "gestantes.",
        ),
        "frag_p1_def_ba_piuria": _fragment(
            "frag_p1_def_ba_piuria",
            1,
            "3. DEFINICIONES",
            "En población pediátrica debe haber ausencia de piuria en el sedimento.",
        ),
        "frag_p1_def_itu": _fragment(
            "frag_p1_def_itu",
            1,
            "3. DEFINICIONES",
            "Infección del tracto urinario: Recuento significativo de colonias "
            "bacterianas en muestras de orina, colectadas apropiadamente, en "
            "pacientes con signos o síntomas atribuibles a ITU",
        ),
        "frag_p1_def_itu_complicada_estructural": _fragment(
            "frag_p1_def_itu_complicada_estructural",
            1,
            "3. DEFINICIONES",
            "Infección del tracto urinario complicada: ITU que ocurre en presencia "
            "de alterac iones estructurales o funcionales de las vías urinarias",
        ),
        "frag_p1_def_itu_bajo": _fragment(
            "frag_p1_def_itu_bajo",
            1,
            "3. DEFINICIONES",
            "Infección del tracto urinario bajo (cistitis y uretritis): Infección "
            "aguda de la vejiga y/o la uretra, acompañada por bacteriuria "
            "significativa, en ausencia de leucorrea, irritación vaginal, fiebre, "
            "d olor lumbar y compromiso sistémicos",
        ),
        "frag_p1_def_itu_alto": _fragment(
            "frag_p1_def_itu_alto",
            1,
            "3. DEFINICIONES",
            "Infección del tracto urinario alto (pielonefritis): Infección aguda "
            "del riñón acompañada por bacteriuria significativa.",
        ),
        "frag_p1_def_itu_complicada_clinica": _fragment(
            "frag_p1_def_itu_complicada_clinica",
            1,
            "3. DEFINICIONES",
            "ITU complicada: infección en mujeres u hombres, con compromiso más "
            "allá de la vejiga, incluyendo pielonefritis, ITU febril o "
            "bacteriémica, ITU asociada a catéter y prostatitis (este último tema "
            "excede los alcances del presente protocolo).",
        ),
        "frag_p2_clasificacion_alta_baja": _fragment(
            "frag_p2_clasificacion_alta_baja",
            2,
            None,
            "La presentación clínica de la ITU permite clasificar la infección "
            "como alta o baja, clasificación necesaria para definir el tratamiento "
            "y el pronóstico.",
        ),
        "frag_p2_no_sintomas_itu": _fragment(
            "frag_p2_no_sintomas_itu",
            2,
            None,
            "No se consideran síntomas compatibles con ITU la orina turb ia o de mal olor.",
        ),
        "frag_p2_embarazada_debe_tratarse": _fragment(
            "frag_p2_embarazada_debe_tratarse",
            2,
            None,
            "En mujeres embarazadas, la bacteriuria asintomática debe tratarse "
            "porque se ha asociado con un mayor riesgo de pielonefritis",
        ),
        "frag_p2_citoquimico": _fragment(
            "frag_p2_citoquimico",
            2,
            "5. Diagnóstico",
            "Se debe realizar citoquímico de orina a todo paciente en el servicio "
            "de urgencias con sospecha de ITU, excepto mujeres con primer episodio "
            "y síntomas típicos.",
        ),
        "frag_p2_tirilla_descarta": _fragment(
            "frag_p2_tirilla_descarta",
            2,
            "5. Diagnóstico",
            "La tirilla de orina es una herramienta de tamizaje para el "
            "diagnóstico, un resultado normal en pacientes con baja sospecha "
            "clínica descarta el diagnóstico.",
        ),
        "frag_p2_piuria": _fragment(
            "frag_p2_piuria",
            2,
            "5. Diagnóstico",
            "Hay una alta correlación entre la presencia de piuria (>10 "
            "leucocitos) e infección, su ausencia puede sugerir colonización",
        ),
        "frag_p3_gram": _fragment(
            "frag_p3_gram",
            3,
            "5. Diagnóstico",
            "Gram de orina sin centrifugar: Suministra información inmediata sobre "
            "la naturaleza de la infección y sirve para guiar el tratamiento "
            "empírico, por lo que debe realizarse en todos los pacientes en el "
            "servicio de urgencias.",
        ),
        "frag_p3_urocultivo_indicacion": _fragment(
            "frag_p3_urocultivo_indicacion",
            3,
            "5. Diagnóstico",
            "Debe solicitarse en todos los casos, excepto primer episodio de ITU "
            "baja no complicada en mujer premenopáusica.",
        ),
        "frag_p3_urocultivo_positivo_1e5": _fragment(
            "frag_p3_urocultivo_positivo_1e5",
            3,
            "5. Diagnóstico",
            "Los urocultivos se consideran positivos con el crecimiento de ≥10 5 "
            "UFC de una bacteria en una muestra de orina o btenida de forma "
            "adecuada por micción espontánea",
        ),
        "frag_p3_urocultivo_positivo_1e3": _fragment(
            "frag_p3_urocultivo_positivo_1e3",
            3,
            "5. Diagnóstico",
            "con un crecimiento ≥10 3 UFC en un paciente con síntomas no "
            "explicados por otra patología",
        ),
        "frag_p3_urocultivo_positivo_1e2": _fragment(
            "frag_p3_urocultivo_positivo_1e2",
            3,
            "5. Diagnóstico",
            "el crecimiento de ≥10 2 UFC de una bacteria en una muestra de orina "
            "obtenida a través de una sonda vesical recién insertada.",
        ),
        "frag_p3_toma_muestra_antibiotico": _fragment(
            "frag_p3_toma_muestra_antibiotico",
            3,
            "5. Diagnóstico",
            "Toma de la muestra: debe tomarse antes de la primera dosis de antibiótico",
        ),
        "frag_p3_analisis_sangre": _fragment(
            "frag_p3_analisis_sangre",
            3,
            "5. Diagnóstico",
            "En todo paciente con ITU que sea hospitalizado debe obtenerse muestra "
            "de sangre para hemoleucograma, ionograma, función renal y proteína C "
            "reactiva (PCR).",
        ),
        "frag_p3_hemocultivos": _fragment(
            "frag_p3_hemocultivos",
            3,
            "5. Diagnóstico",
            "Los hemocultivos deben solicitarse en todos los casos de pielonefritis "
            "aguda que cursan con fiebre, hipotermia o ch oque séptico.",
        ),
        "frag_p3_imagen_urgente": _fragment(
            "frag_p3_imagen_urgente",
            3,
            "5. Diagnóstico",
            "La realización urgente de ecografía o la tomografía (TC) con "
            "contraste está indicada en pacientes con infección urinaria y choque "
            "séptico asociado, falla renal aguda, clínica de complicación local o "
            "fiebre persistente después de 72 horas de tratamiento antibiótico "
            "correcto.",
        ),
        "frag_p3_imagen_tc_abscesos": _fragment(
            "frag_p3_imagen_tc_abscesos",
            3,
            "5. Diagnóstico",
            "Se hará TC con contraste cuando se busquen pequeños abscesos y áreas "
            "de nefritis local, por la mayor sensibilidad del estudio.",
        ),
        "frag_p3_imagen_urotomografia": _fragment(
            "frag_p3_imagen_urotomografia",
            3,
            "5. Diagnóstico",
            "en los casos de sospecha de alteración estructural, incluyendo la "
            "litiasis de vías urinarias la elección será urotomografía",
        ),
        "frag_p3_imagen_ecografia": _fragment(
            "frag_p3_imagen_ecografia",
            3,
            "5. Diagnóstico",
            "para los casos en los cuales se sospecha una alteración funcional, "
            "especialmente por inadecuado vaciamiento vesical o trastornos "
            "obstructivos de las vías urinarias, la elección será ecografía de "
            "vías urinarias con medición del residuo postmiccional.",
        ),
        "frag_p3_imagen_gestante": _fragment(
            "frag_p3_imagen_gestante",
            3,
            "5. Diagnóstico",
            "En las mujeres embarazadas se hará ecografía renal en todas las "
            "pacientes con pielonefritis, más de un episodio de ITU durante el "
            "embarazo, sospecha de litiasis por hematuria y/o dolor.",
        ),
        "frag_p3_tto_ba_indicaciones": _fragment(
            "frag_p3_tto_ba_indicaciones",
            3,
            "6. TRATAMIENTO",
            "Indicaciones de tratamiento de bacteriuria asintomática",
        ),
        "frag_p3_tto_ba_gestante": _fragment(
            "frag_p3_tto_ba_gestante",
            3,
            "6. TRATAMIENTO",
            "Mujer embarazada",
        ),
        "frag_p3_tto_ba_procedimiento": _fragment(
            "frag_p3_tto_ba_procedimiento",
            3,
            "6. TRATAMIENTO",
            "Procedimiento invasivo de vías urinarias con riesgo de sangrado o "
            "disrupción del uroepitelio",
        ),
        "frag_p3_hosp_choque_septico": _fragment(
            "frag_p3_hosp_choque_septico",
            3,
            "6. TRATAMIENTO",
            "Choque séptico",
        ),
        "frag_p3_hosp_intolerancia": _fragment(
            "frag_p3_hosp_intolerancia",
            3,
            "6. TRATAMIENTO",
            "Intolerancia a la vía oral",
        ),
        "frag_p3_hosp_itu_alta": _fragment(
            "frag_p3_hosp_itu_alta",
            3,
            "6. TRATAMIENTO",
            "ITU alta",
        ),
        "frag_p3_hosp_descompensacion": _fragment(
            "frag_p3_hosp_descompensacion",
            3,
            "6. TRATAMIENTO",
            "Descompensación de la enfermedad de base secundaria a la ITU",
        ),
        "frag_p3_hosp_resistente": _fragment(
            "frag_p3_hosp_resistente",
            3,
            "6. TRATAMIENTO",
            "Demostración de germen resistente sin opción de tratamiento "
            "antibiótico    ambulatorio",
        ),
        "frag_p3_hosp_funcion_renal": _fragment(
            "frag_p3_hosp_funcion_renal",
            3,
            "6. TRATAMIENTO",
            "Deterioro de la función renal asociado a la ITU",
        ),
        "frag_p3_hosp_absceso": _fragment(
            "frag_p3_hosp_absceso",
            3,
            "6. TRATAMIENTO",
            "Absceso renal/pararrenal.",
        ),
        "frag_p3_hosp_pediatrica": _fragment(
            "frag_p3_hosp_pediatrica",
            3,
            "6. TRATAMIENTO",
            "Pielonefritis aguda en pacientes pediátricos.",
        ),
        "frag_p3_hosp_social": _fragment(
            "frag_p3_hosp_social",
            3,
            "6. TRATAMIENTO",
            "Inadecuado soporte social para continuidad de terapia ambulatoria",
        ),
        "frag_p3_egreso_afebril": _fragment(
            "frag_p3_egreso_afebril",
            3,
            "6. TRATAMIENTO",
            "48 horas afebril",
        ),
        "frag_p3_egreso_tas": _fragment(
            "frag_p3_egreso_tas",
            3,
            "6. TRATAMIENTO",
            "TAS > 90 mmHg",
        ),
        "frag_p4_egreso_fc": _fragment("frag_p4_egreso_fc", 4, "6. TRATAMIENTO", "FC < 100 lpm"),
        "frag_p4_egreso_fr": _fragment("frag_p4_egreso_fr", 4, "6. TRATAMIENTO", "FR < 24 rpm"),
        "frag_p4_egreso_sato2_pao2": _fragment(
            "frag_p4_egreso_sato2_pao2", 4, "6. TRATAMIENTO", "Sat O2 > 90% o PaO2 > 60"
        ),
        "frag_p4_egreso_via_oral": _fragment(
            "frag_p4_egreso_via_oral", 4, "6. TRATAMIENTO", "Tolerancia a la vía oral"
        ),
        "frag_p4_egreso_comorbilidades": _fragment(
            "frag_p4_egreso_comorbilidades", 4, "6. TRATAMIENTO", "Comorbilidades compensadas"
        ),
        "frag_p4_egreso_tratamiento": _fragment(
            "frag_p4_egreso_tratamiento",
            4,
            "6. TRATAMIENTO",
            "Se ha asegurado el tratamiento ambulatorio",
        ),
        "frag_p4_egreso_social": _fragment(
            "frag_p4_egreso_social", 4, "6. TRATAMIENTO", "Lo permiten las condiciones sociales"
        ),
        "frag_p4_t1_itu_baja": _fragment(
            "frag_p4_t1_itu_baja",
            4,
            "6. TRATAMIENTO",
            "ITU baja (complicada o no complicada)",
        ),
        "frag_p4_t1_itu_baja_antibioticos": _fragment(
            "frag_p4_t1_itu_baja_antibioticos",
            4,
            "6. TRATAMIENTO",
            "Nitrofurantoína o Cefalexina o Fosfomicina*",
        ),
        "frag_p4_t1_ba_row": _fragment(
            "frag_p4_t1_ba_row",
            4,
            "6. TRATAMIENTO",
            "Bacteriuria asintomática**",
        ),
        "frag_p4_t1_dosis_baja_ba": _fragment(
            "frag_p4_t1_dosis_baja_ba",
            4,
            "6. TRATAMIENTO",
            "100 mg VO cada 6 horas 500 mg VO cada 6 horas 3 g VO 5 días 5 días Dosis única",
        ),
        "frag_p4_t1_ambulatoria": _fragment(
            "frag_p4_t1_ambulatoria",
            4,
            "6. TRATAMIENTO",
            "ITU alta ambulatoria Cefalexina 1",
        ),
        "frag_p4_t1_ambulatoria_dosis": _fragment(
            "frag_p4_t1_ambulatoria_dosis",
            4,
            "6. TRATAMIENTO",
            "500 mg VO cada 6 horas 5-7 días",
        ),
        "frag_p4_t1_reevaluar": _fragment(
            "frag_p4_t1_reevaluar",
            4,
            "6. TRATAMIENTO",
            "1 Reevaluar con urocultivo a las 48 horas para ajuste",
        ),
        "frag_p4_t1_sin_fr": _fragment(
            "frag_p4_t1_sin_fr",
            4,
            "6. TRATAMIENTO",
            "ITU alta hospitalaria sin FR para BGN resistentes",
        ),
        "frag_p4_t1_sin_fr_drogas": _fragment(
            "frag_p4_t1_sin_fr_drogas",
            4,
            "6. TRATAMIENTO",
            "Cefazolina o Amikacina",
        ),
        "frag_p4_t1_sin_fr_dosis": _fragment(
            "frag_p4_t1_sin_fr_dosis",
            4,
            "6. TRATAMIENTO",
            "1 g IV cada 8 horas 15 mg/kg IV cada día 7 días 7 días",
        ),
        "frag_p4_t1_con_fr": _fragment(
            "frag_p4_t1_con_fr",
            4,
            "6. TRATAMIENTO",
            "ITU alta hospitalaria con FR para BGN resistentes***",
        ),
        "frag_p4_t1_con_fr_drogas": _fragment(
            "frag_p4_t1_con_fr_drogas",
            4,
            "6. TRATAMIENTO",
            "Piperacilina tazobactam o Amikacina2 o Meropenem3",
        ),
        "frag_p4_t1_con_fr_dosis": _fragment(
            "frag_p4_t1_con_fr_dosis",
            4,
            "6. TRATAMIENTO",
            "4.5 g IV cada 8 horas 15 mg/kg IV cada día 1 g IV cada 8 horas 7 días",
        ),
        "frag_p4_t1_nota_amikacina": _fragment(
            "frag_p4_t1_nota_amikacina",
            4,
            "6. TRATAMIENTO",
            "2 Evitar en choque",
        ),
        "frag_p4_t1_nota_meropenem": _fragment(
            "frag_p4_t1_nota_meropenem",
            4,
            "6. TRATAMIENTO",
            "3 Administrar empíricamente si hay choque",
        ),
        "frag_p4_t1_nota_fosfomicina": _fragment(
            "frag_p4_t1_nota_fosfomicina",
            4,
            "6. TRATAMIENTO",
            "*Preferir en pacientes quienes tienen ITU recurrente o han estado "
            "expuestas a terapia antimicrobiana en los últimos 90 días.",
        ),
        "frag_p4_t1_nota_ba": _fragment(
            "frag_p4_t1_nota_ba",
            4,
            "6. TRATAMIENTO",
            "**Recordar su tratamiento sólo en gestantes o pacientes quienes serán "
            "sometidos a procedimientos urológicos donde se prevé la disrupción "
            "del uroepitelio",
        ),
        "frag_p4_t1_nota_fr": _fragment(
            "frag_p4_t1_nota_fr",
            4,
            "6. TRATAMIENTO",
            "**FR BGN resistentes: hospitalización > 48 horas en los últimos 3 "
            "meses, uso de antibióticos en últimos 90 días, colonización por "
            "germen BLEE.",
        ),
        "frag_p4_t2_heading": _fragment(
            "frag_p4_t2_heading",
            4,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
        ),
        "frag_p4_t2_ba_row": _fragment(
            "frag_p4_t2_ba_row",
            4,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "Bacteriuria asintomática Nitrofurantoína  Cefalexina Fosfomicina3 "
            "100 mg cada 6 h 500 mg cada 6 h 3 g 5 días 5 días Dosis única No No",
        ),
        "frag_p4_t2_itu_baja_row": _fragment(
            "frag_p4_t2_itu_baja_row",
            4,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "ITU baja Nitrofurantoína o Cefalexina o Fosfomicina 3 100 mg cada "
            "6 h 500 mg cada 6 h 5 días 5 días Dosis única No Sólo si hay "
            "recurrencia de la infección",
        ),
        "frag_p4_t2_preventiva_baja": _fragment(
            "frag_p4_t2_preventiva_baja",
            4,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "Nitrofurantoína 100 mg cada día Cefalexina 500 mg cada día TMP-SMX "
            "480 mg cada día Hasta semana 34  gestación",
        ),
        "frag_p5_t2_itu_alta_row": _fragment(
            "frag_p5_t2_itu_alta_row",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "ITU alta Cefazolina* o Piperacilina tazobactam** o Meropenem*** "
            "1 g IV cada 8 horas 4.5 g IV cada 8 horas 1 g IV cada 8 horas "
            "7 días No Sí",
        ),
        "frag_p5_t2_preventiva_alta": _fragment(
            "frag_p5_t2_preventiva_alta",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "Nitrofurantoína 100 mg cada día Cefalexina 500 mg cada día TMP-SMX "
            "480 mg cada día Fosfomicina 3 g cada semana Hasta semana 34  "
            "gestación4",
        ),
        "frag_p5_t2_observacion_trimestre": _fragment(
            "frag_p5_t2_observacion_trimestre",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "Evitar en primer trimestre. Hasta semana 34 gestación4",
        ),
        "frag_p5_t2_nota1": _fragment(
            "frag_p5_t2_nota1",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "1Esta es la terapia empírica. Siempre debe ajustarse según resultados "
            "de urocultivo y antibiograma",
        ),
        "frag_p5_t2_nota2": _fragment(
            "frag_p5_t2_nota2",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "2La decisión se toma con base en los cultivos y pruebas de sensibilidad",
        ),
        "frag_p5_t2_nota3": _fragment(
            "frag_p5_t2_nota3",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "3 Preferir en pacientes quienes tienen ITU recurrente o han estado "
            "expuestas a terapia antimicrobiana en los últimos 90 días.",
        ),
        "frag_p5_t2_nota4": _fragment(
            "frag_p5_t2_nota4",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "4 A la semana 34 podría hacerse cambio a cefalexina o "
            "nitrofurantoína, si el microorganismo es sensible. Administrar "
            "hasta la finalización del embarazo.",
        ),
        "frag_p5_t2_sin_fr": _fragment(
            "frag_p5_t2_sin_fr",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "*Sin factores de riesgo para BGN resistentes",
        ),
        "frag_p5_t2_con_fr": _fragment(
            "frag_p5_t2_con_fr",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "**Con factores de riesgo para BGN resistentes, sin choque",
        ),
        "frag_p5_t2_con_fr_choque": _fragment(
            "frag_p5_t2_con_fr_choque",
            5,
            "Tabla 2. Consideraciones manejo de la ITU en la paciente gestante",
            "***Con factores de riesgo para BGN resistentes, con choque",
        ),
        "frag_p5_control_cambios_v06": _fragment(
            "frag_p5_control_cambios_v06",
            5,
            "CONTROL DE CAMBIOS",
            "06 30 – Septiembre- 2025 Se cambia nombre a protocolo Infección del "  # noqa: RUF001
            "Tracto Urinario Adultos. Se cambia definición de ITU complicada. Se "
            "actualizan recomendaciones de manejo según clasificación de ITU y "
            "factores de riesgo. Se dan consideraciones del manejo de la ITU en "
            "la gestante.",
        ),
    }


def _build_variables() -> dict[str, Variable]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED
    return {
        # --- Definitions (22) ---
        "bacteriuria_significativa": _variable(
            "bacteriuria_significativa",
            "Bacteriuria significativa (recuento significativo de colonias en orina)",
            VariableType.BOOLEAN,
            _prov(
                n,
                (
                    "frag_p1_def_ba",
                    "frag_p1_def_itu",
                    "frag_p1_def_itu_bajo",
                    "frag_p1_def_itu_alto",
                ),
                notes="La fuente usa 'recuento significativo de colonias bacterianas en "
                "muestras de orina' (definiciones de BA e ITU) y 'bacteriuria "
                "significativa' (definiciones de ITU bajo y alto) para el mismo criterio "
                "de laboratorio; concepto canónico normalizado sin umbral universal "
                "(los umbrales numéricos de la página 3 son específicos por contexto).",
            ),
            description="Criterio de laboratorio de la fuente; no es un umbral fijo de UFC.",
        ),
        "sin_signos_sintomas_itu": _variable(
            "sin_signos_sintomas_itu",
            "Sin signos o síntomas atribuibles a ITU",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_ba",)),
            description="Negativo directo de la fuente; complementario de "
            "signos_sintomas_itu (las pruebas nunca afirman ambos a la vez).",
        ),
        "mujer_no_embarazada": _variable(
            "mujer_no_embarazada",
            "Mujer no embarazada",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_ba_cultivos",)),
        ),
        "urocultivos_2_mismo_patron": _variable(
            "urocultivos_2_mismo_patron",
            "Dos urocultivos con el mismo patógeno y perfil de sensibilidad",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p1_def_ba_cultivos",),
                notes="Colapsa '2 urocultivos con el mismo patógeno y perfil de sensibilidad'.",
            ),
        ),
        "hombre": _variable(
            "hombre",
            "Hombre",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_ba_cultivos",)),
        ),
        "urocultivo_unico": _variable(
            "urocultivo_unico",
            "Un urocultivo",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p1_def_ba_cultivos",),
                notes="Colapsa '1 [urocultivo] en hombres y pacientes gestantes'.",
            ),
        ),
        "ausencia_piuria_sedimento": _variable(
            "ausencia_piuria_sedimento",
            "Ausencia de piuria en el sedimento",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_ba_piuria",)),
        ),
        "poblacion_pediatrica": _variable(
            "poblacion_pediatrica",
            "Población pediátrica",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_ba_piuria",)),
        ),
        "signos_sintomas_itu": _variable(
            "signos_sintomas_itu",
            "Signos o síntomas atribuibles a ITU",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu",)),
            description="Complementario de sin_signos_sintomas_itu.",
        ),
        "alteracion_estructural": _variable(
            "alteracion_estructural",
            "Alteración estructural de las vías urinarias",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_complicada_estructural",)),
        ),
        "alteracion_funcional": _variable(
            "alteracion_funcional",
            "Alteración funcional de las vías urinarias",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_complicada_estructural",)),
        ),
        "infeccion_aguda_vejiga_uretra": _variable(
            "infeccion_aguda_vejiga_uretra",
            "Infección aguda de la vejiga y/o la uretra",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p1_def_itu_bajo",),
                notes="Colapsa 'Infección aguda de la vejiga y/o la uretra'.",
            ),
        ),
        "sin_leucorrea": _variable(
            "sin_leucorrea",
            "Ausencia de leucorrea",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_bajo",)),
        ),
        "sin_irritacion_vaginal": _variable(
            "sin_irritacion_vaginal",
            "Ausencia de irritación vaginal",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_bajo",)),
        ),
        "sin_fiebre": _variable(
            "sin_fiebre",
            "Ausencia de fiebre",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_bajo",)),
        ),
        "sin_dolor_lumbar": _variable(
            "sin_dolor_lumbar",
            "Ausencia de dolor lumbar",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_bajo",)),
        ),
        "sin_compromiso_sistemico": _variable(
            "sin_compromiso_sistemico",
            "Ausencia de compromiso sistémico",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p1_def_itu_bajo",),
                notes="Fuente: 'compromiso sistémicos'.",
            ),
        ),
        "infeccion_aguda_rinon": _variable(
            "infeccion_aguda_rinon",
            "Infección aguda del riñón",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_alto",)),
        ),
        "pielonefritis": _variable(
            "pielonefritis",
            "Pielonefritis",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_alto", "frag_p1_def_itu_complicada_clinica")),
        ),
        "itu_febril_bacteriemica": _variable(
            "itu_febril_bacteriemica",
            "ITU febril o bacteriémica",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_complicada_clinica",)),
        ),
        "itu_asociada_cateter": _variable(
            "itu_asociada_cateter",
            "ITU asociada a catéter",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_complicada_clinica",)),
        ),
        "gestante": _variable(
            "gestante",
            "Mujer embarazada (gestante)",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_tto_ba_gestante", "frag_p2_embarazada_debe_tratarse")),
        ),
        # --- Diagnosis (15) ---
        "en_urgencias": _variable(
            "en_urgencias",
            "Paciente en el servicio de urgencias",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p2_citoquimico",)),
        ),
        "sospecha_itu": _variable(
            "sospecha_itu",
            "Sospecha de ITU",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p2_citoquimico",)),
            description="Sospecha clínica; distinta de infeccion_urinaria (condición establecida).",
        ),
        "primer_episodio": _variable(
            "primer_episodio",
            "Primer episodio",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p2_citoquimico",)),
        ),
        "sintomas_tipicos": _variable(
            "sintomas_tipicos",
            "Síntomas típicos",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p2_citoquimico",)),
        ),
        "mujer": _variable(
            "mujer",
            "Mujer",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p2_citoquimico",)),
        ),
        "tirilla_normal": _variable(
            "tirilla_normal",
            "Resultado normal de la tirilla de orina",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p2_tirilla_descarta",),
                notes="'un resultado normal' de la tirilla de orina.",
            ),
        ),
        "sospecha_clinica_baja": _variable(
            "sospecha_clinica_baja",
            "Baja sospecha clínica",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p2_tirilla_descarta",)),
        ),
        "leucocitos_orina_campo": _variable(
            "leucocitos_orina_campo",
            "Leucocitos en orina por campo",
            VariableType.NUMERIC,
            _prov(
                n,
                ("frag_p2_piuria",),
                notes="Umbral '>10 leucocitos'; unidad no declarada en la fuente.",
            ),
        ),
        "sonda_recien_insertada": _variable(
            "sonda_recien_insertada",
            "Muestra a través de sonda vesical recién insertada",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_urocultivo_positivo_1e2",)),
        ),
        "urocultivo_cfu_ml": _variable(
            "urocultivo_cfu_ml",
            "Recuento de UFC del urocultivo",
            VariableType.NUMERIC,
            _prov(
                n,
                (
                    "frag_p3_urocultivo_positivo_1e5",
                    "frag_p3_urocultivo_positivo_1e3",
                    "frag_p3_urocultivo_positivo_1e2",
                ),
                notes="Umbrales 10^5, 10^3 y 10^2 UFC por contexto de muestra; los "
                "superíndices presentan artefactos OCR en la evidencia ('10 5').",
            ),
            unit="UFC",
        ),
        "muestra_miccion_espontanea": _variable(
            "muestra_miccion_espontanea",
            "Muestra obtenida de forma adecuada por micción espontánea",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_urocultivo_positivo_1e5",)),
        ),
        "sintomas_no_explicados_otra_patologia": _variable(
            "sintomas_no_explicados_otra_patologia",
            "Síntomas no explicados por otra patología",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_urocultivo_positivo_1e3",)),
        ),
        "itu_baja_no_complicada": _variable(
            "itu_baja_no_complicada",
            "ITU baja no complicada",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_urocultivo_indicacion",)),
        ),
        "premenopausica": _variable(
            "premenopausica",
            "Mujer premenopáusica",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_urocultivo_indicacion",)),
        ),
        "infeccion_urinaria": _variable(
            "infeccion_urinaria",
            "Infección urinaria (ITU) establecida",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p3_analisis_sangre", "frag_p3_imagen_urgente"),
                notes="La fuente usa 'ITU' (análisis de sangre) e 'infección urinaria' "
                "(estudios imaginológicos) para la misma condición establecida del "
                "paciente.",
            ),
            description="Entrada clínica externa; distinta de sospecha_itu.",
        ),
        # --- Treatment / population (27) ---
        "itu_alta": _variable(
            "itu_alta",
            "ITU alta",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_alto", "frag_p3_hosp_itu_alta")),
        ),
        "itu_baja": _variable(
            "itu_baja",
            "ITU baja",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p1_def_itu_bajo", "frag_p4_t1_itu_baja")),
        ),
        "procedimiento_invasivo_vias_urinarias": _variable(
            "procedimiento_invasivo_vias_urinarias",
            "Procedimiento invasivo de vías urinarias con riesgo de sangrado o "
            "disrupción del uroepitelio",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p3_tto_ba_procedimiento", "frag_p4_t1_nota_ba"),
                notes="Colapsa 'Procedimiento invasivo de vías urinarias con riesgo de "
                "sangrado o disrupción del uroepitelio' (p3) y 'procedimientos "
                "urológicos donde se prevé la disrupción del uroepitelio' (p4); ambas "
                "son formulaciones de la fuente.",
            ),
        ),
        "choque_septico": _variable(
            "choque_septico",
            "Choque séptico",
            VariableType.BOOLEAN,
            _prov(
                s,
                (
                    "frag_p3_hosp_choque_septico",
                    "frag_p3_hemocultivos",
                    "frag_p3_imagen_urgente",
                ),
            ),
        ),
        "intolerancia_via_oral": _variable(
            "intolerancia_via_oral",
            "Intolerancia a la vía oral",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_hosp_intolerancia",)),
        ),
        "descompensacion_enfermedad_base": _variable(
            "descompensacion_enfermedad_base",
            "Descompensación de la enfermedad de base secundaria a la ITU",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_hosp_descompensacion",)),
        ),
        "germen_resistente_sin_opcion_ambulatoria": _variable(
            "germen_resistente_sin_opcion_ambulatoria",
            "Demostración de germen resistente sin opción de tratamiento antibiótico ambulatorio",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p3_hosp_resistente",),
                notes="Colapsa el bullet completo de la fuente.",
            ),
        ),
        "deterioro_funcion_renal": _variable(
            "deterioro_funcion_renal",
            "Deterioro de la función renal asociado a la ITU",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_hosp_funcion_renal",)),
        ),
        "absceso_renal_pararrenal": _variable(
            "absceso_renal_pararrenal",
            "Absceso renal/pararrenal",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_hosp_absceso",)),
        ),
        "soporte_social_inadecuado": _variable(
            "soporte_social_inadecuado",
            "Inadecuado soporte social para continuidad de terapia ambulatoria",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p3_hosp_social",),
                notes="Colapsa el bullet completo de la fuente.",
            ),
        ),
        "hospitalizado": _variable(
            "hospitalizado",
            "Paciente hospitalizado",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_analisis_sangre",)),
            description="Paciente hospitalizado al momento de la evaluación.",
        ),
        "hospitalizacion_48h_ultimos_3meses": _variable(
            "hospitalizacion_48h_ultimos_3meses",
            "Hospitalización > 48 horas en los últimos 3 meses",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_t1_nota_fr",)),
            description="Entrada clínica/histórica externa; el motor no computa la "
            "ventana temporal.",
        ),
        "antibioticos_ultimos_90dias": _variable(
            "antibioticos_ultimos_90dias",
            "Uso de antibióticos en los últimos 90 días",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_t1_nota_fr",)),
            description="Entrada histórica externa; el motor no computa la ventana.",
        ),
        "colonizacion_blee": _variable(
            "colonizacion_blee",
            "Colonización por germen BLEE",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_t1_nota_fr",)),
        ),
        "itu_recurrente": _variable(
            "itu_recurrente",
            "ITU recurrente",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_t1_nota_fosfomicina", "frag_p5_t2_nota3")),
            description="Entrada histórica externa; el motor no computa la recurrencia.",
        ),
        "fiebre": _variable(
            "fiebre",
            "Fiebre",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_hemocultivos",)),
        ),
        "hipotermia": _variable(
            "hipotermia",
            "Hipotermia",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_hemocultivos",)),
        ),
        "falla_renal_aguda": _variable(
            "falla_renal_aguda",
            "Falla renal aguda",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_imagen_urgente",)),
        ),
        "complicacion_local": _variable(
            "complicacion_local",
            "Clínica de complicación local",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_imagen_urgente",)),
        ),
        "tratamiento_antibiotico_correcto": _variable(
            "tratamiento_antibiotico_correcto",
            "Tratamiento antibiótico correcto",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_imagen_urgente",)),
        ),
        "sospecha_alteracion": _variable(
            "sospecha_alteracion",
            "Tipo de alteración sospechada para imagen",
            VariableType.CATEGORICAL,
            _prov(
                n,
                ("frag_p3_imagen_urotomografia", "frag_p3_imagen_ecografia"),
                notes="Colapsa las dos ramas 'la elección será' (estructural → "
                "urotomografía; funcional → ecografía).",
            ),
            allowed_values=("estructural", "funcional"),
        ),
        "hematuria": _variable(
            "hematuria",
            "Hematuria",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_imagen_gestante",)),
        ),
        "dolor": _variable(
            "dolor",
            "Dolor",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_imagen_gestante",)),
        ),
        "mas_de_un_episodio_itu": _variable(
            "mas_de_un_episodio_itu",
            "Más de un episodio de ITU durante el embarazo",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p3_imagen_gestante",),
                notes="Colapsa 'más de un episodio de ITU durante el embarazo'.",
            ),
            description="Entrada histórica externa; el motor no cuenta episodios.",
        ),
        "recurrencia_itu": _variable(
            "recurrencia_itu",
            "Recurrencia de la infección",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_t2_itu_baja_row",)),
            description="Entrada histórica externa; el motor no computa la recurrencia.",
        ),
        "sospecha_absceso_nefritis_local": _variable(
            "sospecha_absceso_nefritis_local",
            "Búsqueda de pequeños abscesos y áreas de nefritis local",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p3_imagen_tc_abscesos",),
                notes="'cuando se busquen pequeños abscesos y áreas de nefritis local'.",
            ),
        ),
        "sospecha_litiasis": _variable(
            "sospecha_litiasis",
            "Sospecha de litiasis",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p3_imagen_gestante",)),
            description="Entrada clínica externa; no derivada de hematuria/dolor.",
        ),
        # --- Discharge (10) ---
        "afebril_horas": _variable(
            "afebril_horas",
            "Horas afebril",
            VariableType.DURATION,
            _prov(
                n,
                ("frag_p3_egreso_afebril",),
                notes="Duración del estado afebril en horas; umbral '48 horas afebril'.",
            ),
            unit="hours",
        ),
        "tas": _variable(
            "tas",
            "Presión arterial sistólica",
            VariableType.NUMERIC,
            _prov(
                n,
                ("frag_p3_egreso_tas",),
                notes="'TAS' = presión arterial sistólica; umbral '> 90 mmHg'.",
            ),
            unit="mmHg",
        ),
        "fc": _variable(
            "fc",
            "Frecuencia cardiaca",
            VariableType.NUMERIC,
            _prov(s, ("frag_p4_egreso_fc",)),
            unit="lpm",
        ),
        "fr": _variable(
            "fr",
            "Frecuencia respiratoria",
            VariableType.NUMERIC,
            _prov(s, ("frag_p4_egreso_fr",)),
            unit="rpm",
        ),
        "sato2": _variable(
            "sato2",
            "Saturación de oxígeno",
            VariableType.NUMERIC,
            _prov(n, ("frag_p4_egreso_sato2_pao2",), notes="'Sat O2'; umbral '> 90%'."),
            unit="%",
        ),
        "pao2": _variable(
            "pao2",
            "PaO2",
            VariableType.NUMERIC,
            _prov(
                n,
                ("frag_p4_egreso_sato2_pao2",),
                notes="Umbral '> 60'; unidad no declarada en la fuente.",
            ),
        ),
        "tolera_via_oral": _variable(
            "tolera_via_oral",
            "Tolerancia a la vía oral",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_egreso_via_oral",)),
        ),
        "comorbilidades_compensadas": _variable(
            "comorbilidades_compensadas",
            "Comorbilidades compensadas",
            VariableType.BOOLEAN,
            _prov(s, ("frag_p4_egreso_comorbilidades",)),
        ),
        "tratamiento_ambulatorio_asegurado": _variable(
            "tratamiento_ambulatorio_asegurado",
            "Se ha asegurado el tratamiento ambulatorio",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p4_egreso_tratamiento",),
                notes="Colapsa 'Se ha asegurado el tratamiento ambulatorio'.",
            ),
        ),
        "condiciones_sociales_permiten": _variable(
            "condiciones_sociales_permiten",
            "Lo permiten las condiciones sociales",
            VariableType.BOOLEAN,
            _prov(
                n,
                ("frag_p4_egreso_social",),
                notes="Colapsa 'Lo permiten las condiciones sociales'.",
            ),
        ),
        # --- Temporal (2) ---
        "fiebre_horas": _variable(
            "fiebre_horas",
            "Horas de fiebre persistente",
            VariableType.DURATION,
            _prov(
                n,
                ("frag_p3_imagen_urgente",),
                notes="Duración de fiebre persistente en horas; acoplada en la fuente a "
                "'tratamiento antibiótico correcto'.",
            ),
            unit="hours",
        ),
        "tiempo_desde_inicio_terapia_hours": _variable(
            "tiempo_desde_inicio_terapia_hours",
            "Horas desde el inicio de la terapia",
            VariableType.DURATION,
            _prov(
                n,
                ("frag_p4_t1_reevaluar",),
                notes="Tiempo desde el inicio de la terapia para la reevaluación a las 48 horas.",
            ),
            unit="hours",
        ),
    }


def _build_actions() -> dict[str, Action]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED
    prescribe_note = (
        "Alternativa declarada en la fuente; el payload compone celdas de la tabla y "
        "el motor nunca ejecuta ni selecciona entre alternativas."
    )
    return {
        # --- CLASSIFY (5) ---
        "act_classify_itu_alto": _action(
            "act_classify_itu_alto",
            ActionType.CLASSIFY,
            _prov(s, ("frag_p1_def_itu_alto", "frag_p2_clasificacion_alta_baja")),
            payload={"clasificacion": "ITU_alta"},
        ),
        "act_classify_itu_bajo": _action(
            "act_classify_itu_bajo",
            ActionType.CLASSIFY,
            _prov(s, ("frag_p1_def_itu_bajo", "frag_p2_clasificacion_alta_baja")),
            payload={"clasificacion": "ITU_baja"},
        ),
        "act_classify_urocultivo_positivo_1e5": _action(
            "act_classify_urocultivo_positivo_1e5",
            ActionType.CLASSIFY,
            _prov(
                n,
                ("frag_p3_urocultivo_positivo_1e5",),
                notes="Umbral '≥10 5 UFC' con artefacto OCR preservado en la evidencia.",
            ),
            payload={"umbral": ">= 10^5 UFC micción espontánea"},
        ),
        "act_classify_urocultivo_positivo_1e3": _action(
            "act_classify_urocultivo_positivo_1e3",
            ActionType.CLASSIFY,
            _prov(
                n,
                ("frag_p3_urocultivo_positivo_1e3",),
                notes="Umbral '≥10 3 UFC' con síntomas no explicados por otra patología.",
            ),
            payload={"umbral": ">= 10^3 UFC síntomas no explicados"},
        ),
        "act_classify_urocultivo_positivo_1e2": _action(
            "act_classify_urocultivo_positivo_1e2",
            ActionType.CLASSIFY,
            _prov(
                n,
                ("frag_p3_urocultivo_positivo_1e2",),
                notes="Umbral '≥10 2 UFC' en sonda vesical recién insertada.",
            ),
            payload={"umbral": ">= 10^2 UFC sonda recién insertada"},
        ),
        # --- DECISION (2) ---
        "act_descarta_diagnostico_itu": _action(
            "act_descarta_diagnostico_itu",
            ActionType.DECISION,
            _prov(s, ("frag_p2_tirilla_descarta",)),
            label="Descarta el diagnóstico de ITU",
        ),
        "act_tratar_bacteriuria_asintomatica": _action(
            "act_tratar_bacteriuria_asintomatica",
            ActionType.DECISION,
            _prov(
                n,
                (
                    "frag_p3_tto_ba_indicaciones",
                    "frag_p3_tto_ba_gestante",
                    "frag_p3_tto_ba_procedimiento",
                ),
                notes="Indicación de tratamiento de bacteriuria asintomática según las "
                "dos indicaciones de la fuente.",
            ),
            label="Indicación de tratamiento de bacteriuria asintomática",
        ),
        # --- REQUEST_TEST (14) ---
        "act_citoquimico": _action(
            "act_citoquimico", ActionType.REQUEST_TEST, _prov(s, ("frag_p2_citoquimico",))
        ),
        "act_gram_orina": _action(
            "act_gram_orina", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_gram",))
        ),
        "act_urocultivo": _action(
            "act_urocultivo", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_urocultivo_indicacion",))
        ),
        "act_urocultivo_control": _action(
            "act_urocultivo_control",
            ActionType.REQUEST_TEST,
            _prov(
                n,
                ("frag_p4_t1_reevaluar",),
                notes="Urocultivo de reevaluación a las 48 horas; intervalo declarativo "
                "del payload.",
            ),
            payload={"intervalo_horas": 48},
        ),
        "act_hemoleucograma": _action(
            "act_hemoleucograma", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_analisis_sangre",))
        ),
        "act_ionograma": _action(
            "act_ionograma", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_analisis_sangre",))
        ),
        "act_funcion_renal": _action(
            "act_funcion_renal", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_analisis_sangre",))
        ),
        "act_pcr": _action(
            "act_pcr", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_analisis_sangre",))
        ),
        "act_hemocultivos": _action(
            "act_hemocultivos", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_hemocultivos",))
        ),
        "act_imagen_urgente_eco_tc": _action(
            "act_imagen_urgente_eco_tc",
            ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_imagen_urgente",)),
        ),
        "act_tc_contraste": _action(
            "act_tc_contraste", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_imagen_tc_abscesos",))
        ),
        "act_urotomografia": _action(
            "act_urotomografia",
            ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_imagen_urotomografia",)),
        ),
        "act_ecografia_vias_urinarias": _action(
            "act_ecografia_vias_urinarias",
            ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_imagen_ecografia",)),
        ),
        "act_ecografia_renal": _action(
            "act_ecografia_renal", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_imagen_gestante",))
        ),
        # --- ADMIT (1) ---
        "act_hospitalizar": _action(
            "act_hospitalizar",
            ActionType.ADMIT,
            _prov(
                n,
                (
                    "frag_p3_hosp_choque_septico",
                    "frag_p3_hosp_intolerancia",
                    "frag_p3_hosp_itu_alta",
                    "frag_p3_hosp_descompensacion",
                    "frag_p3_hosp_resistente",
                    "frag_p3_hosp_funcion_renal",
                    "frag_p3_hosp_absceso",
                    "frag_p3_hosp_social",
                ),
                notes="Consecuencia de las 8 indicaciones de hospitalización aplicables "
                "a adultos; el bullet pediátrico queda fuera del alcance.",
            ),
        ),
        # --- DISCHARGE (1) ---
        "act_egreso": _action(
            "act_egreso",
            ActionType.DISCHARGE,
            _prov(
                n,
                (
                    "frag_p3_egreso_afebril",
                    "frag_p3_egreso_tas",
                    "frag_p4_egreso_fc",
                    "frag_p4_egreso_fr",
                    "frag_p4_egreso_sato2_pao2",
                    "frag_p4_egreso_via_oral",
                    "frag_p4_egreso_comorbilidades",
                    "frag_p4_egreso_tratamiento",
                    "frag_p4_egreso_social",
                ),
                notes="Paso a terapia oral y/o egreso cuando se cumplen los criterios "
                "de la fuente.",
            ),
        ),
        # --- PRESCRIBE (21) ---
        "act_t1_nitrofurantoina": _action(
            "act_t1_nitrofurantoina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t1_itu_baja_antibioticos", "frag_p4_t1_dosis_baja_ba"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Nitrofurantoína",
                "dosis": "100 mg",
                "via": "VO",
                "frecuencia": "cada 6 horas",
                "duracion": "5 días",
            },
        ),
        "act_t1_cefalexina": _action(
            "act_t1_cefalexina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t1_itu_baja_antibioticos", "frag_p4_t1_dosis_baja_ba"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Cefalexina",
                "dosis": "500 mg",
                "via": "VO",
                "frecuencia": "cada 6 horas",
                "duracion": "5 días",
            },
        ),
        "act_t1_fosfomicina": _action(
            "act_t1_fosfomicina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t1_itu_baja_antibioticos", "frag_p4_t1_dosis_baja_ba"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Fosfomicina",
                "dosis": "3 g",
                "via": "VO",
                "duracion": "Dosis única",
            },
        ),
        "act_t1_ba_nitrofurantoina": _action(
            "act_t1_ba_nitrofurantoina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                (
                    "frag_p4_t1_ba_row",
                    "frag_p4_t1_itu_baja_antibioticos",
                    "frag_p4_t1_dosis_baja_ba",
                ),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Nitrofurantoína",
                "dosis": "100 mg",
                "via": "VO",
                "frecuencia": "cada 6 horas",
                "duracion": "5 días",
            },
        ),
        "act_t1_ba_cefalexina": _action(
            "act_t1_ba_cefalexina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                (
                    "frag_p4_t1_ba_row",
                    "frag_p4_t1_itu_baja_antibioticos",
                    "frag_p4_t1_dosis_baja_ba",
                ),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Cefalexina",
                "dosis": "500 mg",
                "via": "VO",
                "frecuencia": "cada 6 horas",
                "duracion": "5 días",
            },
        ),
        "act_t1_ba_fosfomicina": _action(
            "act_t1_ba_fosfomicina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                (
                    "frag_p4_t1_ba_row",
                    "frag_p4_t1_itu_baja_antibioticos",
                    "frag_p4_t1_dosis_baja_ba",
                ),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Fosfomicina",
                "dosis": "3 g",
                "via": "VO",
                "duracion": "Dosis única",
            },
        ),
        "act_cefalexina_alta_amb": _action(
            "act_cefalexina_alta_amb",
            ActionType.PRESCRIBE,
            _prov(
                n, ("frag_p4_t1_ambulatoria", "frag_p4_t1_ambulatoria_dosis"), notes=prescribe_note
            ),
            payload={
                "medicamento": "Cefalexina",
                "dosis": "500 mg",
                "via": "VO",
                "frecuencia": "cada 6 horas",
                "duracion": "5-7 días",
            },
        ),
        "act_cefazolina": _action(
            "act_cefazolina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t1_sin_fr_drogas", "frag_p4_t1_sin_fr_dosis", "frag_p5_t2_itu_alta_row"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Cefazolina",
                "dosis": "1 g",
                "via": "IV",
                "frecuencia": "cada 8 horas",
                "duracion": "7 días",
            },
        ),
        "act_amikacina": _action(
            "act_amikacina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t1_sin_fr_dosis", "frag_p4_t1_con_fr_dosis", "frag_p4_t1_nota_amikacina"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Amikacina",
                "dosis": "15 mg/kg",
                "via": "IV",
                "frecuencia": "cada día",
                "duracion": "7 días",
            },
        ),
        "act_piperacilina_tazobactam": _action(
            "act_piperacilina_tazobactam",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t1_con_fr_drogas", "frag_p4_t1_con_fr_dosis", "frag_p5_t2_itu_alta_row"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Piperacilina tazobactam",
                "dosis": "4.5 g",
                "via": "IV",
                "frecuencia": "cada 8 horas",
                "duracion": "7 días",
            },
        ),
        "act_meropenem": _action(
            "act_meropenem",
            ActionType.PRESCRIBE,
            _prov(
                n,
                (
                    "frag_p4_t1_con_fr_drogas",
                    "frag_p4_t1_con_fr_dosis",
                    "frag_p4_t1_nota_meropenem",
                    "frag_p5_t2_itu_alta_row",
                ),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Meropenem",
                "dosis": "1 g",
                "via": "IV",
                "frecuencia": "cada 8 horas",
                "duracion": "7 días",
            },
        ),
        "act_t2_ba_nitrofurantoina": _action(
            "act_t2_ba_nitrofurantoina",
            ActionType.PRESCRIBE,
            _prov(n, ("frag_p4_t2_ba_row",), notes=prescribe_note),
            payload={
                "medicamento": "Nitrofurantoína",
                "dosis": "100 mg",
                "frecuencia": "cada 6 h",
                "duracion": "5 días",
            },
        ),
        "act_t2_ba_cefalexina": _action(
            "act_t2_ba_cefalexina",
            ActionType.PRESCRIBE,
            _prov(n, ("frag_p4_t2_ba_row",), notes=prescribe_note),
            payload={
                "medicamento": "Cefalexina",
                "dosis": "500 mg",
                "frecuencia": "cada 6 h",
                "duracion": "5 días",
            },
        ),
        "act_t2_ba_fosfomicina": _action(
            "act_t2_ba_fosfomicina",
            ActionType.PRESCRIBE,
            _prov(n, ("frag_p4_t2_ba_row",), notes=prescribe_note),
            payload={"medicamento": "Fosfomicina", "dosis": "3 g", "duracion": "Dosis única"},
        ),
        "act_t2_baja_nitrofurantoina": _action(
            "act_t2_baja_nitrofurantoina",
            ActionType.PRESCRIBE,
            _prov(n, ("frag_p4_t2_itu_baja_row",), notes=prescribe_note),
            payload={
                "medicamento": "Nitrofurantoína",
                "dosis": "100 mg",
                "frecuencia": "cada 6 h",
                "duracion": "5 días",
            },
        ),
        "act_t2_baja_cefalexina": _action(
            "act_t2_baja_cefalexina",
            ActionType.PRESCRIBE,
            _prov(n, ("frag_p4_t2_itu_baja_row",), notes=prescribe_note),
            payload={
                "medicamento": "Cefalexina",
                "dosis": "500 mg",
                "frecuencia": "cada 6 h",
                "duracion": "5 días",
            },
        ),
        "act_t2_baja_fosfomicina": _action(
            "act_t2_baja_fosfomicina",
            ActionType.PRESCRIBE,
            _prov(n, ("frag_p4_t2_itu_baja_row",), notes=prescribe_note),
            payload={"medicamento": "Fosfomicina", "dosis": "3 g", "duracion": "Dosis única"},
        ),
        "act_preventiva_nitrofurantoina": _action(
            "act_preventiva_nitrofurantoina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t2_preventiva_baja", "frag_p5_t2_preventiva_alta", "frag_p5_t2_nota4"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Nitrofurantoína",
                "dosis": "100 mg",
                "frecuencia": "cada día",
                "duracion": "hasta semana 34 gestación",
            },
        ),
        "act_preventiva_cefalexina": _action(
            "act_preventiva_cefalexina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t2_preventiva_baja", "frag_p5_t2_preventiva_alta", "frag_p5_t2_nota4"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Cefalexina",
                "dosis": "500 mg",
                "frecuencia": "cada día",
                "duracion": "hasta semana 34 gestación",
            },
        ),
        "act_preventiva_tmpsmx": _action(
            "act_preventiva_tmpsmx",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t2_preventiva_baja", "frag_p5_t2_preventiva_alta", "frag_p5_t2_nota4"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "TMP-SMX",
                "dosis": "480 mg",
                "frecuencia": "cada día",
                "duracion": "hasta semana 34 gestación",
            },
        ),
        "act_preventiva_fosfomicina": _action(
            "act_preventiva_fosfomicina",
            ActionType.PRESCRIBE,
            _prov(
                n,
                ("frag_p4_t2_preventiva_baja", "frag_p5_t2_preventiva_alta", "frag_p5_t2_nota4"),
                notes=prescribe_note,
            ),
            payload={
                "medicamento": "Fosfomicina",
                "dosis": "3 g",
                "frecuencia": "cada semana",
                "duracion": "hasta semana 34 gestación",
            },
        ),
        # --- RESTRICTION (1) ---
        "act_restriccion_muestra_previa": _action(
            "act_restriccion_muestra_previa",
            ActionType.RESTRICTION,
            _prov(s, ("frag_p3_toma_muestra_antibiotico",)),
            label="Tomar la muestra antes de la primera dosis de antibiótico",
        ),
    }


def _build_expressions() -> dict[str, Any]:
    hospitalization = _or(
        _flag("choque_septico"),
        _flag("intolerancia_via_oral"),
        _flag("itu_alta"),
        _flag("descompensacion_enfermedad_base"),
        _flag("germen_resistente_sin_opcion_ambulatoria"),
        _flag("deterioro_funcion_renal"),
        _flag("absceso_renal_pararrenal"),
        _flag("soporte_social_inadecuado"),
    )

    fr_bgn = _or(
        _flag("hospitalizacion_48h_ultimos_3meses"),
        _flag("antibioticos_ultimos_90dias"),
        _flag("colonizacion_blee"),
    )

    egreso = _and(
        _temporal("afebril_horas", 48, "hours"),
        _gt("tas", 90),
        _lt("fc", 100),
        _lt("fr", 24),
        _or(_gt("sato2", 90), _gt("pao2", 60)),
        _flag("tolera_via_oral"),
        _flag("comorbilidades_compensadas"),
        _flag("tratamiento_ambulatorio_asegurado"),
        _flag("condiciones_sociales_permiten"),
    )

    return {
        "hospitalization": hospitalization,
        "fr_bgn": fr_bgn,
        "egreso": egreso,
    }


def _build_rules(expressions: dict[str, Any]) -> dict[str, Rule]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED
    hospitalization = expressions["hospitalization"]
    fr_bgn = expressions["fr_bgn"]
    egreso = expressions["egreso"]

    return {
        # --- Definitions (8) ---
        "rule_def_ba": _rule(
            "rule_def_ba",
            _and(_flag("bacteriuria_significativa"), _flag("sin_signos_sintomas_itu")),
            _prov(
                n,
                ("frag_p1_def_ba",),
                notes="Componente 1 de la definición de BA: bacteriuria significativa "
                "sin signos ni síntomas atribuibles a ITU; ver rule_def_ba_cultivos y "
                "rule_def_ba_piuria_pediatrica.",
            ),
        ),
        "rule_def_ba_cultivos": _rule(
            "rule_def_ba_cultivos",
            _or(
                _and(_flag("mujer_no_embarazada"), _flag("urocultivos_2_mismo_patron")),
                _and(_flag("hombre"), _flag("urocultivo_unico")),
                _and(_flag("gestante"), _flag("urocultivo_unico")),
            ),
            _prov(
                n,
                ("frag_p1_def_ba_cultivos",),
                notes="Componente 2 de la definición de BA: requisito microbiológico "
                "por población de la misma oración fuente.",
            ),
        ),
        "rule_def_ba_piuria_pediatrica": _rule(
            "rule_def_ba_piuria_pediatrica",
            _and(_flag("poblacion_pediatrica"), _flag("ausencia_piuria_sedimento")),
            _prov(
                n,
                ("frag_p1_def_ba_piuria",),
                notes="Componente 3 de la definición de BA: cláusula pediátrica "
                "conservada como evidencia fuera del alcance adulto del protocolo; no "
                "es un requisito del BA adulto.",
            ),
        ),
        "rule_def_itu": _rule(
            "rule_def_itu",
            _and(_flag("bacteriuria_significativa"), _flag("signos_sintomas_itu")),
            _prov(
                n,
                ("frag_p1_def_itu",),
                notes="Definición de ITU ensamblada desde la frase de DEFINICIONES.",
            ),
        ),
        "rule_def_itu_complicada_estructural": _rule(
            "rule_def_itu_complicada_estructural",
            _or(_flag("alteracion_estructural"), _flag("alteracion_funcional")),
            _prov(s, ("frag_p1_def_itu_complicada_estructural",)),
        ),
        "rule_def_itu_bajo": _rule(
            "rule_def_itu_bajo",
            _and(
                _flag("infeccion_aguda_vejiga_uretra"),
                _flag("bacteriuria_significativa"),
                _flag("sin_leucorrea"),
                _flag("sin_irritacion_vaginal"),
                _flag("sin_fiebre"),
                _flag("sin_dolor_lumbar"),
                _flag("sin_compromiso_sistemico"),
            ),
            _prov(
                n,
                ("frag_p1_def_itu_bajo", "frag_p2_clasificacion_alta_baja"),
                notes="Definición de ITU bajo ensamblada; la clasificación alta/baja "
                "es necesaria para definir tratamiento y pronóstico.",
            ),
            action_refs=("act_classify_itu_bajo",),
        ),
        "rule_def_itu_alto": _rule(
            "rule_def_itu_alto",
            _and(_flag("infeccion_aguda_rinon"), _flag("bacteriuria_significativa")),
            _prov(s, ("frag_p1_def_itu_alto", "frag_p2_clasificacion_alta_baja")),
            action_refs=("act_classify_itu_alto",),
        ),
        "rule_def_itu_complicada_clinica": _rule(
            "rule_def_itu_complicada_clinica",
            _or(
                _flag("pielonefritis"),
                _flag("itu_febril_bacteriemica"),
                _flag("itu_asociada_cateter"),
            ),
            _prov(
                n,
                ("frag_p1_def_itu_complicada_clinica",),
                notes="Definición de ITU complicada con compromiso más allá de la "
                "vejiga; prostatitis excluida de la condición porque la fuente declara "
                "que excede los alcances del protocolo (vi_prostatitis_fuera_alcance).",
            ),
        ),
        # --- Diagnosis (11) ---
        "rule_citoquimico_orina": _rule(
            "rule_citoquimico_orina",
            _flag("sospecha_itu"),
            _prov(
                n,
                ("frag_p2_citoquimico",),
                notes="Citoquímico de orina ante sospecha de ITU en urgencias; "
                "excepción: mujeres con primer episodio y síntomas típicos.",
            ),
            applies_to=_flag("en_urgencias"),
            exceptions=(_and(_flag("mujer"), _flag("primer_episodio"), _flag("sintomas_tipicos")),),
            action_refs=("act_citoquimico",),
        ),
        "rule_tirilla_descarta_diagnostico": _rule(
            "rule_tirilla_descarta_diagnostico",
            _and(_flag("tirilla_normal"), _flag("sospecha_clinica_baja")),
            _prov(
                n,
                ("frag_p2_tirilla_descarta",),
                notes="Resultado normal de la tirilla con baja sospecha clínica "
                "descarta el diagnóstico.",
            ),
            action_refs=("act_descarta_diagnostico_itu",),
        ),
        "rule_piuria_mayor_10": _rule(
            "rule_piuria_mayor_10",
            _gt("leucocitos_orina_campo", 10),
            _prov(
                n,
                ("frag_p2_piuria",),
                notes="Criterio de piuria '>10 leucocitos'; correlación descriptiva de la fuente.",
            ),
        ),
        "rule_gram_urgencias": _rule(
            "rule_gram_urgencias",
            _flag("en_urgencias"),
            _prov(s, ("frag_p3_gram",)),
            action_refs=("act_gram_orina",),
        ),
        "rule_urocultivo_indicado": _rule(
            "rule_urocultivo_indicado",
            _flag("sospecha_itu"),
            _prov(
                n,
                ("frag_p3_urocultivo_indicacion", "frag_p3_toma_muestra_antibiotico"),
                notes="Excepción: primer episodio de ITU baja no complicada en mujer "
                "premenopáusica. La restricción de tomar la muestra antes de la primera "
                "dosis de antibiótico es una instrucción de procedimiento adherida a la "
                "indicación del urocultivo; la fuente no le da condición propia.",
            ),
            exceptions=(
                _and(
                    _flag("mujer"),
                    _flag("primer_episodio"),
                    _flag("itu_baja_no_complicada"),
                    _flag("premenopausica"),
                ),
            ),
            action_refs=("act_urocultivo", "act_restriccion_muestra_previa"),
        ),
        "rule_urocultivo_positivo_1e5": _rule(
            "rule_urocultivo_positivo_1e5",
            _and(_ge("urocultivo_cfu_ml", 100000), _flag("muestra_miccion_espontanea")),
            _prov(
                n,
                ("frag_p3_urocultivo_positivo_1e5",),
                notes="Umbral '≥10 5 UFC' en muestra por micción espontánea; artefacto "
                "OCR preservado en la evidencia.",
            ),
            action_refs=("act_classify_urocultivo_positivo_1e5",),
        ),
        "rule_urocultivo_positivo_1e3": _rule(
            "rule_urocultivo_positivo_1e3",
            _and(
                _ge("urocultivo_cfu_ml", 1000),
                _flag("sintomas_no_explicados_otra_patologia"),
            ),
            _prov(
                n,
                ("frag_p3_urocultivo_positivo_1e3",),
                notes="Umbral '≥10 3 UFC' en paciente con síntomas no explicados por "
                "otra patología.",
            ),
            action_refs=("act_classify_urocultivo_positivo_1e3",),
        ),
        "rule_urocultivo_positivo_1e2": _rule(
            "rule_urocultivo_positivo_1e2",
            _and(_ge("urocultivo_cfu_ml", 100), _flag("sonda_recien_insertada")),
            _prov(
                n,
                ("frag_p3_urocultivo_positivo_1e2",),
                notes="Umbral '≥10 2 UFC' en muestra por sonda vesical recién insertada.",
            ),
            action_refs=("act_classify_urocultivo_positivo_1e2",),
        ),
        "rule_analisis_sangre": _rule(
            "rule_analisis_sangre",
            _flag("infeccion_urinaria"),
            _prov(
                n,
                ("frag_p3_analisis_sangre",),
                notes="Muestra de sangre en todo paciente con ITU que sea "
                "hospitalizado; la condición de hospitalización es la composición de "
                "los criterios de la fuente.",
            ),
            applies_to=hospitalization,
            action_refs=("act_hemoleucograma", "act_ionograma", "act_funcion_renal", "act_pcr"),
        ),
        "rule_hemocultivos": _rule(
            "rule_hemocultivos",
            _or(_flag("fiebre"), _flag("hipotermia"), _flag("choque_septico")),
            _prov(
                n,
                ("frag_p3_hemocultivos",),
                notes="Hemocultivos en pielonefritis aguda que cursa con fiebre, "
                "hipotermia o choque séptico.",
            ),
            applies_to=_flag("pielonefritis"),
            action_refs=("act_hemocultivos",),
        ),
        "rule_fr_bgn_resistentes": _rule(
            "rule_fr_bgn_resistentes",
            fr_bgn,
            _prov(
                n,
                ("frag_p4_t1_nota_fr",),
                notes="Composición OR de los tres factores de riesgo para BGN "
                "resistentes declarados por la fuente; expresión compartida por las "
                "reglas de selección de tratamiento.",
            ),
        ),
        # --- Imaging (5) ---
        "rule_imagen_urgente": _rule(
            "rule_imagen_urgente",
            _and(
                _flag("infeccion_urinaria"),
                _or(
                    _flag("choque_septico"),
                    _flag("falla_renal_aguda"),
                    _flag("complicacion_local"),
                    _and(
                        _temporal("fiebre_horas", 72, "hours"),
                        _flag("tratamiento_antibiotico_correcto"),
                    ),
                ),
            ),
            _prov(
                n,
                ("frag_p3_imagen_urgente",),
                notes="Estudios imaginológicos urgentes; 'fiebre persistente después "
                "de 72 horas de tratamiento antibiótico correcto' se representa como "
                "duración de fiebre ≥72h acoplada a tratamiento correcto "
                "(vi_fiebre_72h_dos_condiciones).",
            ),
            action_refs=("act_imagen_urgente_eco_tc",),
        ),
        "rule_tc_abscesos_nefritis": _rule(
            "rule_tc_abscesos_nefritis",
            _flag("sospecha_absceso_nefritis_local"),
            _prov(
                n,
                ("frag_p3_imagen_tc_abscesos",),
                notes="TC con contraste cuando se busquen pequeños abscesos y áreas de "
                "nefritis local.",
            ),
            action_refs=("act_tc_contraste",),
        ),
        "rule_imagen_urotomografia": _rule(
            "rule_imagen_urotomografia",
            _membership("sospecha_alteracion", ("estructural",)),
            _prov(
                n,
                ("frag_p3_imagen_urotomografia",),
                notes="Sospecha de alteración estructural (incluyendo litiasis) → urotomografía.",
            ),
            action_refs=("act_urotomografia",),
        ),
        "rule_imagen_ecografia_funcional": _rule(
            "rule_imagen_ecografia_funcional",
            _membership("sospecha_alteracion", ("funcional",)),
            _prov(
                n,
                ("frag_p3_imagen_ecografia",),
                notes="Sospecha de alteración funcional (vaciamiento vesical "
                "inadecuado u obstrucción) → ecografía de vías urinarias con residuo "
                "postmiccional.",
            ),
            action_refs=("act_ecografia_vias_urinarias",),
        ),
        "rule_ecografia_renal_gestante": _rule(
            "rule_ecografia_renal_gestante",
            _or(
                _flag("pielonefritis"),
                _flag("mas_de_un_episodio_itu"),
                _and(_flag("sospecha_litiasis"), _or(_flag("hematuria"), _flag("dolor"))),
            ),
            _prov(
                n,
                ("frag_p3_imagen_gestante",),
                notes="Ecografía renal en gestantes con pielonefritis, más de un "
                "episodio de ITU durante el embarazo, o sospecha de litiasis por "
                "hematuria y/o dolor; hematuria/dolor no son indicaciones "
                "independientes.",
            ),
            applies_to=_flag("gestante"),
            action_refs=("act_ecografia_renal",),
        ),
        # --- Treatment indications (1) ---
        "rule_tto_ba_indicado": _rule(
            "rule_tto_ba_indicado",
            _and(
                _flag("bacteriuria_significativa"),
                _flag("sin_signos_sintomas_itu"),
                _or(_flag("gestante"), _flag("procedimiento_invasivo_vias_urinarias")),
            ),
            _prov(
                n,
                (
                    "frag_p3_tto_ba_indicaciones",
                    "frag_p3_tto_ba_gestante",
                    "frag_p3_tto_ba_procedimiento",
                    "frag_p2_embarazada_debe_tratarse",
                ),
                notes="El encabezado 'Indicaciones de tratamiento de bacteriuria "
                "asintomática' define el contexto; el contexto BA se explicita en la "
                "condición porque el modelo no tiene campo de alcance por sección.",
            ),
            action_refs=("act_tratar_bacteriuria_asintomatica",),
        ),
        # --- Hospitalization (9) ---
        "rule_hosp_criterio_choque_septico": _rule(
            "rule_hosp_criterio_choque_septico",
            _flag("choque_septico"),
            _prov(s, ("frag_p3_hosp_choque_septico",)),
        ),
        "rule_hosp_criterio_intolerancia_oral": _rule(
            "rule_hosp_criterio_intolerancia_oral",
            _flag("intolerancia_via_oral"),
            _prov(s, ("frag_p3_hosp_intolerancia",)),
        ),
        "rule_hosp_criterio_itu_alta": _rule(
            "rule_hosp_criterio_itu_alta",
            _flag("itu_alta"),
            _prov(s, ("frag_p3_hosp_itu_alta",)),
        ),
        "rule_hosp_criterio_descompensacion": _rule(
            "rule_hosp_criterio_descompensacion",
            _flag("descompensacion_enfermedad_base"),
            _prov(s, ("frag_p3_hosp_descompensacion",)),
        ),
        "rule_hosp_criterio_germen_resistente": _rule(
            "rule_hosp_criterio_germen_resistente",
            _flag("germen_resistente_sin_opcion_ambulatoria"),
            _prov(
                n, ("frag_p3_hosp_resistente",), notes="Colapsa el bullet completo de la fuente."
            ),
        ),
        "rule_hosp_criterio_funcion_renal": _rule(
            "rule_hosp_criterio_funcion_renal",
            _flag("deterioro_funcion_renal"),
            _prov(s, ("frag_p3_hosp_funcion_renal",)),
        ),
        "rule_hosp_criterio_absceso": _rule(
            "rule_hosp_criterio_absceso",
            _flag("absceso_renal_pararrenal"),
            _prov(s, ("frag_p3_hosp_absceso",)),
        ),
        "rule_hosp_criterio_soporte_social": _rule(
            "rule_hosp_criterio_soporte_social",
            _flag("soporte_social_inadecuado"),
            _prov(n, ("frag_p3_hosp_social",), notes="Colapsa el bullet completo de la fuente."),
        ),
        "rule_hospitalizacion": _rule(
            "rule_hospitalizacion",
            hospitalization,
            _prov(
                n,
                (
                    "frag_p3_hosp_choque_septico",
                    "frag_p3_hosp_intolerancia",
                    "frag_p3_hosp_itu_alta",
                    "frag_p3_hosp_descompensacion",
                    "frag_p3_hosp_resistente",
                    "frag_p3_hosp_funcion_renal",
                    "frag_p3_hosp_absceso",
                    "frag_p3_hosp_social",
                ),
                notes="Composición OR de las 8 indicaciones de hospitalización "
                "aplicables a adultos; 'Pielonefritis aguda en pacientes pediátricos' "
                "queda fuera del alcance adulto (vi_criterio_pediatrico_fuera_alcance).",
            ),
            action_refs=("act_hospitalizar",),
        ),
        # --- Discharge (10) ---
        "rule_egreso_afebril_48h": _rule(
            "rule_egreso_afebril_48h",
            _temporal("afebril_horas", 48, "hours"),
            _prov(
                n,
                ("frag_p3_egreso_afebril",),
                notes="'48 horas afebril' como duración del estado afebril.",
            ),
        ),
        "rule_egreso_tas": _rule(
            "rule_egreso_tas",
            _gt("tas", 90),
            _prov(n, ("frag_p3_egreso_tas",), notes="Umbral estricto '> 90 mmHg'."),
        ),
        "rule_egreso_fc": _rule("rule_egreso_fc", _lt("fc", 100), _prov(s, ("frag_p4_egreso_fc",))),
        "rule_egreso_fr": _rule("rule_egreso_fr", _lt("fr", 24), _prov(s, ("frag_p4_egreso_fr",))),
        "rule_egreso_sato2_pao2": _rule(
            "rule_egreso_sato2_pao2",
            _or(_gt("sato2", 90), _gt("pao2", 60)),
            _prov(s, ("frag_p4_egreso_sato2_pao2",)),
        ),
        "rule_egreso_via_oral": _rule(
            "rule_egreso_via_oral",
            _flag("tolera_via_oral"),
            _prov(s, ("frag_p4_egreso_via_oral",)),
        ),
        "rule_egreso_comorbilidades": _rule(
            "rule_egreso_comorbilidades",
            _flag("comorbilidades_compensadas"),
            _prov(s, ("frag_p4_egreso_comorbilidades",)),
        ),
        "rule_egreso_tratamiento": _rule(
            "rule_egreso_tratamiento",
            _flag("tratamiento_ambulatorio_asegurado"),
            _prov(
                n,
                ("frag_p4_egreso_tratamiento",),
                notes="Colapsa 'Se ha asegurado el tratamiento ambulatorio'.",
            ),
        ),
        "rule_egreso_social": _rule(
            "rule_egreso_social",
            _flag("condiciones_sociales_permiten"),
            _prov(
                n,
                ("frag_p4_egreso_social",),
                notes="Colapsa 'Lo permiten las condiciones sociales'.",
            ),
        ),
        "rule_plan_egreso": _rule(
            "rule_plan_egreso",
            egreso,
            _prov(
                n,
                (
                    "frag_p3_egreso_afebril",
                    "frag_p3_egreso_tas",
                    "frag_p4_egreso_fc",
                    "frag_p4_egreso_fr",
                    "frag_p4_egreso_sato2_pao2",
                    "frag_p4_egreso_via_oral",
                    "frag_p4_egreso_comorbilidades",
                    "frag_p4_egreso_tratamiento",
                    "frag_p4_egreso_social",
                ),
                notes="Indicaciones para paso a terapia oral y/o egreso compuestas con "
                "AND de los criterios de la fuente.",
            ),
            action_refs=("act_egreso",),
        ),
        # --- Treatment selection (9) ---
        "rule_t1_itu_baja": _rule(
            "rule_t1_itu_baja",
            _flag("itu_baja"),
            _prov(
                n,
                (
                    "frag_p4_t1_itu_baja",
                    "frag_p4_t1_itu_baja_antibioticos",
                    "frag_p4_t1_dosis_baja_ba",
                ),
                notes="Fila 'ITU baja (complicada o no complicada)'; las tres acciones "
                "PRESCRIBE son alternativas declaradas en la fuente, nunca ejecución "
                "simultánea.",
            ),
            action_refs=("act_t1_nitrofurantoina", "act_t1_cefalexina", "act_t1_fosfomicina"),
        ),
        "rule_t1_ba_row": _rule(
            "rule_t1_ba_row",
            _and(
                _flag("bacteriuria_significativa"),
                _flag("sin_signos_sintomas_itu"),
                _or(_flag("gestante"), _flag("procedimiento_invasivo_vias_urinarias")),
            ),
            _prov(
                n,
                (
                    "frag_p4_t1_ba_row",
                    "frag_p4_t1_itu_baja_antibioticos",
                    "frag_p4_t1_dosis_baja_ba",
                    "frag_p4_t1_nota_ba",
                ),
                notes="Fila 'Bacteriuria asintomática**'; la nota ** restringe su "
                "tratamiento a gestantes o pacientes con procedimientos urológicos "
                "donde se prevé la disrupción del uroepitelio. Alternativas declaradas "
                "en la fuente.",
            ),
            action_refs=(
                "act_t1_ba_nitrofurantoina",
                "act_t1_ba_cefalexina",
                "act_t1_ba_fosfomicina",
            ),
        ),
        "rule_t1_alta_ambulatoria": _rule(
            "rule_t1_alta_ambulatoria",
            _and(_flag("itu_alta"), _not(_flag("hospitalizado"))),
            _prov(
                n,
                ("frag_p4_t1_ambulatoria", "frag_p4_t1_ambulatoria_dosis"),
                notes="Fila 'ITU alta ambulatoria' representada como ITU alta no hospitalizada.",
            ),
            action_refs=("act_cefalexina_alta_amb",),
        ),
        "rule_t1_alta_hosp_sin_fr": _rule(
            "rule_t1_alta_hosp_sin_fr",
            _and(_flag("itu_alta"), _flag("hospitalizado"), _not(fr_bgn)),
            _prov(
                n,
                ("frag_p4_t1_sin_fr", "frag_p4_t1_sin_fr_drogas", "frag_p4_t1_sin_fr_dosis"),
                notes="Fila 'ITU alta hospitalaria sin FR para BGN resistentes'; "
                "alternativas declaradas en la fuente.",
            ),
            action_refs=("act_cefazolina", "act_amikacina"),
        ),
        "rule_t1_alta_hosp_con_fr_piperacilina": _rule(
            "rule_t1_alta_hosp_con_fr_piperacilina",
            _and(_flag("itu_alta"), _flag("hospitalizado"), fr_bgn),
            _prov(
                n,
                ("frag_p4_t1_con_fr", "frag_p4_t1_con_fr_drogas", "frag_p4_t1_con_fr_dosis"),
                notes="Fila 'ITU alta hospitalaria con FR para BGN resistentes'; "
                "piperacilina tazobactam sin restricción de choque declarada.",
            ),
            action_refs=("act_piperacilina_tazobactam",),
        ),
        "rule_t1_alta_hosp_con_fr_amikacina": _rule(
            "rule_t1_alta_hosp_con_fr_amikacina",
            _and(_flag("itu_alta"), _flag("hospitalizado"), fr_bgn),
            _prov(
                n,
                (
                    "frag_p4_t1_con_fr",
                    "frag_p4_t1_con_fr_drogas",
                    "frag_p4_t1_con_fr_dosis",
                    "frag_p4_t1_nota_amikacina",
                ),
                notes="Nota 2: evitar amikacina en choque.",
            ),
            exceptions=(_flag("choque_septico"),),
            action_refs=("act_amikacina",),
        ),
        "rule_t1_alta_hosp_con_fr_meropenem": _rule(
            "rule_t1_alta_hosp_con_fr_meropenem",
            _and(_flag("itu_alta"), _flag("hospitalizado"), fr_bgn, _flag("choque_septico")),
            _prov(
                n,
                (
                    "frag_p4_t1_con_fr",
                    "frag_p4_t1_con_fr_drogas",
                    "frag_p4_t1_con_fr_dosis",
                    "frag_p4_t1_nota_meropenem",
                ),
                notes="Nota 3: meropenem se administra empíricamente si hay choque.",
            ),
            action_refs=("act_meropenem",),
        ),
        "rule_fosfomicina_preferida": _rule(
            "rule_fosfomicina_preferida",
            _or(_flag("itu_recurrente"), _flag("antibioticos_ultimos_90dias")),
            _prov(s, ("frag_p4_t1_nota_fosfomicina", "frag_p5_t2_nota3")),
            notes="Preferencia declarada por la fuente, no selección obligatoria.",
        ),
        "rule_reevaluar_48h": _rule(
            "rule_reevaluar_48h",
            _temporal("tiempo_desde_inicio_terapia_hours", 48, "hours"),
            _prov(
                n,
                ("frag_p4_t1_reevaluar",),
                notes="Reevaluar con urocultivo a las 48 horas para ajuste; nota 1 de "
                "la fila 'ITU alta ambulatoria'.",
            ),
            applies_to=_and(_flag("itu_alta"), _not(_flag("hospitalizado"))),
            action_refs=("act_urocultivo_control",),
        ),
        # --- Pregnancy (7) ---
        "rule_t2_ba_gestante": _rule(
            "rule_t2_ba_gestante",
            _and(_flag("bacteriuria_significativa"), _flag("sin_signos_sintomas_itu")),
            _prov(
                n,
                ("frag_p4_t2_ba_row",),
                notes="Fila 'Bacteriuria asintomática' de la Tabla 2; alternativas "
                "declaradas en la fuente.",
            ),
            applies_to=_flag("gestante"),
            action_refs=(
                "act_t2_ba_nitrofurantoina",
                "act_t2_ba_cefalexina",
                "act_t2_ba_fosfomicina",
            ),
        ),
        "rule_t2_itu_baja_gestante": _rule(
            "rule_t2_itu_baja_gestante",
            _flag("itu_baja"),
            _prov(
                n,
                ("frag_p4_t2_itu_baja_row",),
                notes="Fila 'ITU baja' de la Tabla 2; alternativas declaradas en la fuente.",
            ),
            applies_to=_flag("gestante"),
            action_refs=(
                "act_t2_baja_nitrofurantoina",
                "act_t2_baja_cefalexina",
                "act_t2_baja_fosfomicina",
            ),
        ),
        "rule_t2_itu_alta_gestante_cefazolina": _rule(
            "rule_t2_itu_alta_gestante_cefazolina",
            _and(_flag("itu_alta"), _not(fr_bgn)),
            _prov(
                n,
                ("frag_p5_t2_itu_alta_row", "frag_p5_t2_sin_fr"),
                notes="Cefazolina: * sin factores de riesgo para BGN resistentes.",
            ),
            applies_to=_flag("gestante"),
            action_refs=("act_cefazolina",),
        ),
        "rule_t2_itu_alta_gestante_piperacilina": _rule(
            "rule_t2_itu_alta_gestante_piperacilina",
            _and(_flag("itu_alta"), fr_bgn, _not(_flag("choque_septico"))),
            _prov(
                n,
                ("frag_p5_t2_itu_alta_row", "frag_p5_t2_con_fr"),
                notes="Piperacilina tazobactam: ** con factores de riesgo para BGN "
                "resistentes, sin choque.",
            ),
            applies_to=_flag("gestante"),
            action_refs=("act_piperacilina_tazobactam",),
        ),
        "rule_t2_itu_alta_gestante_meropenem": _rule(
            "rule_t2_itu_alta_gestante_meropenem",
            _and(_flag("itu_alta"), fr_bgn, _flag("choque_septico")),
            _prov(
                n,
                ("frag_p5_t2_itu_alta_row", "frag_p5_t2_con_fr_choque"),
                notes="Meropenem: *** con factores de riesgo para BGN resistentes, con choque.",
            ),
            applies_to=_flag("gestante"),
            action_refs=("act_meropenem",),
        ),
        "rule_t2_preventiva_baja": _rule(
            "rule_t2_preventiva_baja",
            _and(_flag("itu_baja"), _flag("recurrencia_itu")),
            _prov(
                n,
                ("frag_p4_t2_itu_baja_row", "frag_p4_t2_preventiva_baja", "frag_p5_t2_nota2"),
                notes="Terapia preventiva 'sólo si hay recurrencia de la infección'; "
                "la decisión se toma con base en cultivos y pruebas de sensibilidad "
                "(nota 2). Alternativas declaradas en la fuente.",
            ),
            applies_to=_flag("gestante"),
            action_refs=(
                "act_preventiva_nitrofurantoina",
                "act_preventiva_cefalexina",
                "act_preventiva_tmpsmx",
                "act_preventiva_fosfomicina",
            ),
        ),
        "rule_t2_preventiva_alta": _rule(
            "rule_t2_preventiva_alta",
            _flag("itu_alta"),
            _prov(
                n,
                ("frag_p5_t2_itu_alta_row", "frag_p5_t2_preventiva_alta", "frag_p5_t2_nota2"),
                notes="Terapia preventiva indicada ('Sí') en la fila ITU alta de la "
                "Tabla 2; la decisión se toma con base en cultivos y pruebas de "
                "sensibilidad (nota 2). Alternativas declaradas en la fuente.",
            ),
            applies_to=_flag("gestante"),
            action_refs=(
                "act_preventiva_nitrofurantoina",
                "act_preventiva_cefalexina",
                "act_preventiva_tmpsmx",
                "act_preventiva_fosfomicina",
            ),
        ),
    }


def _build_validation_items() -> dict[str, ValidationItem]:
    open_status = ValidationItemStatus.OPEN
    return {
        "vi_recuento_significativo_umbral": ValidationItem(
            id="vi_recuento_significativo_umbral",
            category="gap",
            description="DEFINICIONES usa 'recuento significativo de colonias "
            "bacterianas' / 'bacteriuria significativa' sin umbral numérico; los "
            "umbrales de la página 3 son específicos por contexto y no se codifican "
            "como umbral universal de la variable bacteriuria_significativa.",
            severity="high",
            related_ids=("bacteriuria_significativa", "rule_def_ba", "rule_def_itu"),
            status=open_status,
        ),
        "vi_urocultivo_umbrales_ocr": ValidationItem(
            id="vi_urocultivo_umbrales_ocr",
            category="ambiguity",
            description="Los umbrales de positividad del urocultivo contienen "
            "artefactos OCR/superíndices ('10 5', 'o btenida'); la evidencia verbatim "
            "los preserva y la representación numérica normalizada está documentada "
            "en la procedencia.",
            severity="low",
            related_ids=("frag_p3_urocultivo_positivo_1e5",),
            status=open_status,
        ),
        "vi_nota_doble_asterisco": ValidationItem(
            id="vi_nota_doble_asterisco",
            category="ambiguity",
            description="El marcador '**' aparece dos veces en las notas de la Tabla "
            "1 (fila de bacteriuria asintomática y definición de FR para BGN "
            "resistentes); ambas notas se conservan como fragmentos separados.",
            severity="low",
            related_ids=("frag_p4_t1_nota_ba", "frag_p4_t1_nota_fr"),
            status=open_status,
        ),
        "vi_seleccion_antibiotico_alternativas": ValidationItem(
            id="vi_seleccion_antibiotico_alternativas",
            category="limitation",
            description="Las tablas declaran alternativas ('Nitrofurantoína o "
            "Cefalexina o Fosfomicina') sin lógica de selección; las múltiples "
            "acciones PRESCRIBE de una regla son alternativas declaradas en la fuente "
            "y nunca se ejecutan simultáneamente. Fase 7 debe renderizarlas unidas "
            "por 'o', nunca como prescripciones simultáneas.",
            severity="high",
            related_ids=("rule_t1_itu_baja", "rule_t1_ba_row", "rule_t2_ba_gestante"),
            status=open_status,
        ),
        "vi_restricciones_procedimiento": ValidationItem(
            id="vi_restricciones_procedimiento",
            category="limitation",
            description="La instrucción de tomar la muestra antes de la primera dosis "
            "de antibiótico está adherida a la indicación del urocultivo; los detalles "
            "de procedimiento (desechar 15-30 ml iniciales, sonda recién insertada) "
            "permanecen declarativos.",
            severity="low",
            related_ids=("rule_urocultivo_indicado", "act_restriccion_muestra_previa"),
            status=open_status,
        ),
        "vi_evitar_primer_trimestre_ambiguedad": ValidationItem(
            id="vi_evitar_primer_trimestre_ambiguedad",
            category="ambiguity",
            description="'Evitar en primer trimestre' aparece en la columna de "
            "observaciones de las filas ITU baja y ITU alta de la Tabla 2 sin nombrar "
            "el medicamento; la capa de texto no permite mapearlo a un fármaco "
            "específico, por lo que no se codifica como restricción por medicamento.",
            severity="medium",
            related_ids=("frag_p5_t2_observacion_trimestre", "frag_p4_t2_itu_baja_row"),
            status=open_status,
        ),
        "vi_semana34_calendar": ValidationItem(
            id="vi_semana34_calendar",
            category="limitation",
            description="'Hasta semana 34 gestación', el posible cambio a cefalexina o "
            "nitrofurantoína en la semana 34 'si el microorganismo es sensible' y "
            "'administrar hasta la finalización del embarazo' son construcciones de "
            "calendario no computables por el motor; se transportan en payloads y "
            "notas.",
            severity="medium",
            related_ids=("frag_p5_t2_nota4", "act_preventiva_nitrofurantoina"),
            status=open_status,
        ),
        "vi_historia_clinica_no_computable": ValidationItem(
            id="vi_historia_clinica_no_computable",
            category="limitation",
            description="Hospitalización >48h en los últimos 3 meses, uso de "
            "antibióticos en los últimos 90 días, recurrencia y número de episodios "
            "son entradas clínicas/históricas externas; el motor no computa historias "
            "ni calendarios.",
            severity="medium",
            related_ids=(
                "hospitalizacion_48h_ultimos_3meses",
                "antibioticos_ultimos_90dias",
                "mas_de_un_episodio_itu",
                "recurrencia_itu",
                "itu_recurrente",
            ),
            status=open_status,
        ),
        "vi_fiebre_72h_dos_condiciones": ValidationItem(
            id="vi_fiebre_72h_dos_condiciones",
            category="ambiguity",
            description="'Fiebre persistente después de 72 horas de tratamiento "
            "antibiótico correcto' acopla duración de fiebre y adecuación del "
            "tratamiento; se representa como duración ≥72h AND tratamiento correcto.",
            severity="low",
            related_ids=("fiebre_horas", "tratamiento_antibiotico_correcto", "rule_imagen_urgente"),
            status=open_status,
        ),
        "vi_criterio_pediatrico_fuera_alcance": ValidationItem(
            id="vi_criterio_pediatrico_fuera_alcance",
            category="scope",
            description="El bullet 'Pielonefritis aguda en pacientes pediátricos' se "
            "conserva como evidencia fuente (frag_p3_hosp_pediatrica); no se crea "
            "regla ejecutable porque el alcance del protocolo excluye neonatos y "
            "niños. La composición de hospitalización usa las 8 indicaciones "
            "aplicables a adultos.",
            severity="medium",
            related_ids=("frag_p3_hosp_pediatrica",),
            status=open_status,
        ),
        "vi_prostatitis_fuera_alcance": ValidationItem(
            id="vi_prostatitis_fuera_alcance",
            category="scope",
            description="La fuente incluye prostatitis en la definición de ITU "
            "complicada y declara que 'excede los alcances del presente protocolo'; "
            "se conserva como evidencia y en las notas de la regla, sin acción "
            "operativa inventada.",
            severity="medium",
            related_ids=("frag_p1_def_itu_complicada_clinica", "rule_def_itu_complicada_clinica"),
            status=open_status,
        ),
        "vi_ajuste_urocultivo_antibiograma": ValidationItem(
            id="vi_ajuste_urocultivo_antibiograma",
            category="limitation",
            description="'Siempre debe ajustarse según resultados de urocultivo y "
            "antibiograma' y 'la decisión se toma con base en los cultivos y pruebas "
            "de sensibilidad' son instrucciones procedimentales no computables; se "
            "transportan en la procedencia.",
            severity="low",
            related_ids=("frag_p5_t2_nota1", "frag_p5_t2_nota2"),
            status=open_status,
        ),
    }


def _build_test_cases() -> dict[str, TestCase]:
    hosp_flag_ids = (
        "choque_septico",
        "intolerancia_via_oral",
        "itu_alta",
        "descompensacion_enfermedad_base",
        "germen_resistente_sin_opcion_ambulatoria",
        "deterioro_funcion_renal",
        "absceso_renal_pararrenal",
        "soporte_social_inadecuado",
    )

    def hosp_inputs(**overrides: Scalar) -> dict[str, Scalar]:
        inputs: dict[str, Scalar] = {key: False for key in hosp_flag_ids}
        inputs.update(overrides)
        return inputs

    fr_flag_ids = (
        "hospitalizacion_48h_ultimos_3meses",
        "antibioticos_ultimos_90dias",
        "colonizacion_blee",
    )

    def fr_inputs(**overrides: Scalar) -> dict[str, Scalar]:
        inputs: dict[str, Scalar] = {key: False for key in fr_flag_ids}
        inputs.update(overrides)
        return inputs

    def egreso_inputs(**overrides: Scalar) -> dict[str, Scalar]:
        inputs: dict[str, Scalar] = {
            "afebril_horas": 48,
            "tas": 91,
            "fc": 99,
            "fr": 23,
            "sato2": 91,
            "pao2": 61,
            "tolera_via_oral": True,
            "comorbilidades_compensadas": True,
            "tratamiento_ambulatorio_asegurado": True,
            "condiciones_sociales_permiten": True,
        }
        inputs.update(overrides)
        return inputs

    return {
        # --- Definitions (15) ---
        "tc_def_itu_pos": TestCase(
            id="tc_def_itu_pos",
            inputs={"bacteriuria_significativa": True, "signos_sintomas_itu": True},
            expected_results={"rule_def_itu": T},
        ),
        "tc_def_itu_missing": TestCase(
            id="tc_def_itu_missing",
            inputs={"bacteriuria_significativa": None, "signos_sintomas_itu": True},
            expected_results={"rule_def_itu": U},
        ),
        "tc_def_ba_cultivos_mujer_2": TestCase(
            id="tc_def_ba_cultivos_mujer_2",
            inputs={
                "mujer_no_embarazada": True,
                "urocultivos_2_mismo_patron": True,
                "hombre": False,
                "gestante": False,
                "urocultivo_unico": False,
            },
            expected_results={"rule_def_ba_cultivos": T},
        ),
        "tc_def_ba_cultivos_hombre_1": TestCase(
            id="tc_def_ba_cultivos_hombre_1",
            inputs={
                "mujer_no_embarazada": False,
                "hombre": True,
                "urocultivo_unico": True,
                "gestante": False,
                "urocultivos_2_mismo_patron": False,
            },
            expected_results={"rule_def_ba_cultivos": T},
        ),
        "tc_def_ba_cultivos_gestante_1": TestCase(
            id="tc_def_ba_cultivos_gestante_1",
            inputs={
                "gestante": True,
                "urocultivo_unico": True,
                "mujer_no_embarazada": False,
                "hombre": False,
                "urocultivos_2_mismo_patron": False,
            },
            expected_results={"rule_def_ba_cultivos": T},
        ),
        "tc_def_ba_cultivos_ninguno": TestCase(
            id="tc_def_ba_cultivos_ninguno",
            inputs={
                "mujer_no_embarazada": True,
                "urocultivos_2_mismo_patron": False,
                "hombre": False,
                "gestante": False,
                "urocultivo_unico": False,
            },
            expected_results={"rule_def_ba_cultivos": F},
        ),
        "tc_def_ba_piuria_pediatrica": TestCase(
            id="tc_def_ba_piuria_pediatrica",
            inputs={"poblacion_pediatrica": True, "ausencia_piuria_sedimento": True},
            expected_results={"rule_def_ba_piuria_pediatrica": T},
        ),
        "tc_def_ba_pos": TestCase(
            id="tc_def_ba_pos",
            inputs={"bacteriuria_significativa": True, "sin_signos_sintomas_itu": True},
            expected_results={"rule_def_ba": T},
        ),
        "tc_def_ba_neg": TestCase(
            id="tc_def_ba_neg",
            inputs={"bacteriuria_significativa": True, "sin_signos_sintomas_itu": False},
            expected_results={"rule_def_ba": F},
        ),
        "tc_def_ba_missing": TestCase(
            id="tc_def_ba_missing",
            inputs={"bacteriuria_significativa": None, "sin_signos_sintomas_itu": True},
            expected_results={"rule_def_ba": U},
        ),
        "tc_def_ba_completa_mujer": TestCase(
            id="tc_def_ba_completa_mujer",
            inputs={
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
                "mujer_no_embarazada": True,
                "urocultivos_2_mismo_patron": True,
                "hombre": False,
                "gestante": False,
                "urocultivo_unico": False,
            },
            expected_results={"rule_def_ba": T, "rule_def_ba_cultivos": T},
        ),
        "tc_def_itu_bajo_pos": TestCase(
            id="tc_def_itu_bajo_pos",
            inputs={
                "infeccion_aguda_vejiga_uretra": True,
                "bacteriuria_significativa": True,
                "sin_leucorrea": True,
                "sin_irritacion_vaginal": True,
                "sin_fiebre": True,
                "sin_dolor_lumbar": True,
                "sin_compromiso_sistemico": True,
            },
            expected_results={"rule_def_itu_bajo": T},
        ),
        "tc_def_itu_bajo_con_fiebre": TestCase(
            id="tc_def_itu_bajo_con_fiebre",
            inputs={
                "infeccion_aguda_vejiga_uretra": True,
                "bacteriuria_significativa": True,
                "sin_leucorrea": True,
                "sin_irritacion_vaginal": True,
                "sin_fiebre": False,
                "sin_dolor_lumbar": True,
                "sin_compromiso_sistemico": True,
            },
            expected_results={"rule_def_itu_bajo": F},
        ),
        "tc_def_itu_complicada_estructural": TestCase(
            id="tc_def_itu_complicada_estructural",
            inputs={"alteracion_estructural": True, "alteracion_funcional": False},
            expected_results={"rule_def_itu_complicada_estructural": T},
        ),
        "tc_def_itu_complicada_clinica": TestCase(
            id="tc_def_itu_complicada_clinica",
            inputs={
                "pielonefritis": True,
                "itu_febril_bacteriemica": False,
                "itu_asociada_cateter": False,
                "alteracion_estructural": False,
                "alteracion_funcional": False,
            },
            expected_results={
                "rule_def_itu_complicada_clinica": T,
                "rule_def_itu_complicada_estructural": F,
            },
        ),
        # --- Diagnosis (19) ---
        "tc_citoquimico_pos": TestCase(
            id="tc_citoquimico_pos",
            inputs={"en_urgencias": True, "sospecha_itu": True, "mujer": False},
            expected_results={"rule_citoquimico_orina": T},
        ),
        "tc_citoquimico_excepcion": TestCase(
            id="tc_citoquimico_excepcion",
            inputs={
                "en_urgencias": True,
                "sospecha_itu": True,
                "mujer": True,
                "primer_episodio": True,
                "sintomas_tipicos": True,
            },
            expected_results={"rule_citoquimico_orina": F},
        ),
        "tc_citoquimico_missing": TestCase(
            id="tc_citoquimico_missing",
            inputs={"en_urgencias": None, "sospecha_itu": True},
            expected_results={"rule_citoquimico_orina": U},
        ),
        "tc_tirilla_descarta": TestCase(
            id="tc_tirilla_descarta",
            inputs={"tirilla_normal": True, "sospecha_clinica_baja": True},
            expected_results={"rule_tirilla_descarta_diagnostico": T},
        ),
        "tc_piuria_11": TestCase(
            id="tc_piuria_11",
            inputs={"leucocitos_orina_campo": 11},
            expected_results={"rule_piuria_mayor_10": T},
        ),
        "tc_piuria_10": TestCase(
            id="tc_piuria_10",
            inputs={"leucocitos_orina_campo": 10},
            expected_results={"rule_piuria_mayor_10": F},
        ),
        "tc_gram_urgencias": TestCase(
            id="tc_gram_urgencias",
            inputs={"en_urgencias": True},
            expected_results={"rule_gram_urgencias": T},
        ),
        "tc_urocultivo_pos": TestCase(
            id="tc_urocultivo_pos",
            inputs={"sospecha_itu": True, "mujer": False},
            expected_results={"rule_urocultivo_indicado": T},
        ),
        "tc_urocultivo_excepcion": TestCase(
            id="tc_urocultivo_excepcion",
            inputs={
                "sospecha_itu": True,
                "mujer": True,
                "primer_episodio": True,
                "itu_baja_no_complicada": True,
                "premenopausica": True,
            },
            expected_results={"rule_urocultivo_indicado": F},
        ),
        "tc_urocultivo_1e5": TestCase(
            id="tc_urocultivo_1e5",
            inputs={"urocultivo_cfu_ml": 100000, "muestra_miccion_espontanea": True},
            expected_results={"rule_urocultivo_positivo_1e5": T},
        ),
        "tc_urocultivo_1e5_abajo": TestCase(
            id="tc_urocultivo_1e5_abajo",
            inputs={"urocultivo_cfu_ml": 99999, "muestra_miccion_espontanea": True},
            expected_results={"rule_urocultivo_positivo_1e5": F},
        ),
        "tc_urocultivo_1e3": TestCase(
            id="tc_urocultivo_1e3",
            inputs={
                "urocultivo_cfu_ml": 1000,
                "sintomas_no_explicados_otra_patologia": True,
            },
            expected_results={"rule_urocultivo_positivo_1e3": T},
        ),
        "tc_urocultivo_1e2": TestCase(
            id="tc_urocultivo_1e2",
            inputs={"urocultivo_cfu_ml": 100, "sonda_recien_insertada": True},
            expected_results={"rule_urocultivo_positivo_1e2": T},
        ),
        "tc_analisis_sangre_hosp": TestCase(
            id="tc_analisis_sangre_hosp",
            inputs={**hosp_inputs(choque_septico=True), "infeccion_urinaria": True},
            expected_results={"rule_analisis_sangre": T},
        ),
        "tc_analisis_sangre_no_hosp": TestCase(
            id="tc_analisis_sangre_no_hosp",
            inputs={**hosp_inputs(), "infeccion_urinaria": True},
            expected_results={"rule_analisis_sangre": F},
        ),
        "tc_hemocultivos_pos": TestCase(
            id="tc_hemocultivos_pos",
            inputs={
                "pielonefritis": True,
                "fiebre": True,
                "hipotermia": False,
                "choque_septico": False,
            },
            expected_results={"rule_hemocultivos": T},
        ),
        "tc_hemocultivos_hipotermia": TestCase(
            id="tc_hemocultivos_hipotermia",
            inputs={
                "pielonefritis": True,
                "fiebre": False,
                "hipotermia": True,
                "choque_septico": False,
            },
            expected_results={"rule_hemocultivos": T},
        ),
        "tc_hemocultivos_neg": TestCase(
            id="tc_hemocultivos_neg",
            inputs={
                "pielonefritis": True,
                "fiebre": False,
                "hipotermia": False,
                "choque_septico": False,
            },
            expected_results={"rule_hemocultivos": F},
        ),
        "tc_hemocultivos_no_aplica": TestCase(
            id="tc_hemocultivos_no_aplica",
            inputs={"pielonefritis": False, "fiebre": True},
            expected_results={"rule_hemocultivos": F},
        ),
        # --- Imaging (14) ---
        "tc_imagen_shock": TestCase(
            id="tc_imagen_shock",
            inputs={
                "infeccion_urinaria": True,
                "choque_septico": True,
                "falla_renal_aguda": False,
                "complicacion_local": False,
                "fiebre_horas": 0,
                "tratamiento_antibiotico_correcto": False,
            },
            expected_results={"rule_imagen_urgente": T},
        ),
        "tc_imagen_fiebre_72": TestCase(
            id="tc_imagen_fiebre_72",
            inputs={
                "infeccion_urinaria": True,
                "choque_septico": False,
                "falla_renal_aguda": False,
                "complicacion_local": False,
                "fiebre_horas": 72,
                "tratamiento_antibiotico_correcto": True,
            },
            expected_results={"rule_imagen_urgente": T},
        ),
        "tc_imagen_fiebre_71": TestCase(
            id="tc_imagen_fiebre_71",
            inputs={
                "infeccion_urinaria": True,
                "choque_septico": False,
                "falla_renal_aguda": False,
                "complicacion_local": False,
                "fiebre_horas": 71,
                "tratamiento_antibiotico_correcto": True,
            },
            expected_results={"rule_imagen_urgente": F},
        ),
        "tc_imagen_fiebre_72_sin_tto": TestCase(
            id="tc_imagen_fiebre_72_sin_tto",
            inputs={
                "infeccion_urinaria": True,
                "choque_septico": False,
                "falla_renal_aguda": False,
                "complicacion_local": False,
                "fiebre_horas": 72,
                "tratamiento_antibiotico_correcto": False,
            },
            expected_results={"rule_imagen_urgente": F},
        ),
        "tc_imagen_sospecha_solo": TestCase(
            id="tc_imagen_sospecha_solo",
            inputs={
                "sospecha_itu": True,
                "infeccion_urinaria": False,
                "choque_septico": True,
            },
            expected_results={"rule_imagen_urgente": F},
        ),
        "tc_tc_abscesos": TestCase(
            id="tc_tc_abscesos",
            inputs={"sospecha_absceso_nefritis_local": True},
            expected_results={"rule_tc_abscesos_nefritis": T},
        ),
        "tc_imagen_urotomografia": TestCase(
            id="tc_imagen_urotomografia",
            inputs={"sospecha_alteracion": "estructural"},
            expected_results={
                "rule_imagen_urotomografia": T,
                "rule_imagen_ecografia_funcional": F,
            },
        ),
        "tc_imagen_ecografia": TestCase(
            id="tc_imagen_ecografia",
            inputs={"sospecha_alteracion": "funcional"},
            expected_results={"rule_imagen_ecografia_funcional": T},
        ),
        "tc_ecografia_renal_gestante": TestCase(
            id="tc_ecografia_renal_gestante",
            inputs={"gestante": True, "pielonefritis": True},
            expected_results={"rule_ecografia_renal_gestante": T},
        ),
        "tc_ecografia_renal_episodios": TestCase(
            id="tc_ecografia_renal_episodios",
            inputs={
                "gestante": True,
                "mas_de_un_episodio_itu": True,
                "pielonefritis": False,
                "sospecha_litiasis": False,
                "hematuria": False,
                "dolor": False,
            },
            expected_results={"rule_ecografia_renal_gestante": T},
        ),
        "tc_ecografia_renal_litiasis_pos": TestCase(
            id="tc_ecografia_renal_litiasis_pos",
            inputs={
                "gestante": True,
                "sospecha_litiasis": True,
                "hematuria": True,
                "dolor": False,
                "pielonefritis": False,
                "mas_de_un_episodio_itu": False,
            },
            expected_results={"rule_ecografia_renal_gestante": T},
        ),
        "tc_ecografia_renal_dolor_solo": TestCase(
            id="tc_ecografia_renal_dolor_solo",
            inputs={
                "gestante": True,
                "dolor": True,
                "sospecha_litiasis": False,
                "pielonefritis": False,
                "mas_de_un_episodio_itu": False,
                "hematuria": False,
            },
            expected_results={"rule_ecografia_renal_gestante": F},
        ),
        "tc_ecografia_renal_hematuria_sola": TestCase(
            id="tc_ecografia_renal_hematuria_sola",
            inputs={
                "gestante": True,
                "hematuria": True,
                "sospecha_litiasis": False,
                "pielonefritis": False,
                "mas_de_un_episodio_itu": False,
                "dolor": False,
            },
            expected_results={"rule_ecografia_renal_gestante": F},
        ),
        "tc_ecografia_renal_no_gestante": TestCase(
            id="tc_ecografia_renal_no_gestante",
            inputs={"gestante": False, "pielonefritis": True},
            expected_results={"rule_ecografia_renal_gestante": F},
        ),
        # --- Hospitalization (10) ---
        "tc_hosp_choque": TestCase(
            id="tc_hosp_choque",
            inputs=hosp_inputs(choque_septico=True),
            expected_results={
                "rule_hosp_criterio_choque_septico": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_intolerancia": TestCase(
            id="tc_hosp_intolerancia",
            inputs=hosp_inputs(intolerancia_via_oral=True),
            expected_results={
                "rule_hosp_criterio_intolerancia_oral": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_itu_alta": TestCase(
            id="tc_hosp_itu_alta",
            inputs=hosp_inputs(itu_alta=True),
            expected_results={
                "rule_hosp_criterio_itu_alta": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_descompensacion": TestCase(
            id="tc_hosp_descompensacion",
            inputs=hosp_inputs(descompensacion_enfermedad_base=True),
            expected_results={
                "rule_hosp_criterio_descompensacion": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_germen_resistente": TestCase(
            id="tc_hosp_germen_resistente",
            inputs=hosp_inputs(germen_resistente_sin_opcion_ambulatoria=True),
            expected_results={
                "rule_hosp_criterio_germen_resistente": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_funcion_renal": TestCase(
            id="tc_hosp_funcion_renal",
            inputs=hosp_inputs(deterioro_funcion_renal=True),
            expected_results={
                "rule_hosp_criterio_funcion_renal": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_absceso": TestCase(
            id="tc_hosp_absceso",
            inputs=hosp_inputs(absceso_renal_pararrenal=True),
            expected_results={
                "rule_hosp_criterio_absceso": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_soporte_social": TestCase(
            id="tc_hosp_soporte_social",
            inputs=hosp_inputs(soporte_social_inadecuado=True),
            expected_results={
                "rule_hosp_criterio_soporte_social": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_ninguno": TestCase(
            id="tc_hosp_ninguno",
            inputs=hosp_inputs(),
            expected_results={"rule_hospitalizacion": F},
        ),
        "tc_hosp_unknown": TestCase(
            id="tc_hosp_unknown",
            inputs=hosp_inputs(choque_septico=None),
            expected_results={"rule_hospitalizacion": U},
        ),
        # --- Discharge (8) ---
        "tc_egreso_completo": TestCase(
            id="tc_egreso_completo",
            inputs=egreso_inputs(),
            expected_results={"rule_plan_egreso": T},
        ),
        "tc_egreso_afebril_47": TestCase(
            id="tc_egreso_afebril_47",
            inputs=egreso_inputs(afebril_horas=47),
            expected_results={"rule_plan_egreso": F},
        ),
        "tc_egreso_tas_90": TestCase(
            id="tc_egreso_tas_90",
            inputs=egreso_inputs(tas=90),
            expected_results={"rule_egreso_tas": F, "rule_plan_egreso": F},
        ),
        "tc_egreso_fc_100": TestCase(
            id="tc_egreso_fc_100",
            inputs=egreso_inputs(fc=100),
            expected_results={"rule_egreso_fc": F, "rule_plan_egreso": F},
        ),
        "tc_egreso_fr_24": TestCase(
            id="tc_egreso_fr_24",
            inputs=egreso_inputs(fr=24),
            expected_results={"rule_egreso_fr": F, "rule_plan_egreso": F},
        ),
        "tc_egreso_sato2_90_pao2_61": TestCase(
            id="tc_egreso_sato2_90_pao2_61",
            inputs=egreso_inputs(sato2=90, pao2=61),
            expected_results={"rule_egreso_sato2_pao2": T, "rule_plan_egreso": T},
        ),
        "tc_egreso_sato2_90_pao2_60": TestCase(
            id="tc_egreso_sato2_90_pao2_60",
            inputs=egreso_inputs(sato2=90, pao2=60),
            expected_results={"rule_egreso_sato2_pao2": F, "rule_plan_egreso": F},
        ),
        "tc_egreso_missing_pao2": TestCase(
            id="tc_egreso_missing_pao2",
            inputs=egreso_inputs(sato2=90, pao2=None),
            expected_results={"rule_egreso_sato2_pao2": U, "rule_plan_egreso": U},
        ),
        # --- Treatment (17) ---
        "tc_t1_itu_baja": TestCase(
            id="tc_t1_itu_baja",
            inputs={"itu_baja": True},
            expected_results={"rule_t1_itu_baja": T},
        ),
        "tc_t1_ba_gestante": TestCase(
            id="tc_t1_ba_gestante",
            inputs={
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
                "gestante": True,
                "procedimiento_invasivo_vias_urinarias": False,
            },
            expected_results={"rule_t1_ba_row": T},
        ),
        "tc_t1_ba_no_indicada": TestCase(
            id="tc_t1_ba_no_indicada",
            inputs={
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
                "gestante": False,
                "procedimiento_invasivo_vias_urinarias": False,
            },
            expected_results={"rule_t1_ba_row": F},
        ),
        "tc_t1_ba_procedimiento": TestCase(
            id="tc_t1_ba_procedimiento",
            inputs={
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
                "gestante": False,
                "procedimiento_invasivo_vias_urinarias": True,
            },
            expected_results={"rule_t1_ba_row": T},
        ),
        "tc_tto_ba_gestante_con_ba": TestCase(
            id="tc_tto_ba_gestante_con_ba",
            inputs={
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
                "gestante": True,
                "procedimiento_invasivo_vias_urinarias": False,
            },
            expected_results={"rule_tto_ba_indicado": T},
        ),
        "tc_tto_ba_procedimiento_con_ba": TestCase(
            id="tc_tto_ba_procedimiento_con_ba",
            inputs={
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
                "gestante": False,
                "procedimiento_invasivo_vias_urinarias": True,
            },
            expected_results={"rule_tto_ba_indicado": T},
        ),
        "tc_tto_ba_gestante_sin_ba": TestCase(
            id="tc_tto_ba_gestante_sin_ba",
            inputs={
                "bacteriuria_significativa": False,
                "sin_signos_sintomas_itu": True,
                "gestante": True,
                "procedimiento_invasivo_vias_urinarias": False,
            },
            expected_results={"rule_tto_ba_indicado": F},
        ),
        "tc_tto_ba_procedimiento_sin_ba": TestCase(
            id="tc_tto_ba_procedimiento_sin_ba",
            inputs={
                "bacteriuria_significativa": False,
                "sin_signos_sintomas_itu": True,
                "gestante": False,
                "procedimiento_invasivo_vias_urinarias": True,
            },
            expected_results={"rule_tto_ba_indicado": F},
        ),
        "tc_tto_ba_missing": TestCase(
            id="tc_tto_ba_missing",
            inputs={
                "bacteriuria_significativa": None,
                "sin_signos_sintomas_itu": True,
                "gestante": True,
                "procedimiento_invasivo_vias_urinarias": False,
            },
            expected_results={"rule_tto_ba_indicado": U},
        ),
        "tc_t1_alta_amb": TestCase(
            id="tc_t1_alta_amb",
            inputs={"itu_alta": True, "hospitalizado": False},
            expected_results={"rule_t1_alta_ambulatoria": T},
        ),
        "tc_t1_alta_hosp_sin_fr": TestCase(
            id="tc_t1_alta_hosp_sin_fr",
            inputs={**fr_inputs(), "itu_alta": True, "hospitalizado": True},
            expected_results={
                "rule_t1_alta_hosp_sin_fr": T,
                "rule_t1_alta_hosp_con_fr_piperacilina": F,
            },
        ),
        "tc_t1_alta_hosp_con_fr": TestCase(
            id="tc_t1_alta_hosp_con_fr",
            inputs={
                "itu_alta": True,
                "hospitalizado": True,
                "hospitalizacion_48h_ultimos_3meses": True,
            },
            expected_results={
                "rule_fr_bgn_resistentes": T,
                "rule_t1_alta_hosp_con_fr_piperacilina": T,
                "rule_t1_alta_hosp_sin_fr": F,
            },
        ),
        "tc_t1_con_fr_amikacina_sin_choque": TestCase(
            id="tc_t1_con_fr_amikacina_sin_choque",
            inputs={
                "itu_alta": True,
                "hospitalizado": True,
                "antibioticos_ultimos_90dias": True,
                "choque_septico": False,
            },
            expected_results={
                "rule_t1_alta_hosp_con_fr_amikacina": T,
                "rule_t1_alta_hosp_con_fr_meropenem": F,
            },
        ),
        "tc_t1_con_fr_meropenem_choque": TestCase(
            id="tc_t1_con_fr_meropenem_choque",
            inputs={
                "itu_alta": True,
                "hospitalizado": True,
                "colonizacion_blee": True,
                "choque_septico": True,
            },
            expected_results={
                "rule_t1_alta_hosp_con_fr_amikacina": F,
                "rule_t1_alta_hosp_con_fr_meropenem": T,
            },
        ),
        "tc_fosfomicina_preferida": TestCase(
            id="tc_fosfomicina_preferida",
            inputs={"itu_recurrente": True, "antibioticos_ultimos_90dias": False},
            expected_results={"rule_fosfomicina_preferida": T},
        ),
        "tc_reevaluar_48h": TestCase(
            id="tc_reevaluar_48h",
            inputs={
                "itu_alta": True,
                "hospitalizado": False,
                "tiempo_desde_inicio_terapia_hours": 48,
            },
            expected_results={"rule_reevaluar_48h": T},
        ),
        "tc_reevaluar_47h": TestCase(
            id="tc_reevaluar_47h",
            inputs={
                "itu_alta": True,
                "hospitalizado": False,
                "tiempo_desde_inicio_terapia_hours": 47,
            },
            expected_results={"rule_reevaluar_48h": F},
        ),
        # --- Pregnancy (10) ---
        "tc_t2_ba_gestante": TestCase(
            id="tc_t2_ba_gestante",
            inputs={
                "gestante": True,
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
            },
            expected_results={"rule_t2_ba_gestante": T},
        ),
        "tc_t2_ba_no_gestante": TestCase(
            id="tc_t2_ba_no_gestante",
            inputs={
                "gestante": False,
                "bacteriuria_significativa": True,
                "sin_signos_sintomas_itu": True,
            },
            expected_results={"rule_t2_ba_gestante": F},
        ),
        "tc_t2_itu_baja_gestante": TestCase(
            id="tc_t2_itu_baja_gestante",
            inputs={"gestante": True, "itu_baja": True},
            expected_results={"rule_t2_itu_baja_gestante": T},
        ),
        "tc_t2_itu_baja_no_gestante": TestCase(
            id="tc_t2_itu_baja_no_gestante",
            inputs={"gestante": False, "itu_baja": True},
            expected_results={"rule_t2_itu_baja_gestante": F},
        ),
        "tc_t2_alta_cefazolina": TestCase(
            id="tc_t2_alta_cefazolina",
            inputs={**fr_inputs(), "gestante": True, "itu_alta": True},
            expected_results={
                "rule_t2_itu_alta_gestante_cefazolina": T,
                "rule_t2_itu_alta_gestante_piperacilina": F,
                "rule_t2_itu_alta_gestante_meropenem": F,
            },
        ),
        "tc_t2_alta_piperacilina": TestCase(
            id="tc_t2_alta_piperacilina",
            inputs={
                "gestante": True,
                "itu_alta": True,
                "antibioticos_ultimos_90dias": True,
                "choque_septico": False,
            },
            expected_results={
                "rule_t2_itu_alta_gestante_cefazolina": F,
                "rule_t2_itu_alta_gestante_piperacilina": T,
                "rule_t2_itu_alta_gestante_meropenem": F,
            },
        ),
        "tc_t2_alta_meropenem": TestCase(
            id="tc_t2_alta_meropenem",
            inputs={
                "gestante": True,
                "itu_alta": True,
                "colonizacion_blee": True,
                "choque_septico": True,
            },
            expected_results={
                "rule_t2_itu_alta_gestante_cefazolina": F,
                "rule_t2_itu_alta_gestante_piperacilina": F,
                "rule_t2_itu_alta_gestante_meropenem": T,
            },
        ),
        "tc_t2_preventiva_baja_recurrencia": TestCase(
            id="tc_t2_preventiva_baja_recurrencia",
            inputs={"gestante": True, "itu_baja": True, "recurrencia_itu": True},
            expected_results={"rule_t2_preventiva_baja": T},
        ),
        "tc_t2_preventiva_baja_sin_recurrencia": TestCase(
            id="tc_t2_preventiva_baja_sin_recurrencia",
            inputs={"gestante": True, "itu_baja": True, "recurrencia_itu": False},
            expected_results={"rule_t2_preventiva_baja": F},
        ),
        "tc_t2_preventiva_alta": TestCase(
            id="tc_t2_preventiva_alta",
            inputs={"gestante": True, "itu_alta": True},
            expected_results={"rule_t2_preventiva_alta": T},
        ),
    }


def main(argv: list[str] | None = None) -> None:
    """Regenerate the serialized package artifact from the builder."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("usage: python -m cpg_tree.protocols.itu_v06 <output-package.yaml>")
    target = Path(args[0])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_package(build_itu_package()), encoding="utf-8")


if __name__ == "__main__":
    main()
