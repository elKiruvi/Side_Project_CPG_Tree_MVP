# Clinical Decision Tree — CT-PL-193 v09 (NAC)

Protocol metadata:

| | |
|---|---|
| Protocol | CT-PL-193 — Protocolo de práctica clínica de neumonía adquirida en comunidad |
| Version | v09 |
| Approval date | 2024-08-12 |
| Population | Atención de pacientes adultos con diagnóstico de neumonía adquirida en comunidad |
| Source document | `doc-3a1654757801b7b6` — CT-PL-193 … NAC (v9-ago-2024).pdf, 7 páginas |
| Canonical rules | 42 |
| FLOW relationships (D2.5 reconciliadas) | 9 |
| Disconnected components | 3 componentes conectados + 30 reglas sin conexión FLOW |

> **Nota de lectura.** Este documento es una representación de presentación de las
> relaciones reconciliadas en D2.5 (`evaluation/pathway/CT-PL-193-v09-reconciliation.yaml`).
> Solo las relaciones FLOW reconciliadas aparecen como transiciones entre reglas.
> Las relaciones REFERENCE, COMPOSITION, INTERNAL, GAP, CONFLICT e INFERRED **no**
> se dibujan como flujo clínico. No se descubrió ni infirió ninguna relación nueva.
> Prototipo de investigación; no es consejo clínico.

## Notation

| Símbolo | Significado |
|---|---|
| `[FLOW]` | Transición de presentación reconciliada en D2.5 con evidencia de fuente |
| `⚠️ UNRESOLVED` | La fuente no permite establecer el contenido/umbral; no tratado como validado |
| `⚠️ CONFLICT` | Evidencia fuente en conflicto; sin ganador elegido |
| `⚠️ INFERRED` | Estructura inferida durante la reconciliación; nunca flujo validado |
| `⚠️ GAP` | Evidencia insuficiente o contenido ausente de la fuente |
| `⚪ UNKNOWN` | Semántica del motor: información faltante → INDETERMINATE (nunca FALSE) |
| `(pN)` | Página del documento fuente |

---

# 1. Clinical Decision Tree

El grafo reconciliado de NAC tiene **3 componentes conectados** (las reglas sin
FLOW aparecen en la sección 5; no se fabricaron conectores).

## Component 1 — Radiografía de tórax → seguimiento

```
                        ┌────────────────────────────────────────────┐
                        │ rule_rx_torax_indicada                     │
                        │ Condición: signos y síntomas respiratorios │
                        │ bajos                                     │
                        │ Acción: act_rx_torax (REQUEST_TEST)       │
                        │ Fuente: frag_p3_rx_torax (p3) · NORMALIZED│
                        └───────────────┬────────────┬───────────────┘
                                        │            │
                     [FLOW] RX inicial  │            │  [FLOW] RX no concluyente
                     sin hallazgos +    │            │  + alta probabilidad
                     sospecha alta      │            │
                                        ▼            ▼
                    ┌───────────────────────────┐  ┌───────────────────────────────┐
                    │ rule_rx_repetir_48h       │  │ rule_tc_torax                 │
                    │ Condición: RX sin         │  │ Condición: alta probabilidad  │
                    │ hallazgos + sospecha alta │  │ + RX no concluyente +         │
                    │ Acción: repetir RX        │  │ prioritario/complicación      │
                    │ (intervalo 48 h: dato     │  │ Acción: act_tc_torax          │
                    │ declarativo)              │  │ Fuente: frag_p3_tc (p3)       │
                    │ Fuente: frag_p3_rx_repetir│  └───────────────────────────────┘
                    │ (p3)                      │
                    └───────────────────────────┘
```

## Component 2 — Definición de la necesidad de hospitalización

