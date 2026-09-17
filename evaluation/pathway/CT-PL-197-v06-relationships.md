# CT-PL-197 v06 — Inventario de relaciones clínicas candidatas

Fase 10 (D1/D2) — evidencia para revisión humana ANTES de cualquier implementación
de vías clínicas. Ninguna fila está aprobada. `review_status` es `PROPOSED` en todas;
el revisor humano deberá cambiarla a `APPROVED`, `REJECTED` u `OMITTED`.

Documento fuente: `doc-800af94bc0654138` — CT-PL-197 v06 (ITU), 5 páginas.
Paquete canónico: `protocols/CT-PL-197/v06/package.yaml` (60 reglas, 84 fragmentos).
Las citas provienen de `verbatim_text` de los fragmentos del paquete y de la capa de
texto extraída (`data/02_intermediate/doc-800af94bc0654138/pages/`); cuando la cita
proviene de la capa de página y no de un fragmento del paquete, se indica.

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
| rel-itu-001 | rule_def_ba | rule_def_itu | branches | FLOW | — | «…provenientes de pacientes **sin** signos o síntomas atribuibles a ITU» vs «…en pacientes **con** signos o síntomas atribuibles a ITU» | frag_p1_def_ba, frag_p1_def_itu | 1 | EXTRACTED | PROPOSED | Bifurcación definicional de entrada (BA vs ITU). Apoyada por «El diagnóstico diferencial entre bacteriuria asintomática e ITU…» (capa de página 2, no es fragmento) y por las filas separadas BA/ITU de la Tabla 1. |
| rel-itu-002 | rule_def_ba | rule_tto_ba_indicado | gates | FLOW | — | «Indicaciones de tratamiento de bacteriuria asintomática • Mujer embarazada • Procedimiento invasivo de vías urinarias con riesgo de sangrado o disrupción del uroepitelio» | frag_p3_tto_ba_indicaciones, frag_p3_tto_ba_gestante, frag_p3_tto_ba_procedimiento | 3 | SOURCE_STATED | PROPOSED | Lista de indicaciones explícita que restringe el tratamiento de BA. |
| rel-itu-003 | rule_def_ba | rule_t1_ba_row | gates | FLOW | — | «**Recordar su tratamiento sólo en gestantes o pacientes quienes serán sometidos a procedimientos urológicos donde se prevé la disrupción del uroepitelio» | frag_p4_t1_nota_ba, frag_p4_t1_ba_row | 4 | SOURCE_STATED | PROPOSED | Nota ** de la fila «Bacteriuria asintomática**» de la Tabla 1. |
| rel-itu-004 | rule_def_ba | rule_t2_ba_gestante | gates | FLOW | — | «En mujeres embarazadas, la bacteriuria asintomática debe tratarse porque se ha asociado con un mayor riesgo de pielonefritis» | frag_p2_embarazada_debe_tratarse, frag_p4_t2_ba_row | 2, 4 | SOURCE_STATED | PROPOSED | Fila «Bacteriuria asintomática» de la Tabla 2 (gestante). |
| rel-itu-005 | rule_def_itu_bajo | rule_t1_itu_baja | branches | FLOW | — | «ITU baja (complicada o no complicada)» | frag_p4_t1_itu_baja, frag_p2_clasificacion_alta_baja | 4 | EXTRACTED | PROPOSED | Tabla 1: estructura CONDICIÓN→ANTIBIÓTICO EMPÍRICO. La clasificación es SOURCE_STATED; el mapeo fila→regla es estructura de tabla. |
| rel-itu-006 | rule_def_itu_alto | rule_t1_alta_ambulatoria | branches | FLOW | — | «ITU alta ambulatoria Cefalexina 1» | frag_p4_t1_ambulatoria | 4 | EXTRACTED | PROPOSED | Rama «no hospitalizado» de la fila ITU alta; la celda adjunta es la nota 1 de reevaluación (rel-itu-010). |
| rel-itu-007 | rule_def_itu_alto | rule_t1_alta_hosp_sin_fr | branches | FLOW | — | «ITU alta ambulatoria» / «ITU alta hospitalaria sin FR para BGN resistentes» | frag_p4_t1_ambulatoria, frag_p4_t1_sin_fr | 4 | EXTRACTED | PROPOSED | Rama hospitalizado vs ambulatorio, explícita en las filas de la Tabla 1. |
| rel-itu-008 | rule_fr_bgn_resistentes | rule_t1_alta_hosp_con_fr_piperacilina | branches | FLOW | — | «**FR BGN resistentes: hospitalización > 48 horas en los últimos 3 meses, uso de antibióticos en últimos 90 días, colonización por germen BLEE.» + «ITU alta hospitalaria con FR para BGN resistentes***» | frag_p4_t1_nota_fr, frag_p4_t1_con_fr | 4 | SOURCE_STATED | PROPOSED | La nota ** define la condición de la rama «con FR». |
| rel-itu-009 | rule_t1_alta_hosp_con_fr_amikacina | rule_t1_alta_hosp_con_fr_meropenem | excepts | FLOW | excepción | «Piperacilina tazobactam o Amikacina2 o Meropenem3» + «2 Evitar en choque» + «3 Administrar empíricamente si hay choque» | frag_p4_t1_con_fr_drogas, frag_p4_t1_nota_amikacina, frag_p4_t1_nota_meropenem | 4 | SOURCE_STATED | PROPOSED | Marcadores de nota 2/3: corresponde a la excepción canónica de rule_t1_alta_hosp_con_fr_amikacina (choque_septico). |
| rel-itu-010 | rule_t1_alta_ambulatoria | rule_reevaluar_48h | precedes | FLOW | — | «1 Reevaluar con urocultivo a las 48 horas para ajuste» (celda adjunta a la fila «ITU alta ambulatoria») | frag_p4_t1_reevaluar, frag_p4_t1_ambulatoria | 4 | SOURCE_STATED | PROPOSED | Instrucción numerada explícita anclada a la fila ambulatoria. |
| rel-itu-011 | rule_tirilla_descarta_diagnostico | TERMINAL: diagnóstico descartado | branches | FLOW | NO | «…un resultado normal en pacientes con baja sospecha clínica descarta el diagnóstico.» | frag_p2_tirilla_descarta | 2 | SOURCE_STATED | PROPOSED | Rama de fin de vía; "to" es un terminal de presentación propuesto, no una regla canónica. |
| rel-itu-012 | rule_citoquimico_orina | TERMINAL: sin citoquímico | excepts | FLOW | excepción | «Se debe realizar citoquímico de orina a todo paciente en el servicio de urgencias con sospecha de ITU, excepto mujeres con primer episodio y síntomas típicos.» | frag_p2_citoquimico | 2 | SOURCE_STATED | PROPOSED | Excepción canónica de rule_citoquimico_orina. |
| rel-itu-013 | rule_urocultivo_indicado | TERMINAL: sin urocultivo | excepts | FLOW | excepción | «Debe solicitarse en todos los casos, excepto primer episodio de ITU baja no complicada en mujer premenopáusica.» | frag_p3_urocultivo_indicacion | 3 | SOURCE_STATED | PROPOSED | Excepción canónica de rule_urocultivo_indicado. |
| rel-itu-014 | rule_urocultivo_indicado | rule_urocultivo_positivo_1e5 | branches | FLOW | — | «Los urocultivos se consideran positivos con el crecimiento de ≥10 5 UFC de una bacteria en una muestra de orina o btenida de forma adecuada por micción espontánea» | frag_p3_urocultivo_positivo_1e5 | 3 | EXTRACTED | PROPOSED | Rama de interpretación del resultado según contexto de muestra. |
| rel-itu-015 | rule_urocultivo_indicado | rule_urocultivo_positivo_1e3 | branches | FLOW | — | «con un crecimiento ≥10 3 UFC en un paciente con síntomas no explicados por otra patología» | frag_p3_urocultivo_positivo_1e3 | 3 | EXTRACTED | PROPOSED | Ídem: rama por contexto. |
| rel-itu-016 | rule_urocultivo_indicado | rule_urocultivo_positivo_1e2 | branches | FLOW | — | «el crecimiento de ≥10 2 UFC de una bacteria en una muestra de orina obtenida a través de una sonda vesical recién insertada.» | frag_p3_urocultivo_positivo_1e2 | 3 | EXTRACTED | PROPOSED | Ídem: rama por contexto. |
| rel-itu-017 | rule_def_itu_complicada_estructural | rule_imagen_urotomografia | branches | FLOW | — | «en los casos de sospecha de alteración estructural, incluyendo la litiasis de vías urinarias la elección será urotomografía» | frag_p3_imagen_urotomografia | 3 | SOURCE_STATED | PROPOSED | «la elección será» = rama explícita. |
| rel-itu-018 | rule_def_itu_complicada_estructural | rule_imagen_ecografia_funcional | branches | FLOW | — | «para los casos en los cuales se sospecha una alteración funcional, especialmente por inadecuado vaciamiento vesical o trastornos obstructivos de las vías urinarias, la elección será ecografía de vías urinarias con medición del residuo postmiccional.» | frag_p3_imagen_ecografia | 3 | SOURCE_STATED | PROPOSED | «la elección será» = rama explícita. |
| rel-itu-019 | rule_t1_* (contexto: tratamiento antibiótico) | rule_imagen_urgente | gates | FLOW | — | «…fiebre persistente después de 72 horas de tratamiento antibiótico correcto.» | frag_p3_imagen_urgente | 3 | SOURCE_STATED | PROPOSED | Disparador temporal interno a la condición canónica (vi_fiebre_72h_dos_condiciones). El "from" es contexto de tratamiento, no una regla específica — decisión humana requerida sobre el anclaje. |
| rel-itu-020 | rule_hospitalizacion | rule_analisis_sangre | gates | FLOW | — | «En todo paciente con ITU que sea hospitalizado debe obtenerse muestra de sangre para hemoleucograma, ionograma, función renal y proteína C reactiva (PCR).» | frag_p3_analisis_sangre | 3 | SOURCE_STATED | PROPOSED | Condicional explícito en la redacción fuente. |
| rel-itu-021 | rule_def_itu_alto | rule_hemocultivos | gates | FLOW | — | «Los hemocultivos deben solicitarse en todos los casos de pielonefritis aguda que cursan con fiebre, hipotermia o ch oque séptico.» | frag_p3_hemocultivos | 3 | SOURCE_STATED | PROPOSED | Pielonefritis = ITU alta (definición frag_p1_def_itu_alto). |
| rel-itu-022 | rule_def_itu_alto | rule_ecografia_renal_gestante | gates | FLOW | — | «En las mujeres embarazadas se hará ecografía renal en todas las pacientes con pielonefritis, más de un episodio de ITU durante el embarazo, sospecha de litiasis por hematuria y/o dolor.» | frag_p3_imagen_gestante | 3 | SOURCE_STATED | PROPOSED | Condicional explícito (gestante + pielonefritis/otros). |
| rel-itu-023 | rule_t2_itu_alta_gestante_cefazolina | rule_t2_itu_alta_gestante_piperacilina | branches | FLOW | — | «ITU alta Cefazolina* o Piperacilina tazobactam** o Meropenem***» + «*Sin factores de riesgo para BGN resistentes» + «**Con factores de riesgo para BGN resistentes, sin choque» | frag_p5_t2_itu_alta_row, frag_p5_t2_sin_fr, frag_p5_t2_con_fr | 5 | SOURCE_STATED | PROPOSED | Notas de marcador * / ** de la Tabla 2. |
| rel-itu-024 | rule_t2_itu_alta_gestante_piperacilina | rule_t2_itu_alta_gestante_meropenem | branches | FLOW | — | «**Con factores de riesgo para BGN resistentes, sin choque» + «***Con factores de riesgo para BGN resistentes, con choque» | frag_p5_t2_con_fr, frag_p5_t2_con_fr_choque, frag_p5_t2_itu_alta_row | 5 | SOURCE_STATED | PROPOSED | Rama por choque, explícita en las notas de marcador. |
| rel-itu-025 | rule_t2_itu_baja_gestante | rule_t2_preventiva_baja | gates | FLOW | — | «ITU baja Nitrofurantoína o Cefalexina o Fosfomicina 3 … No **Sólo si hay recurrencia de la infección**» | frag_p4_t2_itu_baja_row | 4 | SOURCE_STATED | PROPOSED | Celda explícita de profilaxis condicionada a recurrencia. |
| rel-itu-026 | rule_t2_itu_alta_gestante_cefazolina | rule_t2_preventiva_alta | gates | FLOW | — | «ITU alta Cefazolina* o Piperacilina tazobactam** o Meropenem*** … No **Sí**» | frag_p5_t2_itu_alta_row, frag_p5_t2_preventiva_alta | 5 | EXTRACTED | PROPOSED | Celda «Sí» de profilaxis en fila ITU alta; mapeo de tabla. |

