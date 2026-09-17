# ruff: noqa: TRY004
"""NAC CT-PL-193 v09 knowledge package builder.

Authoritative protocol-specific knowledge for the institutional protocol
"PROTOCOLO DE PRÁCTICA CLÍNICA DE NEUMONÍA ADQUIRIDA EN COMUNIDAD"
(code CT-PL-193, version 9, approved 12-ago-2024, adult patients).

This module is the single source of truth for the NAC knowledge package.
``build_nac_package`` constructs the ProtocolVersion; the serialized YAML
artifact under ``protocols/CT-PL-193/v09/package.yaml`` is generated from it
and must never be edited independently.

Every variable, rule, action, and validation item carries provenance anchored
to fine-grained fragments of the extracted source document
(doc-3a1654757801b7b6, sha256 3a165475...). Known source gaps (the empty
"TRATAMIENTO ANTIBIÓTICO EMPÍRICO" section, image-only algorithms, undefined
CURB-65 calculation) remain explicit UNRESOLVED items and are never
reconstructed from general medical knowledge.

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

DOCUMENT_ID = "doc-3a1654757801b7b6"
SHA256 = "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882"
SOURCE_FILENAME = (
    "CT-PL-193 PROTOCOLO PRACTICA CLINICA NEUMONIA ADQUIRIDA EN COMUNIDAD "
    "-NAC (v9-ago-2024) (5).pdf"
)
SOURCE_BYTE_SIZE = 1089336

T = TruthValue.TRUE
F = TruthValue.FALSE
U = TruthValue.UNKNOWN

EXTRACTED = ValidationStatus.EXTRACTED
UNRESOLVED_STATUS = ValidationStatus.UNRESOLVED


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


def _variable(
    variable_id: str,
    label: str,
    variable_type: VariableType,
    provenance: Provenance,
    *,
    unit: str | None = None,
    description: str | None = None,
    validation_status: ValidationStatus = EXTRACTED,
) -> Variable:
    variable = Variable(
        id=variable_id,
        label=label,
        type=variable_type,
        unit=unit,
        description=description,
        provenance=provenance,
    )
    _VARIABLE_STATUS[variable_id] = validation_status
    return variable


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


def _and(*operands: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(operator=LogicalOperator.AND, operands=operands)


def _or(*operands: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(operator=LogicalOperator.OR, operands=operands)


def _not(operand: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(operator=LogicalOperator.NOT, operands=(operand,))


def _at_least_n(threshold: int, *operands: LogicalOperand) -> LogicalExpression:
    return LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        operands=operands,
        threshold=threshold,
    )


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
    return Action(id=action_id, type=action_type, label=label, payload=payload, provenance=provenance)


def _rule(
    rule_id: str,
    condition: LogicalOperand,
    provenance: Provenance,
    *,
    action_refs: tuple[str, ...] = (),
    applies_to: LogicalOperand | None = None,
    validation_status: ValidationStatus = EXTRACTED,
    notes: str | None = None,
) -> Rule:
    return Rule(
        id=rule_id,
        condition=condition,
        action_refs=action_refs,
        provenance=provenance,
        applies_to=applies_to,
        validation_status=validation_status,
        notes=notes,
    )


_VARIABLE_STATUS: dict[str, ValidationStatus] = {}


def build_nac_package() -> ProtocolVersion:
    """Build the complete NAC CT-PL-193 v09 knowledge package."""
    _VARIABLE_STATUS.clear()

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
    rules = _build_rules(expressions, variables)
    validation_items = _build_validation_items(fragments, variables, rules)
    test_cases = _build_test_cases()

    return ProtocolVersion(
        protocol=Protocol(
            id="CT-PL-193",
            name="Protocolo de práctica clínica de neumonía adquirida en comunidad",
            description="Atención de pacientes adultos con diagnóstico de neumonía adquirida en comunidad",
        ),
        version="v09",
        approval_date="2024-08-12",
        change_summary=(
            "Actualización del protocolo institucional para manejo de neumonía adquirida "
            "en comunidad en pacientes adultos, indicaciones de pruebas moleculares, "
            "tratamiento empírico según factores de riesgo y algoritmo de diagnóstico "
            "y tratamiento"
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
    fragments = {
        "frag_p1_metadata": _fragment(
            "frag_p1_metadata",
            1,
            "PROTOCOLO",
            "PROTOCOLO DE PRÁCTICA CLÍNICA DE NEUMONÍA ADQUIRIDA EN COMUNIDAD "
            "Proceso: Cuidado y tratamiento Código: CT-PL-193 Versión: 9 "
            "Fecha aprobación: 12-ago-2024",
        ),
        "frag_p1_definicion_nac": _fragment(
            "frag_p1_definicion_nac",
            1,
            "PROTOCOLO",
            "La neumonía adquirida en comunidad (NAC) es aquella que se presenta en "
            "aparicion de sintomas respiratorios y/o sintomas generales, asociados a "
            "alteración en un estudio radiológico del pulmón sin otras causas evidentes, "
            "en pacientes no hospitalizados o aquellos hospitalizados en quienes los "
            "sintomas o signos de infeccion se presentan dentro de las primeras 48 horas "
            "de su ingreso hospitalario",
        ),
        "frag_p3_rx_torax": _fragment(
            "frag_p3_rx_torax",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "El diagnóstico de neumonía se basa en un cuadro clínico compatible asociado "
            "a un infiltrado pulmonar de reciente aparición en la radiografía de tórax que "
            "muestre al menos uno de los siguientes hallazgos: Infiltrados alveolares o "
            "intersticiales segmentarios o infiltrados en uno o más lóbulos y que no estaban "
            "presentes previamente. La radiografía de tórax se hará en los pacientes con "
            "signos y síntomas respiratorios bajos (tos, expec toración, dolor pleurítico, "
            "taquipnea, disnea, desaturación y/o alteraciones auscultatorias compatibles).",
        ),
        "frag_p3_rx_repetir": _fragment(
            "frag_p3_rx_repetir",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "En el caso que la radiografía inicial no muestre hallazgos pero exista una "
            "sospecha alta de neumonía debe repetirse la radiografía de tórax en 48 horas.",
        ),
        "frag_p3_tc": _fragment(
            "frag_p3_tc",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Tomografía de tórax (IIA): Sólo está indicada en pacientes con alta pro "
            "babilidad de neumonía por clínica, con radiografía de tórax no concluyente y "
            "en quien es prioritario hacer el diagnóstico de neumonía o se sospeche alguna "
            "complicación (neumonía necro sante, absceso pulmonar o empiema tabicado).",
        ),
        "frag_p3_tc_neutropenia": _fragment(
            "frag_p3_tc_neutropenia",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "En los casos de neutropenia febril se solicitará tomografía de tórax simple "
            "en todos los pacientes con sintomas respiratorios bajos.",
        ),
        "frag_p3_labs_sospecha": _fragment(
            "frag_p3_labs_sospecha",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Para definir la necesidad de hospitalización, se hará hemoleucograma y "
            "nitrógeno ureico en todo paciente con so specha de neumonía.",
        ),
        "frag_p3_labs_hospitalizacion": _fragment(
            "frag_p3_labs_hospitalizacion",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "En pacientes con indicación de hospitalización se adicionarán: proteína C "
            "reactiva, creatinina, lactato y sodio.",
        ),
        "frag_p3_labs_shock": _fragment(
            "frag_p3_labs_shock",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "En pacientes con choque séptico, sepsis grave o falla orgánica múltiple se "
            "realizarán además pruebas de coagulación, AST, A LT, bilirrubinas y gases "
            "arteriales.",
        ),
        "frag_p3_labs_gases_desaturacion": _fragment(
            "frag_p3_labs_gases_desaturacion",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "También se solicitarán gases arteriales en pacientes con desaturación.",
        ),
        "frag_p3_labs_derrame": _fragment(
            "frag_p3_labs_derrame",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "En pacientes con derrame pleural e indicación de toracentesis se solicitarán "
            "además deshidrogenasa láctica y proteínas totales en suero para la adecuada "
            "interpretación de los hallazgos en el líquido pleural",
        ),
        "frag_p3_hemocultivos": _fragment(
            "frag_p3_hemocultivos",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Deben tomarse en los pacientes hospitalizados por neumonía que presenten una "
            "de las siguientes condiciones, nitrógeno ureico en sangre (BUN) mayor a 30 "
            "mg/dL, Proteína C Reactiva (PCR) mayor a 15 mg/dL o Leucocitosis mayor a "
            "15000; o en los pacientes que presenten dos de las siguientes condiciones : "
            "Presión Arterial Diastólica menor a 60 mmHg, Frecuencia Cardiaca mayor a 120 "
            "lpm, Frecuencia Respiratoria mayor a 30 rpm o Dolor Pleu rítico.",
        ),
        "frag_p3_esputo_gram": _fragment(
            "frag_p3_esputo_gram",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Deben obtenerse muestras de esputo para tinción y cultivo en todo paciente "
            "con diagnóstico de neumonía e indicación de hospitalización.",
        ),
        "frag_p3_esputo_inducido": _fragment(
            "frag_p3_esputo_inducido",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Se tomará la muestra por esputo inducido por nebulización de 15-20 minutos "
            "con solución salina hipertónica (3%) en pacientes que no pueden recoger la "
            "muestra de forma espontánea.",
        ),
        "frag_p3_esputo_calidad": _fragment(
            "frag_p3_esputo_calidad",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Se define una muestra de esputo de buena calidad cuando tiene < de 10 células "
            "epiteliales y más de 25 leucocitos por campo.",
        ),
        "frag_p3_filmarray": _fragment(
            "frag_p3_filmarray",
            3,
            "1. RECOMENDACIONES PARA EL DIAGNÓSTICO",
            "Filmarray: Prueba de ácidos nucleicos diseñada para la detección rápida y "
            "simultánea de virus y bacterias respiratorias, el cual se debe solicitar en "
            "todo paciente adulto con diagnóstico confirmado de neumonía e indicación de "
            "hospitalización.",
        ),
        "frag_p4_panel_profundo": _fragment(
            "frag_p4_panel_profundo",
            4,
            "2. RECOMENDACIONES PARA EL MANEJO",
            "Diagnóstico molecular para panel de neumonía filmarray (cod 502828): como "
            "primera opción. Muestra tomada de esputo, aspirado traqueal o lavado "
            "broncoalveolar en pacientes sin sospecha de neumonia por SARSCOV2.",
        ),
        "frag_p4_panel_hisopado": _fragment(
            "frag_p4_panel_hisopado",
            4,
            "2. RECOMENDACIONES PARA EL MANEJO",
            "Diagnóstico molecular para patógenos respiratorios (cod 502162): muestra "
            "tomada de hisopado nasofaríngeo en pacientes que no espectoran.",
        ),
        "frag_p4_liquido_pleural": _fragment(
            "frag_p4_liquido_pleural",
            4,
            "2. RECOMENDACIONES PARA EL MANEJO",
            "Todo paciente con derrame pleural de presunto origen paraneumónico (derrame "
            "pleural unilateral de más de 1 centímetro de espesor sin una causa aparente), "
            "debe ser llevado a toracentesis diagnóstica.",
        ),
        "frag_p4_hosp_01": _fragment(
            "frag_p4_hosp_01", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Paciente con descompensación de enfermedad de base",
        ),
        "frag_p4_hosp_02": _fragment(
            "frag_p4_hosp_02", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Pacientes inmunosuprimidos",
        ),
        "frag_p4_hosp_03": _fragment(
            "frag_p4_hosp_03", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Sospecha de gérmenes resistentes",
        ),
        "frag_p4_hosp_04": _fragment(
            "frag_p4_hosp_04", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Intolerancia a la vía oral",
        ),
        "frag_p4_hosp_05": _fragment(
            "frag_p4_hosp_05", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Sepsis o choque de origen pulmonar",
        ),
        "frag_p4_hosp_06": _fragment(
            "frag_p4_hosp_06", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Compromiso multilobar o derrame pleural en los rayos X de tórax",
        ),
        "frag_p4_hosp_07": _fragment(
            "frag_p4_hosp_07", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Escala de severidad CURB-65 ≥2",
        ),
        "frag_p4_hosp_08": _fragment(
            "frag_p4_hosp_08", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Factores sociales que afecten el cumplimiento y seguimiento del tratamiento",
        ),
        "frag_p4_hosp_09": _fragment(
            "frag_p4_hosp_09", 4, "2. RECOMENDACIONES PARA EL MANEJO",
            "Requerimiento de oxigeno suplementario",
        ),
        "frag_p4_uci_bullet1": _fragment(
            "frag_p4_uci_bullet1",
            4,
            "2. RECOMENDACIONES PARA EL MANEJO",
            "Insuficiencia respiratoria, choque séptico o lactato sérico mayor de 2, "
            "falla renal aguda que requiere terapia de reemplazo renal o falla orgánica "
            "multisistémica.",
        ),
        "frag_p4_uci_3de": _fragment(
            "frag_p4_uci_3de",
            4,
            "2. RECOMENDACIONES PARA EL MANEJO",
            "Paciente que cumpla con 3 o más criterios de: - BUN > 30 - FR > 30 - "
            "Hipotensión que requiera LEV agresivos - Infiltrados multilobares - "
            "PaO2/FiO2 menores de 250 - Confusión - Hipotermia - Plaquetas menor de "
            "100.000 - Leucocitos menor de 4000",
        ),
        "frag_p4_tratamiento_heading": _fragment(
            "frag_p4_tratamiento_heading",
            4,
            "2. RECOMENDACIONES PARA EL MANEJO",
            "TRATAMIENTO ANTIBIÓTICO EMPÍRICO:",
        ),
        "frag_p5_plan_egreso": _fragment(
            "frag_p5_plan_egreso",
            5,
            None,
            "Se dará de alta el paciente cuando lleve 48 horas afebril, estable en su "
            "condicion hemodinamica (Presion arterial sistolica > 90mmHg, frecuencia "
            "cardiaca <100, frecuencia respiratoria <24, saturación de oxígeno mayor de "
            "90, PO2 mayor de 60), tolere la vía oral, las comorbilidades estén "
            "compensadas, se asegure la administración de tratamiento antibiótico "
            "ambulatorio y las condiciones sociales lo permitan.",
        ),
        "frag_p6_alta_instrucciones": _fragment(
            "frag_p6_alta_instrucciones",
            6,
            None,
            "Al momento del alta se indicarán al paciente los signos y síntomas que "
            "sugieren recaída de la infección, específicamente fiebre, disnea, dolor "
            "torácico. Se dará cita de revisión con medicina interna a las 4 semanas del "
            "alta.",
        ),
        "frag_p6_algoritmos": _fragment(
            "frag_p6_algoritmos",
            6,
            "ALGORITMOS DE DIAGNÓSTICO Y MANEJO",
            "ALGORITMOS DE DIAGNÓSTICO Y MANEJO:",
        ),
        "frag_p7_control_cambios_v09": _fragment(
            "frag_p7_control_cambios_v09",
            7,
            "CONTROL CAMBIOS",
            "09 12-ago-2024 Actualización del protocolo institucional para manejo de "
            "neumonía adquirida en comunidad en pacientes adultos, indicaciones de "
            "pruebas moleculares, tratamiento empírico según factores de riesgo y "
            "algoritmo de diagnóstico y tratamiento",
        ),
    }
    return fragments


def _build_variables() -> dict[str, Variable]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED
    u = DerivationState.UNRESOLVED
    return {
        "hospitalizado": _variable(
            "hospitalizado", "Hospitalizado", VariableType.BOOLEAN,
            _prov(s, ("frag_p1_definicion_nac",)),
            description="Paciente hospitalizado al momento de la evaluación.",
        ),
        "sintomas_dentro_48h_ingreso": _variable(
            "sintomas_dentro_48h_ingreso", "Síntomas dentro de las primeras 48 horas del ingreso",
            VariableType.BOOLEAN, _prov(s, ("frag_p1_definicion_nac",)),
        ),
        "sintomas_respiratorios_generales": _variable(
            "sintomas_respiratorios_generales", "Síntomas respiratorios y/o síntomas generales",
            VariableType.BOOLEAN, _prov(s, ("frag_p1_definicion_nac",)),
        ),
        "alteracion_radiologica": _variable(
            "alteracion_radiologica", "Alteración en un estudio radiológico del pulmón",
            VariableType.BOOLEAN, _prov(s, ("frag_p1_definicion_nac",)),
        ),
        "sin_otras_causas_evidentes": _variable(
            "sin_otras_causas_evidentes", "Sin otras causas evidentes",
            VariableType.BOOLEAN, _prov(s, ("frag_p1_definicion_nac",)),
            description="Juicio clínico; el documento no lo operacionaliza.",
        ),
        "cuadro_clinico_compatible": _variable(
            "cuadro_clinico_compatible", "Cuadro clínico compatible",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_rx_torax",)),
        ),
        "infiltrado_reciente_rx": _variable(
            "infiltrado_reciente_rx", "Infiltrado pulmonar de reciente aparición en radiografía de tórax",
            VariableType.BOOLEAN, _prov(n, ("frag_p3_rx_torax",),
                notes="Colapsa la lista 'al menos uno de los siguientes hallazgos: infiltrados "
                "alveolares o intersticiales segmentarios o infiltrados en uno o más lóbulos no "
                "presentes previamente' en una única variable booleana."),
        ),
        "signos_sintomas_respiratorios_bajos": _variable(
            "signos_sintomas_respiratorios_bajos", "Signos y síntomas respiratorios bajos",
            VariableType.BOOLEAN, _prov(n, ("frag_p3_rx_torax",),
                notes="Colapsa la lista '(tos, expectoración, dolor pleurítico, taquipnea, disnea, "
                "desaturación y/o alteraciones auscultatorias compatibles)'."),
        ),
        "rx_inicial_sin_hallazgos": _variable(
            "rx_inicial_sin_hallazgos", "Radiografía inicial sin hallazgos",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_rx_repetir",)),
        ),
        "sospecha_alta_neumonia": _variable(
            "sospecha_alta_neumonia", "Sospecha alta de neumonía",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_rx_repetir",)),
        ),
        "alta_probabilidad_neumonia": _variable(
            "alta_probabilidad_neumonia", "Alta probabilidad de neumonía por clínica",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_tc",)),
        ),
        "rx_no_concluyente": _variable(
            "rx_no_concluyente", "Radiografía de tórax no concluyente",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_tc",)),
        ),
        "prioritario_diagnostico": _variable(
            "prioritario_diagnostico", "Prioritario hacer el diagnóstico de neumonía",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_tc",)),
        ),
        "sospecha_complicacion": _variable(
            "sospecha_complicacion", "Sospecha de complicación",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_tc",)),
            description="Neumonía necrosante, absceso pulmonar o empiema tabicado.",
        ),
        "neutropenia_febril": _variable(
            "neutropenia_febril", "Neutropenia febril",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_tc_neutropenia",)),
        ),
        "sospecha_neumonia": _variable(
            "sospecha_neumonia", "Sospecha de neumonía",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_labs_sospecha",)),
        ),
        "diagnostico_neumonia": _variable(
            "diagnostico_neumonia", "Diagnóstico de neumonía",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_esputo_gram",)),
        ),
        "diagnostico_confirmado_neumonia": _variable(
            "diagnostico_confirmado_neumonia", "Diagnóstico confirmado de neumonía",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_filmarray",)),
        ),
        "descompensacion_enfermedad_base": _variable(
            "descompensacion_enfermedad_base", "Descompensación de enfermedad de base",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_01",)),
        ),
        "inmunosuprimido": _variable(
            "inmunosuprimido", "Paciente inmunosuprimido",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_02",)),
        ),
        "sospecha_germenes_resistentes": _variable(
            "sospecha_germenes_resistentes", "Sospecha de gérmenes resistentes",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_03",)),
        ),
        "intolerancia_via_oral": _variable(
            "intolerancia_via_oral", "Intolerancia a la vía oral",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_04",)),
        ),
        "sepsis_origen_pulmonar": _variable(
            "sepsis_origen_pulmonar", "Sepsis de origen pulmonar",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_05",)),
        ),
        "choque_origen_pulmonar": _variable(
            "choque_origen_pulmonar", "Choque de origen pulmonar",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_05",)),
        ),
        "compromiso_multilobar": _variable(
            "compromiso_multilobar", "Compromiso multilobar",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_06",)),
            description="Criterio de hospitalización; concepto distinto de 'infiltrados "
            "multilobares' de UCI-UCE.",
        ),
        "derrame_pleural_rx": _variable(
            "derrame_pleural_rx", "Derrame pleural en los rayos X de tórax",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_06",)),
        ),
        "curb65_score": _variable(
            "curb65_score", "Escala de severidad CURB-65",
            VariableType.NUMERIC, _prov(u, ("frag_p4_hosp_07",),
                notes="La fuente referencia la escala sin definir componentes ni cálculo; el "
                "puntaje es un dato externo."),
            description="El documento no define los componentes ni el cálculo de la escala.",
            validation_status=UNRESOLVED_STATUS,
        ),
        "factores_sociales": _variable(
            "factores_sociales", "Factores sociales que afecten cumplimiento y seguimiento",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_08",)),
        ),
        "requerimiento_oxigeno_suplementario": _variable(
            "requerimiento_oxigeno_suplementario", "Requerimiento de oxígeno suplementario",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_hosp_09",)),
        ),
        "insuficiencia_respiratoria": _variable(
            "insuficiencia_respiratoria", "Insuficiencia respiratoria",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_bullet1",)),
        ),
        "choque_septico": _variable(
            "choque_septico", "Choque séptico",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_bullet1", "frag_p3_labs_shock")),
        ),
        "lactato_serico": _variable(
            "lactato_serico", "Lactato sérico", VariableType.NUMERIC,
            _prov(n, ("frag_p4_uci_bullet1",),
                notes="Umbral 'mayor de 2' sin unidad declarada en la fuente."),
        ),
        "falla_renal_aguda_trr": _variable(
            "falla_renal_aguda_trr", "Falla renal aguda que requiere terapia de reemplazo renal",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_bullet1",)),
        ),
        "falla_organica_multiple": _variable(
            "falla_organica_multiple", "Falla orgánica múltiple",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_labs_shock",)),
            description="Término de la sección de laboratorio; distinto de 'falla orgánica "
            "multisistémica' de UCI-UCE.",
        ),
        "falla_organica_multisistemica": _variable(
            "falla_organica_multisistemica", "Falla orgánica multisistémica",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_bullet1",)),
        ),
        "sepsis_grave": _variable(
            "sepsis_grave", "Sepsis grave",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_labs_shock",)),
        ),
        "bun": _variable(
            "bun", "Nitrógeno ureico en sangre (BUN)", VariableType.NUMERIC,
            _prov(n, ("frag_p3_hemocultivos", "frag_p4_uci_3de"),
                notes="Unidad mg/dL declarada en la sección de hemocultivos."),
            unit="mg/dL",
        ),
        "fr_respiratoria": _variable(
            "fr_respiratoria", "Frecuencia respiratoria", VariableType.NUMERIC,
            _prov(n, ("frag_p3_hemocultivos", "frag_p4_uci_3de", "frag_p5_plan_egreso"),
                notes="Unidad rpm declarada en la sección de hemocultivos."),
            unit="rpm",
        ),
        "hipotension_requiere_lev": _variable(
            "hipotension_requiere_lev", "Hipotensión que requiera LEV agresivos",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_3de",)),
        ),
        "infiltrados_multilobares": _variable(
            "infiltrados_multilobares", "Infiltrados multilobares",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_3de",)),
            description="Criterio de UCI-UCE; concepto distinto de 'compromiso multilobar' "
            "de hospitalización.",
        ),
        "pao2_fio2": _variable(
            "pao2_fio2", "PaO2/FiO2", VariableType.NUMERIC,
            _prov(n, ("frag_p4_uci_3de",),
                notes="Umbral 'menores de 250' sin unidad declarada en la fuente."),
        ),
        "confusion": _variable(
            "confusion", "Confusión",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_3de",)),
        ),
        "hipotermia": _variable(
            "hipotermia", "Hipotermia",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_uci_3de",)),
        ),
        "plaquetas": _variable(
            "plaquetas", "Plaquetas", VariableType.NUMERIC,
            _prov(n, ("frag_p4_uci_3de",),
                notes="Umbral 'menor de 100.000' sin unidad declarada en la fuente."),
        ),
        "leucocitos": _variable(
            "leucocitos", "Leucocitos", VariableType.NUMERIC,
            _prov(n, ("frag_p3_hemocultivos", "frag_p4_uci_3de"),
                notes="Umbrales 'mayor a 15000' y 'menor de 4000' sin unidad declarada en la fuente."),
        ),
        "pcr": _variable(
            "pcr", "Proteína C reactiva (PCR)", VariableType.NUMERIC,
            _prov(n, ("frag_p3_hemocultivos",), notes="Umbral 'mayor a 15 mg/dL'."),
            unit="mg/dL",
        ),
        "pad": _variable(
            "pad", "Presión arterial diastólica", VariableType.NUMERIC,
            _prov(n, ("frag_p3_hemocultivos",), notes="Umbral 'menor a 60 mmHg'."),
            unit="mmHg",
        ),
        "fc": _variable(
            "fc", "Frecuencia cardiaca", VariableType.NUMERIC,
            _prov(n, ("frag_p3_hemocultivos", "frag_p5_plan_egreso"),
                notes="Umbrales 'mayor a 120 lpm' y '<100' (alta)."),
            unit="lpm",
        ),
        "dolor_pleuritico": _variable(
            "dolor_pleuritico", "Dolor pleurítico",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_hemocultivos",)),
        ),
        "no_puede_recoger_muestra_espontanea": _variable(
            "no_puede_recoger_muestra_espontanea", "No puede recoger la muestra de forma espontánea",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_esputo_inducido",)),
        ),
        "celulas_epiteliales_campo": _variable(
            "celulas_epiteliales_campo", "Células epiteliales por campo", VariableType.NUMERIC,
            _prov(n, ("frag_p3_esputo_calidad",), notes="Umbral '< de 10' por campo."),
        ),
        "leucocitos_campo": _variable(
            "leucocitos_campo", "Leucocitos por campo", VariableType.NUMERIC,
            _prov(n, ("frag_p3_esputo_calidad",), notes="Umbral 'más de 25' por campo."),
        ),
        "sin_sospecha_sarscov2": _variable(
            "sin_sospecha_sarscov2", "Sin sospecha de neumonía por SARSCOV2",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_panel_profundo",)),
        ),
        "no_expectora": _variable(
            "no_expectora", "No expectora",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_panel_hisopado",)),
        ),
        "derrame_pleural_unilateral": _variable(
            "derrame_pleural_unilateral", "Derrame pleural unilateral",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_liquido_pleural",)),
        ),
        "espesor_derrame_cm": _variable(
            "espesor_derrame_cm", "Espesor del derrame pleural", VariableType.NUMERIC,
            _prov(n, ("frag_p4_liquido_pleural",),
                notes="Umbral 'más de 1 centímetro de espesor'."),
            unit="cm",
        ),
        "sin_causa_aparente": _variable(
            "sin_causa_aparente", "Sin causa aparente",
            VariableType.BOOLEAN, _prov(s, ("frag_p4_liquido_pleural",)),
        ),
        "desaturacion": _variable(
            "desaturacion", "Desaturación",
            VariableType.BOOLEAN, _prov(s, ("frag_p3_labs_gases_desaturacion",)),
        ),
        "afebril_horas": _variable(
            "afebril_horas", "Horas afebril", VariableType.DURATION,
            _prov(n, ("frag_p5_plan_egreso",),
                notes="Duración del estado afebril en horas; umbral 'lleve 48 horas afebril'."),
            unit="hours",
        ),
        "pas_sistolica": _variable(
            "pas_sistolica", "Presión arterial sistólica", VariableType.NUMERIC,
            _prov(n, ("frag_p5_plan_egreso",), notes="Umbral '> 90mmHg'."),
            unit="mmHg",
        ),
        "saturacion_oxigeno": _variable(
            "saturacion_oxigeno", "Saturación de oxígeno", VariableType.NUMERIC,
            _prov(n, ("frag_p5_plan_egreso",), notes="Umbral 'mayor de 90'."),
            unit="%",
        ),
        "po2": _variable(
            "po2", "PO2", VariableType.NUMERIC,
            _prov(n, ("frag_p5_plan_egreso",), notes="Umbral 'mayor de 60' sin unidad declarada."),
        ),
        "tolera_via_oral": _variable(
            "tolera_via_oral", "Tolera la vía oral",
            VariableType.BOOLEAN, _prov(s, ("frag_p5_plan_egreso",)),
        ),
        "comorbilidades_compensadas": _variable(
            "comorbilidades_compensadas", "Comorbilidades compensadas",
            VariableType.BOOLEAN, _prov(s, ("frag_p5_plan_egreso",)),
        ),
        "tratamiento_antibiotico_ambulatorio_asegurado": _variable(
            "tratamiento_antibiotico_ambulatorio_asegurado",
            "Administración de tratamiento antibiótico ambulatorio asegurada",
            VariableType.BOOLEAN, _prov(s, ("frag_p5_plan_egreso",)),
        ),
        "condiciones_sociales_adecuadas": _variable(
            "condiciones_sociales_adecuadas", "Condiciones sociales lo permiten",
            VariableType.BOOLEAN, _prov(s, ("frag_p5_plan_egreso",)),
        ),
    }


def _build_actions() -> dict[str, Action]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED
    return {
        "act_rx_torax": _action(
            "act_rx_torax", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_rx_torax",)),
        ),
        "act_rx_torax_repetida_48h": _action(
            "act_rx_torax_repetida_48h", ActionType.REQUEST_TEST,
            _prov(n, ("frag_p3_rx_repetir",),
                notes="El intervalo de 48 horas es dato declarativo del payload."),
            payload={"intervalo_horas": 48},
        ),
        "act_tc_torax": _action(
            "act_tc_torax", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_tc",)),
        ),
        "act_hemoleucograma": _action(
            "act_hemoleucograma", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_sospecha",)),
        ),
        "act_bun": _action(
            "act_bun", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_labs_sospecha",)),
        ),
        "act_pcr": _action(
            "act_pcr", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_hospitalizacion",)),
        ),
        "act_creatinina": _action(
            "act_creatinina", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_hospitalizacion",)),
        ),
        "act_lactato": _action(
            "act_lactato", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_hospitalizacion",)),
        ),
        "act_sodio": _action(
            "act_sodio", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_hospitalizacion",)),
        ),
        "act_coagulacion": _action(
            "act_coagulacion", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_labs_shock",)),
        ),
        "act_ast": _action(
            "act_ast", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_labs_shock",)),
        ),
        "act_alt": _action(
            "act_alt", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_labs_shock",)),
        ),
        "act_bilirrubinas": _action(
            "act_bilirrubinas", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_labs_shock",)),
        ),
        "act_gases_arteriales": _action(
            "act_gases_arteriales", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_shock", "frag_p3_labs_gases_desaturacion")),
        ),
        "act_ldh": _action(
            "act_ldh", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_labs_derrame",)),
        ),
        "act_proteinas_sericas": _action(
            "act_proteinas_sericas", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_labs_derrame",)),
        ),
        "act_toracentesis_diagnostica": _action(
            "act_toracentesis_diagnostica", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p4_liquido_pleural",)),
        ),
        "act_hemocultivos": _action(
            "act_hemocultivos", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_hemocultivos",)),
        ),
        "act_gram_cultivo_esputo": _action(
            "act_gram_cultivo_esputo", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_esputo_gram",)),
        ),
        "act_esputo_inducido": _action(
            "act_esputo_inducido", ActionType.REQUEST_TEST,
            _prov(s, ("frag_p3_esputo_inducido",)),
        ),
        "act_filmarray": _action(
            "act_filmarray", ActionType.REQUEST_TEST, _prov(s, ("frag_p3_filmarray",)),
        ),
        "act_hospitalizar": _action(
            "act_hospitalizar", ActionType.ADMIT,
            _prov(n, ("frag_p4_hosp_01", "frag_p4_hosp_02", "frag_p4_hosp_03",
                      "frag_p4_hosp_04", "frag_p4_hosp_05", "frag_p4_hosp_06",
                      "frag_p4_hosp_07", "frag_p4_hosp_08", "frag_p4_hosp_09"),
                notes="Consecuencia de la lista de indicaciones de hospitalización."),
        ),
        "act_uci_uce": _action(
            "act_uci_uce", ActionType.ADMIT,
            _prov(n, ("frag_p4_uci_bullet1", "frag_p4_uci_3de"),
                notes="Consecuencia de las indicaciones de ingreso a UCI-UCE."),
            payload={"destino": "UCI-UCE"},
        ),
        "act_egreso": _action(
            "act_egreso", ActionType.DISCHARGE, _prov(s, ("frag_p5_plan_egreso",)),
        ),
        "act_educar_recaida": _action(
            "act_educar_recaida", ActionType.EDUCATE,
            _prov(s, ("frag_p6_alta_instrucciones",)),
            label="Signos de recaída: fiebre, disnea, dolor torácico",
        ),
        "act_cita_revision_4_semanas": _action(
            "act_cita_revision_4_semanas", ActionType.FOLLOW_UP,
            _prov(n, ("frag_p6_alta_instrucciones",),
                notes="Cita de revisión a las 4 semanas del alta; dato declarativo del payload."),
            payload={"semanas": 4},
        ),
    }


def _build_expressions() -> dict[str, Any]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED

    hosp_limb_descompensacion = _flag("descompensacion_enfermedad_base")
    hosp_limb_inmunosupresion = _flag("inmunosuprimido")
    hosp_limb_germenes = _flag("sospecha_germenes_resistentes")
    hosp_limb_intolerancia = _flag("intolerancia_via_oral")
    hosp_limb_sepsis_choque = _or(_flag("sepsis_origen_pulmonar"), _flag("choque_origen_pulmonar"))
    hosp_limb_multilobar_derrame = _or(_flag("compromiso_multilobar"), _flag("derrame_pleural_rx"))
    hosp_limb_curb65 = _ge("curb65_score", 2)
    hosp_limb_sociales = _flag("factores_sociales")
    hosp_limb_oxigeno = _flag("requerimiento_oxigeno_suplementario")

    hospitalization = _or(
        hosp_limb_descompensacion,
        hosp_limb_inmunosupresion,
        hosp_limb_germenes,
        hosp_limb_intolerancia,
        hosp_limb_sepsis_choque,
        hosp_limb_multilobar_derrame,
        hosp_limb_curb65,
        hosp_limb_sociales,
        hosp_limb_oxigeno,
    )

    c_bun_gt30 = _gt("bun", 30)
    c_fr_gt30 = _gt("fr_respiratoria", 30)
    c_pcr_gt15 = _gt("pcr", 15)
    c_leucocitos_gt15000 = _gt("leucocitos", 15000)
    c_pad_lt60 = _lt("pad", 60)
    c_fc_gt120 = _gt("fc", 120)
    c_dolor_pleuritico = _flag("dolor_pleuritico")

    hemocultivos_condition = _or(
        _or(c_bun_gt30, c_pcr_gt15, c_leucocitos_gt15000),
        _at_least_n(2, c_pad_lt60, c_fc_gt120, c_fr_gt30, c_dolor_pleuritico),
    )

    toracentesis_expression = _and(
        _flag("derrame_pleural_unilateral"),
        _gt("espesor_derrame_cm", 1),
        _flag("sin_causa_aparente"),
    )

    uci_criterion_bun = c_bun_gt30
    uci_criterion_fr = c_fr_gt30
    uci_criterion_hipotension = _flag("hipotension_requiere_lev")
    uci_criterion_multilobares = _flag("infiltrados_multilobares")
    uci_criterion_pao2_fio2 = _lt("pao2_fio2", 250)
    uci_criterion_confusion = _flag("confusion")
    uci_criterion_hipotermia = _flag("hipotermia")
    uci_criterion_plaquetas = _lt("plaquetas", 100000)
    uci_criterion_leucocitos = _lt("leucocitos", 4000)

    uci_three_de = _at_least_n(
        3,
        uci_criterion_bun,
        uci_criterion_fr,
        uci_criterion_hipotension,
        uci_criterion_multilobares,
        uci_criterion_pao2_fio2,
        uci_criterion_confusion,
        uci_criterion_hipotermia,
        uci_criterion_plaquetas,
        uci_criterion_leucocitos,
    )

    uci_bullet1 = _or(
        _flag("insuficiencia_respiratoria"),
        _flag("choque_septico"),
        _gt("lactato_serico", 2),
        _flag("falla_renal_aguda_trr"),
        _flag("falla_organica_multisistemica"),
    )

    egreso = _and(
        _temporal("afebril_horas", 48, "hours"),
        _gt("pas_sistolica", 90),
        _lt("fc", 100),
        _lt("fr_respiratoria", 24),
        _gt("saturacion_oxigeno", 90),
        _gt("po2", 60),
        _flag("tolera_via_oral"),
        _flag("comorbilidades_compensadas"),
        _flag("tratamiento_antibiotico_ambulatorio_asegurado"),
        _flag("condiciones_sociales_adecuadas"),
    )

    return {
        "s": s,
        "n": n,
        "hospitalization": hospitalization,
        "hosp_limbs": {
            "descompensacion": hosp_limb_descompensacion,
            "inmunosupresion": hosp_limb_inmunosupresion,
            "germenes": hosp_limb_germenes,
            "intolerancia": hosp_limb_intolerancia,
            "sepsis_choque": hosp_limb_sepsis_choque,
            "multilobar_derrame": hosp_limb_multilobar_derrame,
            "curb65": hosp_limb_curb65,
            "sociales": hosp_limb_sociales,
            "oxigeno": hosp_limb_oxigeno,
        },
        "hemocultivos": hemocultivos_condition,
        "toracentesis": toracentesis_expression,
        "uci_criteria": {
            "bun": uci_criterion_bun,
            "fr": uci_criterion_fr,
            "hipotension": uci_criterion_hipotension,
            "multilobares": uci_criterion_multilobares,
            "pao2_fio2": uci_criterion_pao2_fio2,
            "confusion": uci_criterion_confusion,
            "hipotermia": uci_criterion_hipotermia,
            "plaquetas": uci_criterion_plaquetas,
            "leucocitos": uci_criterion_leucocitos,
        },
        "uci_three_de": uci_three_de,
        "uci_bullet1": uci_bullet1,
        "uci_composite": _or(uci_bullet1, uci_three_de),
        "egreso": egreso,
    }


def _build_rules(
    expressions: dict[str, Any],
    variables: dict[str, Variable],
) -> dict[str, Rule]:
    s = DerivationState.SOURCE_STATED
    n = DerivationState.NORMALIZED
    hospitalization = expressions["hospitalization"]
    hosp_limbs = expressions["hosp_limbs"]
    uci_criteria = expressions["uci_criteria"]
    filmarray_population = _and(
        _flag("diagnostico_confirmado_neumonia"), hospitalization
    )
    gram_population = _and(_flag("diagnostico_neumonia"), hospitalization)

    curb65_prov = _prov(
        DerivationState.UNRESOLVED,
        ("frag_p4_hosp_07",),
        notes="El enunciado 'CURB-65 ≥2' es explícito, pero la fuente no define los "
        "componentes ni el cálculo de la escala; el puntaje es un dato externo.",
    )

    return {
        "rule_definicion_nac": _rule(
            "rule_definicion_nac",
            _and(
                _flag("sintomas_respiratorios_generales"),
                _flag("alteracion_radiologica"),
                _flag("sin_otras_causas_evidentes"),
                _or(_not(_flag("hospitalizado")), _flag("sintomas_dentro_48h_ingreso")),
            ),
            _prov(n, ("frag_p1_definicion_nac",),
                notes="Definición operativa de NAC ensamblada desde la frase de DEFINICIONES."),
        ),
        "rule_diagnostico_radiografico": _rule(
            "rule_diagnostico_radiografico",
            _and(_flag("cuadro_clinico_compatible"), _flag("infiltrado_reciente_rx")),
            _prov(n, ("frag_p3_rx_torax",),
                notes="Criterio diagnóstico ensamblado: cuadro clínico compatible + "
                "infiltrado de reciente aparición."),
        ),
        "rule_rx_torax_indicada": _rule(
            "rule_rx_torax_indicada",
            _flag("signos_sintomas_respiratorios_bajos"),
            _prov(n, ("frag_p3_rx_torax",),
                notes="Indicación de radiografía en pacientes con signos y síntomas "
                "respiratorios bajos."),
            action_refs=("act_rx_torax",),
        ),
        "rule_rx_repetir_48h": _rule(
            "rule_rx_repetir_48h",
            _and(_flag("rx_inicial_sin_hallazgos"), _flag("sospecha_alta_neumonia")),
            _prov(n, ("frag_p3_rx_repetir",),
                notes="Repetir radiografía en 48 horas; el intervalo es dato declarativo."),
            action_refs=("act_rx_torax_repetida_48h",),
        ),
        "rule_tc_torax": _rule(
            "rule_tc_torax",
            _and(
                _flag("alta_probabilidad_neumonia"),
                _flag("rx_no_concluyente"),
                _or(_flag("prioritario_diagnostico"), _flag("sospecha_complicacion")),
            ),
            _prov(n, ("frag_p3_tc",),
                notes="Indicación de tomografía ensamblada desde 'Sólo está indicada en...'."),
            action_refs=("act_tc_torax",),
        ),
        "rule_tc_neutropenia_febril": _rule(
            "rule_tc_neutropenia_febril",
            _and(_flag("neutropenia_febril"), _flag("signos_sintomas_respiratorios_bajos")),
            _prov(n, ("frag_p3_tc_neutropenia",), notes="Tomografía simple en neutropenia febril."),
            action_refs=("act_tc_torax",),
        ),
        "rule_labs_sospecha": _rule(
            "rule_labs_sospecha",
            _flag("sospecha_neumonia"),
            _prov(n, ("frag_p3_labs_sospecha",), notes="Laboratorios basales ante sospecha."),
            action_refs=("act_hemoleucograma", "act_bun"),
        ),
        "rule_labs_hospitalizacion": _rule(
            "rule_labs_hospitalizacion",
            hospitalization,
            _prov(n, ("frag_p3_labs_hospitalizacion",),
                notes="Laboratorios adicionales en pacientes con indicación de hospitalización; "
                "la indicación se computa con la misma expresión del criterio de hospitalización."),
            action_refs=("act_pcr", "act_creatinina", "act_lactato", "act_sodio"),
        ),
        "rule_labs_shock": _rule(
            "rule_labs_shock",
            _or(_flag("choque_septico"), _flag("sepsis_grave"), _flag("falla_organica_multiple")),
            _prov(n, ("frag_p3_labs_shock",), notes="Laboratorios en choque séptico, sepsis grave "
                "o falla orgánica múltiple."),
            action_refs=("act_coagulacion", "act_ast", "act_alt", "act_bilirrubinas",
                         "act_gases_arteriales"),
        ),
        "rule_labs_desaturacion": _rule(
            "rule_labs_desaturacion",
            _flag("desaturacion"),
            _prov(n, ("frag_p3_labs_gases_desaturacion",), notes="Gases arteriales en desaturación."),
            action_refs=("act_gases_arteriales",),
        ),
        "rule_labs_derrame_pleural": _rule(
            "rule_labs_derrame_pleural",
            _and(_flag("derrame_pleural_rx"), expressions["toracentesis"]),
            _prov(n, ("frag_p3_labs_derrame", "frag_p4_liquido_pleural"),
                notes="LDH y proteínas séricas cuando hay derrame pleural e indicación de "
                "toracentesis; la indicación se computa con la misma expresión del criterio "
                "paraneumónico."),
            action_refs=("act_ldh", "act_proteinas_sericas"),
        ),
        "rule_toracentesis_paraneumonico": _rule(
            "rule_toracentesis_paraneumonico",
            expressions["toracentesis"],
            _prov(n, ("frag_p4_liquido_pleural",),
                notes="Criterio paraneumónico: unilateral, más de 1 cm, sin causa aparente."),
            action_refs=("act_toracentesis_diagnostica",),
        ),
        "rule_hemocultivos": _rule(
            "rule_hemocultivos",
            expressions["hemocultivos"],
            _prov(n, ("frag_p3_hemocultivos",),
                notes="Uno de: BUN>30, PCR>15, leucocitosis>15000; o dos de: PAD<60, FC>120, "
                "FR>30, dolor pleurítico. La fuente agrega 'antes de la primera dosis "
                "intravenosa de antibióticos' (restricción de procedimiento, no representable)."),
            applies_to=hospitalization,
            action_refs=("act_hemocultivos",),
        ),
        "rule_gram_cultivo_esputo": _rule(
            "rule_gram_cultivo_esputo",
            gram_population,
            _prov(n, ("frag_p3_esputo_gram",), notes="Esputo para Gram y cultivo."),
            action_refs=("act_gram_cultivo_esputo",),
        ),
        "rule_esputo_inducido": _rule(
            "rule_esputo_inducido",
            _and(gram_population, _flag("no_puede_recoger_muestra_espontanea")),
            _prov(n, ("frag_p3_esputo_inducido",),
                notes="Esputo inducido por nebulización 15-20 min con solución salina "
                "hipertónica (3%) cuando no pueden recoger la muestra espontáneamente."),
            action_refs=("act_esputo_inducido",),
        ),
        "rule_esputo_buena_calidad": _rule(
            "rule_esputo_buena_calidad",
            _and(_lt("celulas_epiteliales_campo", 10), _gt("leucocitos_campo", 25)),
            _prov(n, ("frag_p3_esputo_calidad",), notes="Definición de muestra de buena calidad."),
        ),
        "rule_filmarray": _rule(
            "rule_filmarray",
            _flag("diagnostico_confirmado_neumonia"),
            _prov(n, ("frag_p3_filmarray",), notes="Solicitud de panel molecular."),
            applies_to=filmarray_population,
            action_refs=("act_filmarray",),
        ),
        "rule_filmarray_panel_profundo": _rule(
            "rule_filmarray_panel_profundo",
            _flag("sin_sospecha_sarscov2"),
            _prov(s, ("frag_p4_panel_profundo",)),
            applies_to=filmarray_population,
            notes="Primera opción: cod 502828, muestra profunda (esputo, aspirado traqueal o "
            "lavado broncoalveolar). Sin acción: el paquete no selecciona ni ejecuta paneles.",
        ),
        "rule_filmarray_panel_hisopado": _rule(
            "rule_filmarray_panel_hisopado",
            _flag("no_expectora"),
            _prov(s, ("frag_p4_panel_hisopado",)),
            applies_to=filmarray_population,
            notes="cod 502162, hisopado nasofaríngeo en pacientes que no espectoran. Sin "
            "acción: el paquete no selecciona ni ejecuta paneles.",
        ),
        "rule_hosp_criterio_descompensacion": _rule(
            "rule_hosp_criterio_descompensacion", hosp_limbs["descompensacion"],
            _prov(s, ("frag_p4_hosp_01",)),
        ),
        "rule_hosp_criterio_inmunosupresion": _rule(
            "rule_hosp_criterio_inmunosupresion", hosp_limbs["inmunosupresion"],
            _prov(s, ("frag_p4_hosp_02",)),
        ),
        "rule_hosp_criterio_germenes_resistentes": _rule(
            "rule_hosp_criterio_germenes_resistentes", hosp_limbs["germenes"],
            _prov(s, ("frag_p4_hosp_03",)),
        ),
        "rule_hosp_criterio_intolerancia_oral": _rule(
            "rule_hosp_criterio_intolerancia_oral", hosp_limbs["intolerancia"],
            _prov(s, ("frag_p4_hosp_04",)),
        ),
        "rule_hosp_criterio_sepsis_choque": _rule(
            "rule_hosp_criterio_sepsis_choque", hosp_limbs["sepsis_choque"],
            _prov(s, ("frag_p4_hosp_05",)),
        ),
        "rule_hosp_criterio_multilobar_derrame": _rule(
            "rule_hosp_criterio_multilobar_derrame", hosp_limbs["multilobar_derrame"],
            _prov(s, ("frag_p4_hosp_06",)),
        ),
        "rule_hosp_criterio_curb65": _rule(
            "rule_hosp_criterio_curb65",
            hosp_limbs["curb65"],
            curb65_prov,
            validation_status=UNRESOLVED_STATUS,
        ),
        "rule_hosp_criterio_factores_sociales": _rule(
            "rule_hosp_criterio_factores_sociales", hosp_limbs["sociales"],
            _prov(s, ("frag_p4_hosp_08",)),
        ),
        "rule_hosp_criterio_oxigeno": _rule(
            "rule_hosp_criterio_oxigeno", hosp_limbs["oxigeno"],
            _prov(s, ("frag_p4_hosp_09",)),
        ),
        "rule_hospitalizacion": _rule(
            "rule_hospitalizacion",
            hospitalization,
            _prov(n, ("frag_p4_hosp_01", "frag_p4_hosp_02", "frag_p4_hosp_03",
                      "frag_p4_hosp_04", "frag_p4_hosp_05", "frag_p4_hosp_06",
                      "frag_p4_hosp_07", "frag_p4_hosp_08", "frag_p4_hosp_09"),
                notes="Composición OR de las nueve indicaciones de hospitalización."),
            action_refs=("act_hospitalizar",),
        ),
        "rule_uci_criterio_bun": _rule(
            "rule_uci_criterio_bun", uci_criteria["bun"], _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_fr": _rule(
            "rule_uci_criterio_fr", uci_criteria["fr"], _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_hipotension_lev": _rule(
            "rule_uci_criterio_hipotension_lev", uci_criteria["hipotension"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_multilobares": _rule(
            "rule_uci_criterio_multilobares", uci_criteria["multilobares"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_pao2_fio2": _rule(
            "rule_uci_criterio_pao2_fio2", uci_criteria["pao2_fio2"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_confusion": _rule(
            "rule_uci_criterio_confusion", uci_criteria["confusion"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_hipotermia": _rule(
            "rule_uci_criterio_hipotermia", uci_criteria["hipotermia"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_plaquetas": _rule(
            "rule_uci_criterio_plaquetas", uci_criteria["plaquetas"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterio_leucocitos": _rule(
            "rule_uci_criterio_leucocitos", uci_criteria["leucocitos"],
            _prov(s, ("frag_p4_uci_3de",)),
        ),
        "rule_uci_criterios_3de": _rule(
            "rule_uci_criterios_3de",
            expressions["uci_three_de"],
            _prov(n, ("frag_p4_uci_3de",),
                notes="'3 o más criterios de' representado como AT_LEAST_N(3, 9 criterios)."),
        ),
        "rule_uci_bullet1": _rule(
            "rule_uci_bullet1",
            expressions["uci_bullet1"],
            _prov(DerivationState.INFERRED, ("frag_p4_uci_bullet1",),
                notes="Interpretación estructural de la coma: OR de cinco alternativas "
                "(insuficiencia respiratoria; choque séptico; lactato > 2; FRA con TRR; "
                "falla orgánica multisistémica)."),
        ),
        "rule_ingreso_uci_uce": _rule(
            "rule_ingreso_uci_uce",
            expressions["uci_composite"],
            _prov(n, ("frag_p4_uci_bullet1", "frag_p4_uci_3de"),
                notes="Composición OR del primer criterio y del criterio de 3 o más."),
            action_refs=("act_uci_uce",),
        ),
        "rule_plan_egreso": _rule(
            "rule_plan_egreso",
            expressions["egreso"],
            _prov(n, ("frag_p5_plan_egreso", "frag_p6_alta_instrucciones"),
                notes="Criterios de alta ensamblados; las instrucciones de recaída y la cita "
                "de 4 semanas son acciones declarativas asociadas al alta ('al momento del "
                "alta' aproximado por MATCHED de esta regla)."),
            action_refs=("act_egreso", "act_educar_recaida", "act_cita_revision_4_semanas"),
        ),
    }


def _build_validation_items(
    fragments: dict[str, SourceFragment],
    variables: dict[str, Variable],
    rules: dict[str, Rule],
) -> dict[str, ValidationItem]:
    open_status = ValidationItemStatus.OPEN
    return {
        "vi_tratamiento_empirico_gap": ValidationItem(
            id="vi_tratamiento_empirico_gap",
            category="gap",
            description="La página 4 termina en el encabezado 'TRATAMIENTO ANTIBIÓTICO "
            "EMPÍRICO:' sin contenido y sin imágenes en las páginas 4 y 5; el control de "
            "cambios de la versión 9 menciona 'tratamiento empírico según factores de "
            "riesgo'. El contenido no está disponible en la capa de texto extraída y no se "
            "reconstruye.",
            severity="high",
            related_ids=("frag_p4_tratamiento_heading", "frag_p7_control_cambios_v09"),
            status=open_status,
        ),
        "vi_algoritmos_imagen": ValidationItem(
            id="vi_algoritmos_imagen",
            category="gap",
            description="La página 6 contiene el encabezado 'ALGORITMOS DE DIAGNÓSTICO Y "
            "MANEJO:' seguido de una imagen embebida no extraíble como texto; los algoritmos "
            "no se representan ni se reconstruyen.",
            severity="high",
            related_ids=("frag_p6_algoritmos",),
            status=open_status,
        ),
        "vi_curb65_componentes": ValidationItem(
            id="vi_curb65_componentes",
            category="unresolved",
            description="La fuente referencia 'Escala de severidad CURB-65 ≥2' sin definir "
            "los componentes ni el cálculo de la escala; curb65_score se modela como dato "
            "externo no computable desde la fuente.",
            severity="high",
            related_ids=("curb65_score", "rule_hosp_criterio_curb65"),
            status=open_status,
        ),
        "vi_filmarray_seleccion_panel": ValidationItem(
            id="vi_filmarray_seleccion_panel",
            category="limitation",
            description="Las indicaciones de panel (502828 sin sospecha SARSCOV2; 502162 en "
            "quienes no expectoran) pueden satisfacerse simultáneamente; el modelo canónico "
            "no tiene semántica de selección/exclusividad y la fuente no provee lógica "
            "explícita para resolverlo. Las reglas de panel son declarativas y sin acciones.",
            severity="medium",
            related_ids=("rule_filmarray_panel_profundo", "rule_filmarray_panel_hisopado"),
            status=open_status,
        ),
        "vi_definicion_nac_operacionalizacion": ValidationItem(
            id="vi_definicion_nac_operacionalizacion",
            category="ambiguity",
            description="Componentes de la definición de NAC ('sin otras causas evidentes', "
            "'síntomas respiratorios y/o generales') son juicios clínicos que la fuente no "
            "operacionaliza; se representan como banderas booleanas directas.",
            severity="low",
            related_ids=("rule_definicion_nac", "sin_otras_causas_evidentes"),
            status=open_status,
        ),
        "vi_uci_bullet1_parsing": ValidationItem(
            id="vi_uci_bullet1_parsing",
            category="ambiguity",
            description="El agrupamiento por comas del primer criterio de UCI-UCE se "
            "interpretó como OR de cinco alternativas; la interpretación está documentada "
            "en la procedencia de rule_uci_bullet1.",
            severity="low",
            related_ids=("rule_uci_bullet1",),
            status=open_status,
        ),
        "vi_temporal_no_representable": ValidationItem(
            id="vi_temporal_no_representable",
            category="limitation",
            description="El intervalo 'repetir radiografía en 48 horas', la 'cita de revisión "
            "a las 4 semanas' y el vínculo 'al momento del alta' son programaciones futuras "
            "que la semántica temporal mínima (duraciones numéricas) no representa; se "
            "transportan como datos declarativos en payloads y notas.",
            severity="low",
            related_ids=("rule_rx_repetir_48h", "rule_plan_egreso"),
            status=open_status,
        ),
        "vi_unidades_no_declaradas": ValidationItem(
            id="vi_unidades_no_declaradas",
            category="ambiguity",
            description="La fuente no declara unidades para lactato sérico, plaquetas, "
            "leucocitos, PO2 y PaO2/FiO2; las unidades se dejan ausentes en el modelo.",
            severity="low",
            related_ids=("lactato_serico", "plaquetas", "leucocitos", "po2", "pao2_fio2"),
            status=open_status,
        ),
    }


def _build_test_cases() -> dict[str, TestCase]:
    hosp_flag_ids = (
        "descompensacion_enfermedad_base",
        "inmunosuprimido",
        "sospecha_germenes_resistentes",
        "intolerancia_via_oral",
        "sepsis_origen_pulmonar",
        "choque_origen_pulmonar",
        "compromiso_multilobar",
        "derrame_pleural_rx",
        "factores_sociales",
        "requerimiento_oxigeno_suplementario",
    )

    def hosp_inputs(curb65: Scalar = 0, **overrides: Scalar) -> dict[str, Scalar]:
        inputs: dict[str, Scalar] = {key: False for key in hosp_flag_ids}
        inputs["curb65_score"] = curb65
        inputs.update(overrides)
        return inputs

    uci_flag_ids = (
        "insuficiencia_respiratoria",
        "choque_septico",
        "falla_renal_aguda_trr",
        "falla_organica_multisistemica",
        "hipotension_requiere_lev",
        "confusion",
        "hipotermia",
    )

    def uci_inputs(**overrides: Scalar) -> dict[str, Scalar]:
        inputs: dict[str, Scalar] = {key: False for key in uci_flag_ids}
        inputs.update(
            {
                "lactato_serico": 0,
                "bun": 20,
                "fr_respiratoria": 20,
                "infiltrados_multilobares": False,
                "pao2_fio2": 300,
                "plaquetas": 200000,
                "leucocitos": 8000,
            }
        )
        inputs.update(overrides)
        return inputs

    def hemo_inputs(**overrides: Scalar) -> dict[str, Scalar]:
        inputs = hosp_inputs()
        inputs.update(
            {
                "bun": 20,
                "pcr": 5,
                "leucocitos": 8000,
                "pad": 70,
                "fc": 80,
                "fr_respiratoria": 20,
                "dolor_pleuritico": False,
            }
        )
        inputs.update(overrides)
        return inputs

    def egreso_inputs(**overrides: Scalar) -> dict[str, Scalar]:
        inputs: dict[str, Scalar] = {
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
        inputs.update(overrides)
        return inputs

    return {
        "tc_hosp_curb65_boundary": TestCase(
            id="tc_hosp_curb65_boundary",
            inputs=hosp_inputs(curb65=2),
            expected_results={
                "rule_hosp_criterio_curb65": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_curb65_below": TestCase(
            id="tc_hosp_curb65_below",
            inputs=hosp_inputs(curb65=1),
            expected_results={
                "rule_hosp_criterio_curb65": F,
                "rule_hospitalizacion": F,
            },
        ),
        "tc_hosp_none": TestCase(
            id="tc_hosp_none",
            inputs=hosp_inputs(),
            expected_results={"rule_hospitalizacion": F},
        ),
        "tc_hosp_multilobar": TestCase(
            id="tc_hosp_multilobar",
            inputs=hosp_inputs(compromiso_multilobar=True),
            expected_results={
                "rule_hosp_criterio_multilobar_derrame": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_choque_pulmonar": TestCase(
            id="tc_hosp_choque_pulmonar",
            inputs=hosp_inputs(choque_origen_pulmonar=True),
            expected_results={
                "rule_hosp_criterio_sepsis_choque": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_sepsis_pulmonar": TestCase(
            id="tc_hosp_sepsis_pulmonar",
            inputs=hosp_inputs(sepsis_origen_pulmonar=True),
            expected_results={
                "rule_hosp_criterio_sepsis_choque": T,
                "rule_hospitalizacion": T,
            },
        ),
        "tc_hosp_missing_curb65": TestCase(
            id="tc_hosp_missing_curb65",
            inputs=hosp_inputs(curb65=None),
            expected_results={
                "rule_hospitalizacion": U,
                "rule_labs_hospitalizacion": U,
            },
        ),
        "tc_uci_3_criterios": TestCase(
            id="tc_uci_3_criterios",
            inputs=uci_inputs(
                bun=31,
                fr_respiratoria=31,
                infiltrados_multilobares=True,
                compromiso_multilobar=False,
                derrame_pleural_rx=False,
            ),
            expected_results={
                "rule_uci_criterio_bun": T,
                "rule_uci_criterio_fr": T,
                "rule_uci_criterio_multilobares": T,
                "rule_hosp_criterio_multilobar_derrame": F,
                "rule_uci_criterios_3de": T,
                "rule_ingreso_uci_uce": T,
            },
        ),
        "tc_uci_2_criterios": TestCase(
            id="tc_uci_2_criterios",
            inputs=uci_inputs(bun=31, fr_respiratoria=31),
            expected_results={
                "rule_uci_criterios_3de": F,
                "rule_ingreso_uci_uce": F,
            },
        ),
        "tc_uci_2_plus_unknown": TestCase(
            id="tc_uci_2_plus_unknown",
            inputs=uci_inputs(bun=31, fr_respiratoria=31, hipotermia=None),
            expected_results={
                "rule_uci_criterios_3de": U,
                "rule_ingreso_uci_uce": U,
            },
        ),
        "tc_uci_bullet1_lactato": TestCase(
            id="tc_uci_bullet1_lactato",
            inputs=uci_inputs(lactato_serico=2.5),
            expected_results={
                "rule_uci_bullet1": T,
                "rule_ingreso_uci_uce": T,
            },
        ),
        "tc_uci_lactato_equal_2": TestCase(
            id="tc_uci_lactato_equal_2",
            inputs=uci_inputs(lactato_serico=2),
            expected_results={
                "rule_uci_bullet1": F,
                "rule_ingreso_uci_uce": F,
            },
        ),
        "tc_hemo_or_single": TestCase(
            id="tc_hemo_or_single",
            inputs=hemo_inputs(inmunosuprimido=True, bun=31),
            expected_results={"rule_hemocultivos": T},
        ),
        "tc_hemo_2of4": TestCase(
            id="tc_hemo_2of4",
            inputs=hemo_inputs(inmunosuprimido=True, pad=55, fc=121),
            expected_results={"rule_hemocultivos": T},
        ),
        "tc_hemo_1of4": TestCase(
            id="tc_hemo_1of4",
            inputs=hemo_inputs(inmunosuprimido=True, pad=55),
            expected_results={"rule_hemocultivos": F},
        ),
        "tc_hemo_no_hosp": TestCase(
            id="tc_hemo_no_hosp",
            inputs=hemo_inputs(),
            expected_results={"rule_hemocultivos": F},
        ),
        "tc_hemo_hosp_unknown": TestCase(
            id="tc_hemo_hosp_unknown",
            inputs=hemo_inputs(curb65_score=None),
            expected_results={"rule_hemocultivos": U},
        ),
        "tc_egreso_completo_48": TestCase(
            id="tc_egreso_completo_48",
            inputs=egreso_inputs(),
            expected_results={"rule_plan_egreso": T},
        ),
        "tc_egreso_afebril_47": TestCase(
            id="tc_egreso_afebril_47",
            inputs=egreso_inputs(afebril_horas=47),
            expected_results={"rule_plan_egreso": F},
        ),
        "tc_egreso_pas_90": TestCase(
            id="tc_egreso_pas_90",
            inputs=egreso_inputs(pas_sistolica=90),
            expected_results={"rule_plan_egreso": F},
        ),
        "tc_egreso_missing_po2": TestCase(
            id="tc_egreso_missing_po2",
            inputs=egreso_inputs(po2=None),
            expected_results={"rule_plan_egreso": U},
        ),
        "tc_rx_repetir": TestCase(
            id="tc_rx_repetir",
            inputs={"rx_inicial_sin_hallazgos": True, "sospecha_alta_neumonia": True},
            expected_results={"rule_rx_repetir_48h": T},
        ),
        "tc_pleural_1cm": TestCase(
            id="tc_pleural_1cm",
            inputs={
                "derrame_pleural_unilateral": True,
                "espesor_derrame_cm": 1.0,
                "sin_causa_aparente": True,
                "derrame_pleural_rx": False,
            },
            expected_results={
                "rule_toracentesis_paraneumonico": F,
                "rule_labs_derrame_pleural": F,
            },
        ),
        "tc_pleural_1p2cm": TestCase(
            id="tc_pleural_1p2cm",
            inputs={
                "derrame_pleural_unilateral": True,
                "espesor_derrame_cm": 1.2,
                "sin_causa_aparente": True,
                "derrame_pleural_rx": True,
            },
            expected_results={
                "rule_toracentesis_paraneumonico": T,
                "rule_labs_derrame_pleural": T,
            },
        ),
        "tc_gram_sin_dx": TestCase(
            id="tc_gram_sin_dx",
            inputs={**hosp_inputs(), "diagnostico_neumonia": False},
            expected_results={"rule_gram_cultivo_esputo": F},
        ),
        "tc_filmarray_profundo": TestCase(
            id="tc_filmarray_profundo",
            inputs={
                **hosp_inputs(inmunosuprimido=True),
                "diagnostico_confirmado_neumonia": True,
                "sin_sospecha_sarscov2": True,
                "no_expectora": False,
            },
            expected_results={
                "rule_filmarray": T,
                "rule_filmarray_panel_profundo": T,
                "rule_filmarray_panel_hisopado": F,
            },
        ),
        "tc_filmarray_overlap": TestCase(
            id="tc_filmarray_overlap",
            inputs={
                **hosp_inputs(inmunosuprimido=True),
                "diagnostico_confirmado_neumonia": True,
                "sin_sospecha_sarscov2": True,
                "no_expectora": True,
            },
            expected_results={
                "rule_filmarray": T,
                "rule_filmarray_panel_profundo": T,
                "rule_filmarray_panel_hisopado": T,
            },
        ),
        "tc_definicion_nac_comunidad": TestCase(
            id="tc_definicion_nac_comunidad",
            inputs={
                "hospitalizado": False,
                "sintomas_dentro_48h_ingreso": False,
                "sintomas_respiratorios_generales": True,
                "alteracion_radiologica": True,
                "sin_otras_causas_evidentes": True,
            },
            expected_results={"rule_definicion_nac": T},
        ),
        "tc_definicion_nac_48h": TestCase(
            id="tc_definicion_nac_48h",
            inputs={
                "hospitalizado": True,
                "sintomas_dentro_48h_ingreso": True,
                "sintomas_respiratorios_generales": True,
                "alteracion_radiologica": True,
                "sin_otras_causas_evidentes": True,
            },
            expected_results={"rule_definicion_nac": T},
        ),
        "tc_definicion_nac_tardio": TestCase(
            id="tc_definicion_nac_tardio",
            inputs={
                "hospitalizado": True,
                "sintomas_dentro_48h_ingreso": False,
                "sintomas_respiratorios_generales": True,
                "alteracion_radiologica": True,
                "sin_otras_causas_evidentes": True,
            },
            expected_results={"rule_definicion_nac": F},
        ),
    }


def main(argv: list[str] | None = None) -> None:
    """Regenerate the serialized package artifact from the builder."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("usage: python -m cpg_tree.protocols.nac_v09 <output-package.yaml>")
    target = Path(args[0])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_package(build_nac_package()), encoding="utf-8")


if __name__ == "__main__":
    main()
