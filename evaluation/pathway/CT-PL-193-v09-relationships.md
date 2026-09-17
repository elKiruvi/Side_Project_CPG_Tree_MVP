# CT-PL-193 v09 — Inventario de relaciones clínicas candidatas

Fase 10 (D1/D2) — evidencia para revisión humana ANTES de cualquier implementación
de vías clínicas. Ninguna fila está aprobada. `review_status` es `PROPOSED` en todas;
el revisor humano deberá cambiarla a `APPROVED`, `REJECTED` u `OMITTED`.

Documento fuente: `doc-3a1654757801b7b6` — CT-PL-193 v09 (NAC), 7 páginas.
Paquete canónico: `protocols/CT-PL-193/v09/package.yaml` (42 reglas, 35 fragmentos).
Las citas provienen de `verbatim_text` de los fragmentos del paquete y de la capa de
texto extraída (`data/02_intermediate/doc-3a1654757801b7b6/pages/`); cuando la cita
proviene de la capa de página y no de un fragmento del paquete, se indica.

**Limitaciones conocidas de la fuente (no reconstruir con conocimiento médico):**

- Página 6: «ALGORITMOS DE DIAGNÓSTICO Y MANEJO:» es una imagen embebida, no
  extraíble como texto (`vi_algoritmos_imagen`).
- Página 4: «TRATAMIENTO ANTIBIÓTICO EMPÍRICO:» es solo encabezado; el cuerpo no está
  en la capa de texto (`vi_tratamiento_empirico_gap`).
- `rule_hosp_criterio_curb65` es UNRESOLVED (la fuente no define la escala).
- `rule_uci_bullet1` es INFERRED (agrupación por comas, `vi_uci_bullet1_parsing`).

## Vocabulario

**presentation_role**

- `FLOW` — transición, rama o secuencia clínica explícita en la fuente. Único rol
  candidato a arista de árbol de decisión.
- `REFERENCE` — relación contextual entre secciones/decisiones; nunca flujo temporal.
- `COMPOSITION` — una expresión canónica contiene/combina criterios representados en
  otras reglas; estructura, no secuencia.
- `GAP` — la fuente indica información que no puede reconstruirse con la evidencia
  disponible.
- `OMITTED` — relación excluida deliberadamente (fuera de alcance, procedimental,
  ambigua o no apta para flujo explícito).

**evidence_class**

- `SOURCE_STATED` — la relación está explícita en el texto fuente.
- `EXTRACTED` — recuperable directamente de la representación fuente sin
  interpretación clínica.
- `NORMALIZED` — formato estructurado de información de la fuente.
- `INFERRED` — requiere interpretación. **Nunca** puede convertirse en arista FLOW.
- `UNRESOLVED` — no puede establecerse con la evidencia disponible.

**relation** describe la relación fuente con más detalle: `branches`, `precedes`,
`gates`, `references`, `composes`, `excepts`, `terminal`, `missing`, `outside_scope`.