## Candidatos REFERENCE

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-itu-030 | rule_def_itu_bajo / rule_def_itu_alto | rule_t1_* (contexto: tratamiento) | references | REFERENCE | — | «La presentación clínica de la ITU permite clasificar la infección como alta o baja, clasificación necesaria para definir el tratamiento y el pronóstico.» | frag_p2_clasificacion_alta_baja | 2 | SOURCE_STATED | PROPOSED | Vinculación de sección explícita en la fuente; NO es una transición temporal. |
| rel-itu-031 | rule_gram_urgencias | rule_t1_* (contexto: tratamiento empírico) | references | REFERENCE | — | «Gram de orina sin centrifugar: Suministra información inmediata sobre la naturaleza de la infección y sirve para guiar el tratamiento empírico…» | frag_p3_gram | 3 | SOURCE_STATED | PROPOSED | La prueba informa al tratamiento; la fuente no define una transición. |
| rel-itu-032 | rule_fosfomicina_preferida | rule_t1_itu_baja / rule_t2_* | references | REFERENCE | — | «*Preferir en pacientes quienes tienen ITU recurrente o han estado expuestas a terapia antimicrobiana en los últimos 90 días.» | frag_p4_t1_nota_fosfomicina, frag_p5_t2_nota3 | 4, 5 | SOURCE_STATED | PROPOSED | Preferencia declarada por la fuente; NUNCA una selección ni un ranking. |
| rel-itu-033 | rule_def_ba | rule_def_itu_alto | references | REFERENCE | — | «En mujeres embarazadas, la bacteriuria asintomática debe tratarse porque se ha asociado con un mayor riesgo de pielonefritis» | frag_p2_embarazada_debe_tratarse | 2 | SOURCE_STATED | PROPOSED | Asociación causal declarada; no es flujo clínico. |