```
        ┌───────────────────────────────────────────────┐
        │ rule_labs_sospecha                            │
        │ Condición: sospecha de neumonía               │
        │ Acción: hemoleucograma + BUN                  │
        │ Fuente: frag_p3_labs_sospecha (p3)            │
        └───────────────────────┬───────────────────────┘
                                │
              [FLOW] apoya la decisión de hospitalización
              (no es una secuencia temporal estricta)
                                │
                                ▼
        ┌───────────────────────────────────────────────┐
        │ rule_hospitalizacion                          │
        │ Condición: OR de 9 criterios de               │
        │ hospitalización (ver §5, criterios 1–9)       │
        │ Acción: act_hospitalizar (ADMIT)              │
        │ Fuente: frag_p4_hosp_01…09 (p4)               │
        └───┬───────────┬───────────┬───────────┬───────┘
            │           │           │           │
[FLOW]      │ [FLOW]    │ [FLOW]    │ [FLOW]    │
indicación  │ hospitali-│ dx + indi-│ dx confir- │
de hospita- │ zado por  │ cación de │ mado +     │
lización    │ neumonía  │ hospitali-│ indicación │
            │           │ zación    │ de hosp.   │
            ▼           ▼           ▼           ▼
  ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐
  │ rule_labs_hospitalizacion│ │ rule_hemocultivos        │ │ rule_gram_cultivo_esputo│
  │ Acción: PCR, creatinina, │ │ Condición: hospitalizado │ │ Condición: dx de        │
  │ lactato, sodio           │ │ por neumonía + 1 de 3 o  │ │ neumonía + indicación   │
  │ Fuente:                  │ │ 2 de 4 criterios         │ │ de hospitalización      │
  │ frag_p3_labs_hospitaliza-│ │ Acción: act_hemocultivos │ │ Acción: tinción y       │
  │ cion (p3)                │ │ Fuente: frag_p3_hemo-    │ │ cultivo de esputo       │
  │                          │ │ cultivos (p3)            │ │ Fuente:                 │
  │                          │ │                          │ │ frag_p3_esputo_gram (p3)│
  └──────────────────────────┘ └──────────────────────────┘ └───────────┬──────────────┘
  ┌────────────────────┐
  │ rule_filmarray     │
  │ Condición: dx      │
  │ confirmado         │
  │ Acción:            │
  │ act_filmarray      │
  │ Fuente:            │
  │ frag_p3_filmarray  │
  │ (p3)               │
  └────────────────────┘
                                                          │
                                          [FLOW] no puede recoger
                                          muestra espontánea
                                                          │
                                                          ▼
                                          ┌─────────────────────────────┐
                                          │ rule_esputo_inducido        │
                                          │ Condición: dx + hospitali-  │
                                          │ zación + no recoge muestra  │
                                          │ Acción: esputo inducido     │
                                          │ Fuente: frag_p3_esputo_     │
                                          │ inducido (p3)               │
                                          └─────────────────────────────┘
```

## Component 3 — Derrame pleural paraneumónico

```
     ┌──────────────────────────────────────┐
     │ rule_toracentesis_paraneumonico      │
     │ Condición: derrame unilateral > 1 cm │
     │ sin causa aparente                   │
     │ Acción: act_toracentesis_diagnostica │
     │ Fuente: frag_p4_liquido_pleural (p4) │
     └──────────────────┬───────────────────┘
                        │
        [FLOW] derrame pleural + indicación de toracentesis
                        │
                        ▼
     ┌──────────────────────────────────────┐
     │ rule_labs_derrame_pleural            │
     │ Condición: derrame + indicación de   │
     │ toracentesis                         │
     │ Acción: LDH + proteínas séricas      │
     │ Fuente: frag_p3_labs_derrame (p3),   │
     │ frag_p4_liquido_pleural (p4)         │
     └──────────────────────────────────────┘
```

---

# 2. Branches and Clinical Alternatives

El artefacto de reconciliación de NAC **no contiene BRANCH_CONTEXT** ni terminales
de presentación. Las alternativas declaradas (p. ej., los paneles Filmarray
502828/502162) son relaciones **REFERENCE** y no se representan como ramas de flujo
(ver §5).

---

# 3. Exceptions

El paquete canónico de NAC **no contiene reglas con excepciones** (0 de 42 reglas).
No se inventaron excepciones.

---

# ⚠️ 4. Unresolved Evidence and Source Gaps

## Source conflicts (OPEN — sin ganador elegido)

| Conflict | Tema | Evidencia A (TEXT) | Evidencia B (DIAGRAM, p6) | Estado |
|---|---|---|---|---|
| SC-NAC-001 | Umbral CURB-65 de hospitalización | p4: «Escala de severidad CURB-65 ≥2» | «CURB > 2» (reportado; confirmación visual pendiente) | OPEN / UNRESOLVED |
| SC-NAC-002 | Umbral BUN en UCI-UCE | p4: «BUN > 30» | «BUN > 20» (reportado; confirmación visual pendiente) | OPEN / UNRESOLVED |
| SC-NAC-003 | Cantidad/conjunto de criterios UCI-UCE | p4: «3 o más criterios» + 9 criterios | cantidad/conjunto potencialmente distinto (reportado) | OPEN / UNRESOLVED |
| SC-NAC-004 | Presencia de «TAS < 90» en UCI-UCE | p4: el criterio NO aparece en la lista textual | «TAS < 90» presente (reportado) | OPEN / UNRESOLVED |