## Candidatos FLOW

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-nac-001 | signos_sintomas_respiratorios_bajos (variable) | rule_rx_torax_indicada | gates | FLOW | — | «…La radiografía de tórax se hará en los pacientes con signos y síntomas respiratorios bajos (tos, expec toración, dolor pleurítico, taquipnea, disnea, desaturación y/o alteraciones auscultatorias compatibles).» | frag_p3_rx_torax | 3 | SOURCE_STATED | PROPOSED | El "from" es una variable, no una regla; el anclaje del nodo de decisión requiere decisión humana. |
| rel-nac-002 | rule_rx_torax_indicada | rule_rx_repetir_48h | branches | FLOW | — | «En el caso que la radiografía inicial no muestre hallazgos pero exista una sospecha alta de neumonía debe repetirse la radiografía de tórax en 48 horas.» | frag_p3_rx_repetir | 3 | SOURCE_STATED | PROPOSED | Condicional explícito de repetición. |
| rel-nac-003 | rule_rx_torax_indicada | rule_tc_torax | branches | FLOW | — | «Tomografía de tórax (IIA): Sólo está indicada en pacientes con alta pro babilidad de neumonía por clínica, con radiografía de tórax no concluyente y en quien es prioritario hacer el diagnóstico de neumonía o se sospeche alguna complicación (neumonía necro sante, absceso pulmonar o empiema tabicado).» | frag_p3_tc | 3 | SOURCE_STATED | PROPOSED | «radiografía de tórax no concluyente» = rama explícita. |
| rel-nac-004 | neutropenia_febril (variable) | rule_tc_neutropenia_febril | gates | FLOW | — | «En los casos de neutropenia febril se solicitará tomografía de tórax simple en todos los pacientes con sintomas respiratorios bajos.» | frag_p3_tc_neutropenia | 3 | SOURCE_STATED | PROPOSED | "from" es variable; anclaje a decidir por el revisor. |
| rel-nac-005 | rule_labs_sospecha | rule_hospitalizacion | precedes | FLOW | — | «Para definir la necesidad de hospitalización, se hará hemoleucograma y nitrógeno ureico en todo paciente con so specha de neumonía.» | frag_p3_labs_sospecha | 3 | SOURCE_STATED | PROPOSED | Propósito explícito: los exámenes alimentan la decisión de hospitalización. |
| rel-nac-006 | rule_hospitalizacion | rule_labs_hospitalizacion | gates | FLOW | — | «En pacientes con indicación de hospitalización se adicionarán: proteína C reactiva, creatinina, lactato y sodio.» | frag_p3_labs_hospitalizacion | 3 | SOURCE_STATED | PROPOSED | Condicional explícito en la redacción fuente. |
| rel-nac-007 | rule_hosp_criterio_sepsis_choque | rule_labs_shock | gates | FLOW | — | «En pacientes con choque séptico, sepsis grave o falla orgánica múltiple se realizarán además pruebas de coagulación, AST, A LT, bilirrubinas y gases arteriales.» | frag_p3_labs_shock | 3 | SOURCE_STATED | PROPOSED | Listas de disparo no idénticas entre reglas (criterio: sepsis/choque de origen pulmonar; laboratorio: choque séptico/sepsis grave/falla orgánica múltiple) — verificar anclaje. |
| rel-nac-008 | desaturacion (variable) | rule_labs_desaturacion | gates | FLOW | — | «También se solicitarán gases arteriales en pacientes con desaturación.» | frag_p3_labs_gases_desaturacion | 3 | SOURCE_STATED | PROPOSED | "from" es variable; anclaje a decidir por el revisor. |
| rel-nac-009 | rule_toracentesis_paraneumonico | rule_labs_derrame_pleural | gates | FLOW | — | «En pacientes con derrame pleural e indicación de toracentesis se solicitarán además deshidrogenasa láctica y proteínas totales en suero para la adecuada interpretación de los hallazgos en el líquido pleural» | frag_p3_labs_derrame, frag_p4_liquido_pleural | 3, 4 | SOURCE_STATED | PROPOSED | Condicional explícito sobre la indicación de toracentesis. |
| rel-nac-010 | rule_hospitalizacion | rule_hemocultivos | gates | FLOW | — | «Deben tomarse en los pacientes hospitalizados por neumonía que presenten una de las siguientes condiciones, nitrógeno ureico en sangre (BUN) mayor a 30 mg/dL, …» | frag_p3_hemocultivos | 3 | SOURCE_STATED | PROPOSED | Condicional explícito («pacientes hospitalizados por neumonía»). |
| rel-nac-011 | rule_hospitalizacion | rule_gram_cultivo_esputo | gates | FLOW | — | «Deben obtenerse muestras de esputo para tinción y cultivo en todo paciente con diagnóstico de neumonía e indicación de hospitalización.» | frag_p3_esputo_gram | 3 | SOURCE_STATED | PROPOSED | Condicional explícito. |
| rel-nac-012 | rule_gram_cultivo_esputo | rule_esputo_inducido | branches | FLOW | — | «Se tomará la muestra por esputo inducido por nebulización de 15-20 minutos con solución salina hipertónica (3%) en pacientes que no pueden recoger la muestra de forma espontánea.» | frag_p3_esputo_inducido | 3 | SOURCE_STATED | PROPOSED | Rama alternativa de toma de muestra. |
| rel-nac-013 | rule_hospitalizacion | rule_filmarray | gates | FLOW | — | «Filmarray: Prueba de ácidos nucleicos… el cual se debe solicitar en todo paciente adulto con diagnóstico confirmado de neumonía e indicación de hospitalización.» | frag_p3_filmarray | 3 | SOURCE_STATED | PROPOSED | Condicional explícito. |
| rel-nac-014 | rule_filmarray | rule_filmarray_panel_profundo | branches | FLOW | — | «Diagnóstico molecular para panel de neumonía filmarray (cod 502828): como primera opción. Muestra tomada de esputo, aspirado traqueal o lavado broncoalveolar en pacientes sin sospecha de neumonia por SARSCOV2.» | frag_p4_panel_profundo | 4 | SOURCE_STATED | PROPOSED | vi_filmarray_seleccion_panel: la fuente no declara exclusividad entre paneles; «como primera opción» es preferencia, no selección. |
| rel-nac-015 | rule_filmarray | rule_filmarray_panel_hisopado | branches | FLOW | — | «Diagnóstico molecular para patógenos respiratorios (cod 502162): muestra tomada de hisopado nasofaríngeo en pacientes que no espectoran.» | frag_p4_panel_hisopado | 4 | SOURCE_STATED | PROPOSED | Ídem: sin exclusividad declarada (vi_filmarray_seleccion_panel). |
| rel-nac-016 | rule_plan_egreso | act_educar_recaida | precedes | FLOW | — | «Al momento del alta se indicarán al paciente los signos y síntomas que sugieren recaída de la infección, específicamente fiebre, disnea, dolor torácico.» | frag_p6_alta_instrucciones | 6 | SOURCE_STATED | PROPOSED | Anclaje temporal explícito «Al momento del alta». |
| rel-nac-017 | rule_plan_egreso | act_cita_revision_4_semanas | precedes | FLOW | — | «Se dará cita de revisión con medicina interna a las 4 semanas del alta.» | frag_p6_alta_instrucciones | 6 | SOURCE_STATED | PROPOSED | Ídem: anclaje temporal explícito. |