## Candidatos COMPOSITION

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-itu-040 | rule_def_ba | rule_def_ba_cultivos | composes | COMPOSITION | — | «Se requiere 2 urocultivos con el mismo patógeno y perfil de sensibilidad en mujeres no embarazadas, 1 en hombres y pacientes gestantes.» | frag_p1_def_ba_cultivos, frag_p1_def_ba | 1 | NORMALIZED | PROPOSED | Componente de la definición de BA (nota de procedencia de rule_def_ba). |
| rel-itu-041 | rule_hospitalizacion | rule_hosp_criterio_choque_septico, rule_hosp_criterio_intolerancia_oral, rule_hosp_criterio_itu_alta, rule_hosp_criterio_descompensacion, rule_hosp_criterio_germen_resistente, rule_hosp_criterio_funcion_renal, rule_hosp_criterio_absceso, rule_hosp_criterio_soporte_social | composes | COMPOSITION | — | «Indicaciones de hospitalización en pacientes con ITU:» + 8 bullets | frag_p3_hosp_choque_septico, frag_p3_hosp_intolerancia, frag_p3_hosp_itu_alta, frag_p3_hosp_descompensacion, frag_p3_hosp_resistente, frag_p3_hosp_funcion_renal, frag_p3_hosp_absceso, frag_p3_hosp_social | 3 | NORMALIZED | PROPOSED | Encabezado presente en la capa de página (data/02_intermediate), no capturado como fragmento. OR canónico de 8 criterios. NO es flujo. |
| rel-itu-042 | rule_plan_egreso | rule_egreso_afebril_48h, rule_egreso_tas, rule_egreso_fc, rule_egreso_fr, rule_egreso_sato2_pao2, rule_egreso_via_oral, rule_egreso_comorbilidades, rule_egreso_tratamiento, rule_egreso_social | composes | COMPOSITION | — | «Indicaciones para paso a terapia oral y/o egreso:» + 9 bullets | frag_p3_egreso_afebril, frag_p3_egreso_tas, frag_p4_egreso_fc, frag_p4_egreso_fr, frag_p4_egreso_sato2_pao2, frag_p4_egreso_via_oral, frag_p4_egreso_comorbilidades, frag_p4_egreso_tratamiento, frag_p4_egreso_social | 3, 4 | NORMALIZED | PROPOSED | Encabezado en la capa de página, no capturado como fragmento. AND canónico de 9 criterios. NO es flujo. |
| rel-itu-043 | rule_fr_bgn_resistentes | rule_t1_alta_hosp_con_fr_piperacilina, rule_t1_alta_hosp_con_fr_amikacina, rule_t1_alta_hosp_con_fr_meropenem, rule_t2_itu_alta_gestante_piperacilina, rule_t2_itu_alta_gestante_meropenem | composes | COMPOSITION | — | «**FR BGN resistentes: hospitalización > 48 horas en los últimos 3 meses, uso de antibióticos en últimos 90 días, colonización por germen BLEE.» | frag_p4_t1_nota_fr | 4 | NORMALIZED | PROPOSED | Expresión OR compartida/duplicada entre reglas de tratamiento. Estructural; NO es flujo. |
| rel-itu-044 | rule_hospitalizacion | rule_analisis_sangre (applies_to) | composes | COMPOSITION | — | applies_to = OR de los 8 criterios de hospitalización (duplicación estructural) | frag_p3_analisis_sangre | 3 | NORMALIZED | PROPOSED | La duplicación estructural NO es evidencia de flujo; el flujo lo apoya la redacción del fragmento (rel-itu-020). |