**Qué se requiere para resolverlos:** confirmación visual humana del flujograma de
la página 6 (imagen raster no legible por máquina en el entorno actual). No se elige
un umbral ganador; la regla canónica permanece como fue extraída.

## Extraction / representation gaps

- **`rel-nac-050` — Algoritmos de diagnóstico y manejo (p6).** El flujograma existe
  como imagen embebida (1270×976 px) entre «ALGORITMOS DE DIAGNÓSTICO Y MANEJO:» y
  «REFERENCIAS BIBLIOGRÁFICAS:»; no hay capa de texto y no se reconstruyó.
  Estado: `UNRESOLVED_MAPPING` — el mapeo a reglas canónicas queda pendiente de
  lectura visual humana. **No** se pretendió reconstruir el flujograma.

## Source content gaps

- **`rel-nac-051` — Tratamiento antibiótico empírico.** La página 4 termina en el
  encabezado «TRATAMIENTO ANTIBIÓTICO EMPÍRICO:»; las páginas 4–5 no contienen
  imágenes embebidas (inventario de objetos del PDF) y la página 5 inicia con
  «PLAN DE EGRESO». El cuerpo del tratamiento **no está presente** en este PDF:
  ausencia de contenido fuente (no limitación de extracción). El control de cambios
  v09 menciona «tratamiento empírico según factores de riesgo».
  Estado: `GAP` — no se inventó contenido de tratamiento.

## Inferred knowledge

> ⚠️ **INFERRED STRUCTURE — `rel-nac-043`**
>
> `rule_uci_bullet1` («Insuficiencia respiratoria, choque séptico o lactato sérico
> mayor de 2, …») es una sola línea en prosa con comas; su estructura OR de cinco
> alternativas es una interpretación documentada (`vi_uci_bullet1_parsing`).
> Estado: `INFERRED_STRUCTURE`. **No debe interpretarse como secuencia clínica
> autoritativa.** Se presenta únicamente con insignia de no validado.

## Otros no resueltos

- **`rel-nac-052` — CURB-65.** La fuente declara «Escala de severidad CURB-65 ≥2»
  sin definir los componentes ni el cálculo de la escala (`vi_curb65_componentes`).
  `rule_hosp_criterio_curb65` permanece ⚠️ UNRESOLVED + ⚠️ GAP; el puntaje es dato
  externo.

---

# 5. Rules Without Reconciled Flow Connection

Estas 30 reglas existen en el paquete canónico pero **no** participan en ninguna
relación FLOW reconciliada. No se fabricaron conectores. (Algunas conservan
relaciones REFERENCE/COMPOSITION/INTERNAL en la reconciliación, que son contexto,
no flujo.)