## Candidatos REFERENCE

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-nac-030 | rule_filmarray_panel_profundo | rule_filmarray_panel_hisopado | references | REFERENCE | — | «…(cod 502828): como primera opción.…» / «…(cod 502162): …pacientes que no espectoran.» | frag_p4_panel_profundo, frag_p4_panel_hisopado | 4 | SOURCE_STATED | PROPOSED | Preferencia de orden declarada; NUNCA una selección ni exclusión mutua. |
| rel-nac-031 | rule_definicion_nac | rule_diagnostico_radiografico | references | REFERENCE | — | «El diagnóstico de neumonía se basa en un cuadro clínico compatible asociado a un infiltrado pulmonar de reciente aparición en la radiografía de tórax…» | frag_p1_definicion_nac, frag_p3_rx_torax | 1, 3 | SOURCE_STATED | PROPOSED | Ambas reglas derivan de la definición fuente; relación de derivación, no flujo. |

## Candidatos COMPOSITION

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-nac-040 | rule_hospitalizacion | rule_hosp_criterio_descompensacion, rule_hosp_criterio_inmunosupresion, rule_hosp_criterio_germenes_resistentes, rule_hosp_criterio_intolerancia_oral, rule_hosp_criterio_sepsis_choque, rule_hosp_criterio_multilobar_derrame, rule_hosp_criterio_curb65, rule_hosp_criterio_factores_sociales, rule_hosp_criterio_oxigeno | composes | COMPOSITION | — | «INDICACIONES DE HOSPITALIZACIÓN: Son indicaciones de hospitalización relacionadas con el diagnóstico de neumonía:» + 9 bullets | frag_p4_hosp_01, frag_p4_hosp_02, frag_p4_hosp_03, frag_p4_hosp_04, frag_p4_hosp_05, frag_p4_hosp_06, frag_p4_hosp_07, frag_p4_hosp_08, frag_p4_hosp_09 | 4 | NORMALIZED | PROPOSED | Encabezado en la capa de página (data/02_intermediate), no capturado como fragmento. OR canónico de 9 criterios. NO es flujo. |
| rel-nac-041 | rule_uci_criterios_3de | rule_uci_criterio_bun, rule_uci_criterio_fr, rule_uci_criterio_hipotension_lev, rule_uci_criterio_multilobares, rule_uci_criterio_pao2_fio2, rule_uci_criterio_confusion, rule_uci_criterio_hipotermia, rule_uci_criterio_plaquetas, rule_uci_criterio_leucocitos | composes | COMPOSITION | — | «Paciente que cumpla con 3 o más criterios de: - BUN > 30 - FR > 30 - Hipotensión que requiera LEV agresivos - Infiltrados multilobares - PaO2/FiO2 menores de 250 - Confusión - Hipotermia - Plaquetas menor de 100.000 - Leucocitos menor de 4000» | frag_p4_uci_3de | 4 | NORMALIZED | PROPOSED | AT_LEAST_N(3, 9 criterios). NO es flujo. |
| rel-nac-042 | rule_ingreso_uci_uce | rule_uci_criterios_3de | composes | COMPOSITION | — | «Paciente que cumpla con 3 o más criterios de:…» | frag_p4_uci_3de | 4 | NORMALIZED | PROPOSED | Componente del OR de ingreso a UCI-UCE. NO es flujo. |
| rel-nac-043 | rule_ingreso_uci_uce | rule_uci_bullet1 | composes | COMPOSITION | — | «Insuficiencia respiratoria, choque séptico o lactato sérico mayor de 2, falla renal aguda que requiere terapia de reemplazo renal o falla orgánica multisistémica.» | frag_p4_uci_bullet1 | 4 | INFERRED | PROPOSED | Agrupación por comas interpretada como OR de cinco (vi_uci_bullet1_parsing). La composición misma es INFERRED; NUNCA debe presentarse como flujo validado. |
| rel-nac-044 | rule_hospitalizacion | rule_labs_hospitalizacion, rule_gram_cultivo_esputo, rule_esputo_inducido, rule_hemocultivos (applies_to), rule_filmarray (applies_to), rule_filmarray_panel_profundo (applies_to), rule_filmarray_panel_hisopado (applies_to) | composes | COMPOSITION | — | (duplicación estructural de la expresión OR de hospitalización) | frag_p4_hosp_01 … frag_p4_hosp_09 | 4 | NORMALIZED | PROPOSED | Duplicación estructural únicamente; el flujo de cada regla lo apoya su propia frase fuente (rel-nac-006/010/011/013). |
| rel-nac-045 | rule_toracentesis_paraneumonico | rule_labs_derrame_pleural | composes | COMPOSITION | — | (duplicación estructural de la condición de toracentesis) | frag_p4_liquido_pleural | 4 | NORMALIZED | PROPOSED | Duplicación estructural; el flujo lo apoya frag_p3_labs_derrame (rel-nac-009). |