## Candidatos GAP

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-itu-050 | rule_def_ba / rule_def_itu | (umbral universal de bacteriuria significativa) | missing | GAP | — | «Recuento significativo de colonias bacterianas…» | frag_p1_def_ba, frag_p1_def_itu | 1 | UNRESOLVED | PROPOSED | vi_recuento_significativo_umbral: la decisión de entrada BA/ITU depende de un umbral que la fuente define solo por contexto (pág. 3). |

## Candidatos OMITTED

| candidate_id | from | to | relation | presentation_role | branch_label | evidence_quote | fragment_ids | page | evidence_class | review_status | reviewer_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rel-itu-060 | rule_t1_* / rule_t2_* (terapia empírica) | (ajuste según urocultivo y antibiograma) | references | OMITTED | — | «1Esta es la terapia empírica. Siempre debe ajustarse según resultados de urocultivo y antibiograma» + «2La decisión se toma con base en los cultivos y pruebas de sensibilidad» | frag_p5_t2_nota1, frag_p5_t2_nota2 | 5 | SOURCE_STATED | PROPOSED | Instrucción procedimental no computable (vi_ajuste_urocultivo_antibiograma). |
| rel-itu-061 | rule_t2_preventiva_baja / rule_t2_preventiva_alta | (cambio a semana 34 / hasta finalización del embarazo) | missing | OMITTED | — | «4 A la semana 34 podría hacerse cambio a cefalexina o nitrofurantoína, si el microorganismo es sensible. Administrar hasta la finalización del embarazo.» | frag_p5_t2_nota4 | 5 | SOURCE_STATED | PROPOSED | Calendario no computable (vi_semana34_calendar). |
| rel-itu-062 | (observación de Tabla 2) | (restricción por medicamento en primer trimestre) | missing | OMITTED | — | «Evitar en primer trimestre. Hasta semana 34 gestación4» | frag_p5_t2_observacion_trimestre | 5 | SOURCE_STATED | PROPOSED | Ambigüedad de fármaco; no mapeable (vi_evitar_primer_trimestre_ambiguedad). |
| rel-itu-063 | rule_hospitalizacion | (criterio pediátrico) | outside_scope | OMITTED | — | «Pielonefritis aguda en pacientes pediátricos.» | frag_p3_hosp_pediatrica | 3 | SOURCE_STATED | PROPOSED | Fuera del alcance adulto (vi_criterio_pediatrico_fuera_alcance). |
| rel-itu-064 | rule_def_itu_complicada_clinica | (prostatitis) | outside_scope | OMITTED | — | «…y prostatitis (este último tema excede los alcances del presente protocolo).» | frag_p1_def_itu_complicada_clinica | 1 | SOURCE_STATED | PROPOSED | Excluido por la propia fuente (vi_prostatitis_fuera_alcance). |
| rel-itu-065 | rule_def_ba | (cláusula de piuria pediátrica) | outside_scope | OMITTED | — | «En población pediátrica debe haber ausencia de piuria en el sedimento.» | frag_p1_def_ba_piuria | 1 | SOURCE_STATED | PROPOSED | Fuera del alcance adulto del protocolo. |
| rel-itu-066 | rule_urocultivo_indicado | (toma de muestra antes de la primera dosis de antibiótico) | references | OMITTED | — | «Toma de la muestra: debe tomarse antes de la primera dosis de antibiótico» | frag_p3_toma_muestra_antibiotico | 3 | SOURCE_STATED | PROPOSED | Instrucción de procedimiento (vi_restricciones_procedimiento). |