| Rule ID | Condición (resumen) | Acción | Estado / fuente |
|---|---|---|---|
| rule_definicion_nac | Síntomas respiratorios/generales + alteración radiológica + sin otras causas (no hospitalizado o <48 h) | — | NORMALIZED · frag_p1_definicion_nac (p1) · REFERENCE |
| rule_diagnostico_radiografico | Cuadro clínico compatible + infiltrado reciente en RX | — | NORMALIZED · frag_p3_rx_torax (p3) · REFERENCE |
| rule_esputo_buena_calidad | Células epiteliales <10 y leucocitos >25 por campo | — | NORMALIZED · frag_p3_esputo_calidad (p3) |
| rule_filmarray_panel_hisopado | No expectora (hisopado nasofaríngeo, cod 502162) | — (declarativa) | SOURCE_STATED · frag_p4_panel_hisopado (p4) · REFERENCE |
| rule_filmarray_panel_profundo | Sin sospecha SARS-CoV-2 («como primera opción», cod 502828) | — (declarativa) | SOURCE_STATED · frag_p4_panel_profundo (p4) · REFERENCE |
| rule_hosp_criterio_curb65 | CURB-65 ≥ 2 | — | ⚠️ UNRESOLVED ⚠️ GAP · frag_p4_hosp_07 (p4) |
| rule_hosp_criterio_descompensacion | Descompensación de enfermedad de base | — | SOURCE_STATED · frag_p4_hosp_01 (p4) · COMPOSITION |
| rule_hosp_criterio_factores_sociales | Factores sociales que afecten cumplimiento | — | SOURCE_STATED · frag_p4_hosp_08 (p4) · COMPOSITION |
| rule_hosp_criterio_germenes_resistentes | Sospecha de gérmenes resistentes | — | SOURCE_STATED · frag_p4_hosp_03 (p4) · COMPOSITION |
| rule_hosp_criterio_inmunosupresion | Paciente inmunosuprimido | — | SOURCE_STATED · frag_p4_hosp_02 (p4) · COMPOSITION |
| rule_hosp_criterio_intolerancia_oral | Intolerancia a la vía oral | — | SOURCE_STATED · frag_p4_hosp_04 (p4) · COMPOSITION |
| rule_hosp_criterio_multilobar_derrame | Compromiso multilobar o derrame pleural en RX | — | SOURCE_STATED · frag_p4_hosp_06 (p4) · COMPOSITION |
| rule_hosp_criterio_oxigeno | Requerimiento de oxígeno suplementario | — | SOURCE_STATED · frag_p4_hosp_09 (p4) · COMPOSITION |
| rule_hosp_criterio_sepsis_choque | Sepsis o choque de origen pulmonar | — | SOURCE_STATED · frag_p4_hosp_05 (p4) · COMPOSITION |
| rule_ingreso_uci_uce | OR(criterio 1; 3 o más de 9 criterios) | act_uci_uce (ADMIT) | NORMALIZED · frag_p4_uci_bullet1, frag_p4_uci_3de (p4) · ⚠️ CONFLICT ⚠️ INFERRED |
| rule_labs_desaturacion | Desaturación | Gases arteriales | NORMALIZED · frag_p3_labs_gases_desaturacion (p3) · REJECTED |
| rule_labs_shock | Choque séptico, sepsis grave o falla orgánica múltiple | Coagulación, AST, ALT, bilirrubinas, gases | NORMALIZED · frag_p3_labs_shock (p3) · REJECTED |
| rule_plan_egreso | Afebril 48 h + hemodinamia estable + vía oral + comorbilidades compensadas + tto ambulatorio + condiciones sociales | act_egreso + act_educar_recaida + act_cita_revision_4_semanas | NORMALIZED · frag_p5_plan_egreso (p5), frag_p6_alta_instrucciones (p6) · acciones INTERNAL |
| rule_tc_neutropenia_febril | Neutropenia febril + síntomas respiratorios bajos | TC de tórax | NORMALIZED · frag_p3_tc_neutropenia (p3) · REJECTED |
| rule_uci_bullet1 | Insuf. respiratoria / choque séptico / lactato >2 / FRA con TRR / falla orgánica multisistémica | — | ⚠️ INFERRED · frag_p4_uci_bullet1 (p4) |
| rule_uci_criterio_bun | BUN > 30 | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT (SC-NAC-002) |
| rule_uci_criterio_fr | FR > 30 | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT (SC-NAC-003) |
| rule_uci_criterio_hipotension_lev | Hipotensión que requiera LEV agresivos | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterio_multilobares | Infiltrados multilobares | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterio_pao2_fio2 | PaO2/FiO2 < 250 | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterio_confusion | Confusión | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterio_hipotermia | Hipotermia | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterio_plaquetas | Plaquetas < 100.000 | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterio_leucocitos | Leucocitos < 4000 | — | SOURCE_STATED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |
| rule_uci_criterios_3de | 3 o más de los 9 criterios (AT_LEAST_N) | — | NORMALIZED · frag_p4_uci_3de (p4) · ⚠️ CONFLICT |

**Notas:**

- Los 9 criterios de hospitalización (`rule_hosp_criterio_*`) y el criterio
  compuesto `rule_hospitalizacion` forman una **COMPOSITION** (OR) — estructura
  lógica, no secuencia clínica.
- `rule_plan_egreso` conserva sus acciones declarativas (educación de recaída y cita
  a 4 semanas) como relaciones **INTERNAL** (`rel-nac-016/017`): las acciones
  pertenecen a la regla y no son aristas de la vía.
- Los paneles Filmarray (`rel-nac-014/015/030`) y la definición→criterio diagnóstico
  (`rel-nac-031`) son **REFERENCE**: contexto, no flujo.
- Los criterios UCI-UCE individuales comparten evidencia (`frag_p4_uci_3de`) y están
  marcados con el conflicto SC-NAC-003; su presentación no normaliza texto y diagrama.

---