## Candidatos GAP

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-nac-050 | (página 6) | (flujo completo de diagnóstico y manejo) | missing | GAP | — | «ALGORITMOS DE DIAGNÓSTICO Y MANEJO:» | frag_p6_algoritmos | 6 | UNRESOLVED | PROPOSED | vi_algoritmos_imagen: imagen embebida no extraíble como texto. NO reconstruir con conocimiento médico general. |
| rel-nac-051 | (sección 2: manejo) | (tratamiento antibiótico empírico) | missing | GAP | — | «TRATAMIENTO ANTIBIÓTICO EMPÍRICO:» | frag_p4_tratamiento_heading, frag_p7_control_cambios_v09 | 4, 7 | UNRESOLVED | PROPOSED | vi_tratamiento_empirico_gap: encabezado sin cuerpo en la capa de texto. El control de cambios v09 menciona «tratamiento empírico según factores de riesgo». NO inventar contenido. |
| rel-nac-052 | rule_hosp_criterio_curb65 | (definición y cálculo de la escala CURB-65) | missing | GAP | — | «Escala de severidad CURB-65 ≥2» | frag_p4_hosp_07 | 4 | UNRESOLVED | PROPOSED | vi_curb65_componentes: la fuente referencia la escala sin definir componentes ni cálculo; el puntaje es dato externo. Regla UNRESOLVED. |