## Relaciones evaluadas y NO incluidas como candidatos

- `rule_egreso_*` ↔ `rule_plan_egreso` como FLOW: la fuente lista criterios bajo un
  encabezado; no hay frase de transición «se dará de alta cuando…» explícita en la
  capa de texto ITU. Solo COMPOSITION (rel-itu-042).
- `rule_tc_abscesos_nefritis`: su condición es interna a la regla («Se hará TC con
  contraste cuando se busquen…», frag_p3_imagen_tc_abscesos); no hay relación entre
  reglas que inventariar.
- «No se consideran síntomas compatibles con ITU la orina turbia o de mal olor»
  (frag_p2_no_sintomas_itu): definición negativa sin regla asociada; no es una
  relación entre reglas.
- Orden de aparición en el PDF y proximidad de fragmentos: nunca evidencia.

## Estado

Ningún candidato está aprobado. 43 filas PROPOSED para revisión humana:
26 FLOW, 4 REFERENCE, 5 COMPOSITION, 1 GAP, 7 OMITTED.

## Reconciliación D2.5

Registro máquina-validado: `evaluation/pathway/CT-PL-197-v06-reconciliation.yaml`.
La reconciliación NO aprueba nada: recalifica el rol de presentación con evidencia
de fuente y conserva `review_status: PROPOSED` en todas las filas.

### Resumen de resultados (derivar de la YAML; no editar a mano)

| reconciliation_status | candidatos |
|---|---|
| READY_FOR_REVIEW | rel-itu-001..013, 017, 018, 020..026, 030..033, 040..044 |
| REJECTED (rol final OMITTED) | rel-itu-014, 015, 016, 019 |
| GAP | rel-itu-050 |
| OMITTED | rel-itu-060..066 |

### Cambios de rol respecto al inventario

- `rel-itu-001` (BA vs ITU): FLOW → **REFERENCE**. Las definiciones contrastan
  categorías; la fuente no establece una transición «si síntomas → ITU». La
  bifurcación es semántica de clasificación/nodo de entrada en D3.
- `rel-itu-005` / `rel-itu-006` / `rel-itu-007` / `rel-itu-008` (filas de Tabla 1):
  FLOW → **REFERENCE**. Las filas de tabla son aplicabilidad/mapeo contextual, no
  transiciones; la condición de cada fila pertenece a la regla.
- `rel-itu-009` (amikacina/meropenem): FLOW → **EXCEPTION_CONTEXT** con
  `relation: excepts` y `branch_label: excepción (choque)`. NO es una arista FLOW
  ordinaria y NO es una secuencia fármaco→fármaco: «2 Evitar en choque» es la
  excepción canónica `choque_septico` de la regla de amikacina y «3 Administrar
  empíricamente si hay choque» es la condición de la regla de meropenem. D3
  representa las alternativas desde las condiciones canónicas (sin choque →
  alternativas aplicables; con choque → meropenem; amikacina con choque → EXCEPTED).