## Candidatos OMITTED

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-nac-060 | rule_hemocultivos | (toma de hemocultivos antes de la primera dosis IV de antibiótico) | references | OMITTED | — | «antes de la primera dosis intravenosa de antibióticos» (citado en la nota de procedencia de rule_hemocultivos; no aparece en la capa de texto del fragmento) | frag_p3_hemocultivos | 3 | SOURCE_STATED | PROPOSED | Restricción de procedimiento no representable como regla. |
| rel-nac-061 | rule_rx_repetir_48h, rule_plan_egreso | (programación temporal futura: 48 h / 4 semanas) | missing | OMITTED | — | «…debe repetirse la radiografía de tórax en 48 horas.» / «…cita de revisión… a las 4 semanas del alta.» | frag_p3_rx_repetir, frag_p6_alta_instrucciones | 3, 6 | SOURCE_STATED | PROPOSED | vi_temporal_no_representable: los intervalos son payloads declarativos; la semántica temporal mínima del motor no programa eventos futuros. Las transiciones FLOW (rel-nac-002/016/017) siguen siendo válidas; esta fila documenta la limitación de programación. |

## Relaciones evaluadas y NO incluidas como candidatos

- Criterios de egreso NAC (frag_p5_plan_egreso): un único fragmento, una única regla
  (`rule_plan_egreso`); no hay criterios-por-regla que componer (a diferencia de
  ITU). El encabezado «PLAN DE EGRESO.» está en la capa de página 5, no en un
  fragmento del paquete.
- Hospitalización → ingreso UCI-UCE: la fuente NO establece una transición explícita
  entre ambas listas; ambas listas comparten sección («2. RECOMENDACIONES PARA EL
  MANEJO»), pero la co-localización de sección NO es evidencia.
- `rule_esputo_buena_calidad` (frag_p3_esputo_calidad): definición de calidad de
  muestra sin relación entre reglas.
- Orden de aparición en el PDF, proximidad de fragmentos, ids de regla y similitud
  de variables: nunca evidencia.

## Estado

Ningún candidato está aprobado. 30 filas PROPOSED para revisión humana:
17 FLOW, 2 REFERENCE, 6 COMPOSITION, 3 GAP, 2 OMITTED.

## Reconciliación D2.5

Registro máquina-validado: `evaluation/pathway/CT-PL-193-v09-reconciliation.yaml`.
La reconciliación NO aprueba nada: recalifica el rol de presentación con evidencia
de fuente y conserva `review_status: PROPOSED` en todas las filas.

### Resumen de resultados (derivar de la YAML; no editar a mano)

| reconciliation_status | candidatos |
|---|---|
| READY_FOR_REVIEW | rel-nac-002, 003, 005, 006, 009, 010, 011, 012, 013, 014, 015, 016, 017, 030, 031, 040, 044, 045 |
| INFERRED_STRUCTURE | rel-nac-043 (nunca FLOW; insignia de no validado) |
| CONFLICT | rel-nac-041, 042 (SC-NAC-003) |
| UNRESOLVED_MAPPING | rel-nac-050 (flujograma = imagen, mapeo pendiente de confirmación visual) |
| GAP | rel-nac-051, 052 |
| REJECTED (rol final OMITTED) | rel-nac-001, 004, 007, 008 |
| OMITTED | rel-nac-060, 061 |

### Cambios de rol respecto al inventario

- `rel-nac-014` / `rel-nac-015` (paneles Filmarray): FLOW → **REFERENCE**. La fuente
  no establece rama exclusiva; «como primera opción» es preferencia declarada
  (vi_filmarray_seleccion_panel).