- `rel-itu-012` / `rel-itu-013` (excepciones): FLOW → **EXCEPTION_CONTEXT**. La
  fuente declara la excepción pero NO declara qué ocurre después; el destino
  `EXCEPTED: destino no declarado en la fuente` no inventa terminales. D3 usa la
  excepción de la regla canónica y el resultado EXCEPTED del motor.
- `rel-itu-023` / `rel-itu-024` (gestante ITU alta): FLOW → **BRANCH_CONTEXT** con
  ancla de presentación `BRANCH_CONTEXT: ITU alta en gestante — selección empírica
  según FR/choque`. NO son una cadena secuencial cefazolina → piperacilina →
  meropenem: son alternativas condicionales (sin FR → cefazolina; con FR + sin
  choque → piperacilina tazobactam; con FR + choque → meropenem) seleccionadas por
  sus propias condiciones canónicas. El ancla es solo presentación, nunca una regla
  canónica nueva.
- `rel-itu-014` / `rel-itu-015` / `rel-itu-016` (umbrales de urocultivo): REJECTED.
  Son criterios de positividad contextuales (condiciones propias de cada regla de
  interpretación), no transiciones entre reglas. D3 puede mostrarlos como ramas de
  interpretación del nodo urocultivo (semántica de nodo).
- `rel-itu-019` (imagen urgente 72 h): REJECTED y **comodín eliminado**. La fuente
  no nombra una regla de tratamiento específica; el disparador temporal es condición
  propia de `rule_imagen_urgente` (vi_fiebre_72h_dos_condiciones).
- `rel-itu-021` / `rel-itu-022` (hemocultivos / ecografía gestante): FLOW →
  **REFERENCE**. Las condiciones adicionales (fiebre/hipotermia/choque; gestante,
  episodios, litiasis) pertenecen a cada regla; solo la contextualización por
  pielonefritis es apoyada.
- `rel-itu-025` / `rel-itu-026` (profilaxis): FLOW → **REFERENCE**. «Sólo si hay
  recurrencia» y la celda «Sí» son condiciones/atributos de aplicabilidad, no
  aristas de flujo.
- `rel-itu-011` (tirilla descarta): se conserva FLOW hacia `TERMINAL: diagnóstico
  descartado`. TERMINAL es un destino de presentación únicamente, NO una regla
  canónica; D3 puede renderizarlo como nodo terminal de presentación.

### Notas de verificación de fuente

- Los encabezados «Indicaciones de hospitalización en pacientes con ITU:» e
  «Indicaciones para paso a terapia oral y/o egreso:» están en la capa de texto de
  página (pdftotext) pero NO fueron capturados como fragmentos del paquete; se
  citan en `source_location` de rel-itu-041/042.
- La fuente ITU NO contiene frase «se dará de alta cuando…»; el egreso es solo
  encabezado + bullets (rel-itu-042).
- El PDF ITU no tiene contenido de imagen clínica: única imagen = logo (pág. 1).
  Toda la evidencia ITU es TEXT/TABLE verificada por máquina.

Los detalles completos (campos fuente, notas de reconciliación por fila) están en la
YAML de reconciliación, que es el registro validado por pruebas.