- `rel-nac-001`, `rel-nac-004`, `rel-nac-007`, `rel-nac-008`: REJECTED como aristas;
  los disparadores son condiciones propias de cada regla (semántica de nodo en D3).
  `rel-nac-007` además tiene listas de disparo no idénticas entre criterio y regla.
- `rel-nac-005`: se conserva FLOW, pero con `relation: supports` y etiqueta
  «apoya la decisión de hospitalización»: los exámenes alimentan la decisión, NO
  implican secuencia temporal estricta; los criterios permanecen en la regla de
  destino.
- `rel-nac-016` / `rel-nac-017` (instrucciones al alta / cita 4 semanas):
  FLOW → **INTERNAL** con `relation: attaches`. Las acciones ya pertenecen a
  `rule_plan_egreso` (action_refs canónico); NUNCA aristas regla→acción de la vía.
  La información temporal («al momento del alta», «4 semanas») permanece como
  contexto declarativo de la acción (vi_temporal_no_representable).
- `rel-nac-050`: GAP → **UNRESOLVED_MAPPING** con `source_representation: DIAGRAM`:
  el flujograma de la página 6 EXISTE como imagen embebida (1270×976 px, verificado
  con el inventario de objetos del PDF); no es ausencia de fuente, es limitación de
  extracción (sin capa de texto y sin OCR disponible en este entorno).
- `rel-nac-051`: se confirma GAP, ahora con `source_evidence_status:
  SOURCE_CONTENT_ABSENT`: las páginas 4 y 5 NO contienen imágenes embebidas
  (inventario pdfimages: solo páginas 1, 2 y 6) y la capa de texto termina en el
  encabezado «TRATAMIENTO ANTIBIÓTICO EMPÍRICO:». El cuerpo del tratamiento no está
  presente en este PDF: ausencia de contenido fuente, no limitación de extracción.
- `rel-nac-043` (bullet1): permanece COMPOSITION con `evidence_class: INFERRED` y
  estado INFERRED_STRUCTURE; nunca FLOW.

### Conflictos de fuente (SC-NAC-*)

Ningún conflicto elige un ganador. El lado TEXTO está verificado por máquina; el
lado DIAGRAMA (página 6, imagen raster) se registra como `PENDING_VISUAL_CONFIRMATION`
porque el contenido del diagrama no es legible por máquina en este entorno. La
confirmación visual humana es requisito previo a cualquier uso en D3.

| conflict_id | tema | lado A | lado B | estado |
|---|---|---|---|---|
| SC-NAC-001 | Umbral CURB-65 de hospitalización | TEXTO pág. 4: «Escala de severidad CURB-65 ≥2» | DIAGRAMA pág. 6: «CURB > 2» (reportado por el revisor humano) | OPEN / UNRESOLVED |
| SC-NAC-002 | Umbral BUN en UCI-UCE | TEXTO pág. 4: «BUN > 30» | DIAGRAMA pág. 6: «BUN > 20» (reportado) | OPEN / UNRESOLVED |
| SC-NAC-003 | Cantidad/conjunto de criterios UCI-UCE | TEXTO pág. 4: «3 o más criterios» + 9 criterios | DIAGRAMA pág. 6: cantidad/conjunto potencialmente distinto (reportado) | OPEN / UNRESOLVED |
| SC-NAC-004 | «TAS < 90» en UCI-UCE | TEXTO pág. 4: el criterio NO aparece en la lista | DIAGRAMA pág. 6: «TAS < 90» presente (reportado) | OPEN / UNRESOLVED |

### Evidencia de imagen documentada

- Página 6: flujograma «ALGORITMOS DE DIAGNÓSTICO Y MANEJO:» — imagen raster única;
  sin texto vectorial en el flujo de contenido (verificado con análisis del content
  stream). Su contenido requiere lectura visual humana.
- Página 2: «Gráfico 1. Etiología de la neumonía…» — imagen (1200×742 px) de etiología;
  evidencia epidemiológica, sin relación de decisión inventariada.
- Página 1: logo institucional (425×219 px); sin contenido clínico.

Los detalles completos (campos fuente, notas de reconciliación por fila) están en la
YAML de reconciliación, que es el registro validado por pruebas.
