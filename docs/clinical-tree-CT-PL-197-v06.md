# Clinical Decision Tree — CT-PL-197 v06 (ITU)

Protocol metadata:

| | |
|---|---|
| Protocol | CT-PL-197 — Protocolo infección del tracto urinario (ITU) y bacteriuria asintomática en población adulta |
| Version | v06 |
| Approval date | 2025-09-30 |
| Population | Atención de pacientes adultos con bacteriuria asintomática o ITU |
| Source document | `doc-800af94bc0654138` — CT-PL-197 … ITU ADULTOS (v6-sep-2025).pdf, 5 páginas |
| Canonical rules | 60 |
| FLOW relationships (D2.5 reconciliadas) | 8 |
| Presentation branch contexts | 1 (gestante — ITU alta) |
| Presentation terminals | 1 («diagnóstico descartado») |
| Disconnected components | 5 componentes FLOW + 1 contexto de rama + 46 reglas sin conexión FLOW |

> **Nota de lectura.** Este documento es una representación de presentación de las
> relaciones reconciliadas en D2.5 (`evaluation/pathway/CT-PL-197-v06-reconciliation.yaml`).
> Solo las relaciones FLOW reconciliadas aparecen como transiciones entre reglas.
> REFERENCE, COMPOSITION, EXCEPTION_CONTEXT, BRANCH_CONTEXT, GAP y OMITTED **no** se
> dibujan como flujo clínico. No se descubrió ni infirió ninguna relación nueva.
> Prototipo de investigación; no es consejo clínico.

## Notation

| Símbolo | Significado |
|---|---|
| `[FLOW]` | Transición de presentación reconciliada en D2.5 con evidencia de fuente |
| `[TERMINAL]` | Terminal de presentación; **no** es una regla canónica |
| `[CONTEXTO]` | Contexto de rama de presentación; **no** es una regla canónica |
| `⚠️ EXCEPTION` | Excepción canónica de la regla; la fuente **no** declara un destino posterior |
| `⚠️ GAP` | Evidencia insuficiente o contenido ausente de la fuente |
| `⚪ UNKNOWN` | Semántica del motor: información faltante → INDETERMINATE (nunca FALSE) |
| `(pN)` | Página del documento fuente |

---

# 1. Clinical Decision Tree

El grafo reconciliado de ITU tiene **5 componentes FLOW** más un contexto de rama
(sección 2). Las reglas sin FLOW aparecen en la sección 5.

## Component 1 — Bacteriuria asintomática (BA) → tratamiento

```
        ┌──────────────────────────────────────────────┐
        │ rule_def_ba                                  │
        │ Condición: bacteriuria significativa SIN     │
        │ signos ni síntomas de ITU                    │
        │ Fuente: frag_p1_def_ba (p1) · NORMALIZED     │
        └──────┬──────────────┬──────────────┬─────────┘
               │              │              │
  [FLOW]       │  [FLOW]      │  [FLOW]      │
  indicaciones │  «sólo en    │  gestante    │
  de tto de BA │  gestantes o │  (Tabla 2)   │
  (gestante o  │  procedimien-│              │
  procedimiento│  tos uroló-  │              │
  invasivo)    │  gicos»      │              │
               ▼              ▼              ▼
   ┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
   │ rule_tto_ba_indicado   │ │ rule_t1_ba_row         │ │ rule_t2_ba_gestante    │
   │ Condición: BA +        │ │ Condición: BA +        │ │ Condición: BA          │
   │ (gestante o            │ │ (gestante o procedi-   │ │ (población gestante)   │
   │ procedimiento          │ │ miento urológico)      │ │ Acción: nitrofuran-    │
   │ invasivo)              │ │ Acción: nitrofuran-    │ │ toína / cefalexina /   │
   │ Acción: tratar BA      │ │ toína / cefalexina /   │ │ fosfomicina            │
   │ (DECISION)             │ │ fosfomicina            │ │ (alternativas)         │
   │ Fuente: frag_p3_tto_ba │ │ (alternativas)         │ │ Fuente:                │
   │ indicaciones (p3)      │ │ Fuente: frag_p4_t1_    │ │ frag_p4_t2_ba_row (p4) │
   │                        │ │ ba_row (p4)            │ │                        │
   └────────────────────────┘ └────────────────────────┘ └────────────────────────┘

   ⚠️ Las tres acciones PRESCRIBE de cada fila son alternativas declaradas por la
   fuente; nunca una selección ni una secuencia.
```

## Component 2 — ITU alta ambulatoria → reevaluación

```
     ┌──────────────────────────────────────────────┐
     │ rule_t1_alta_ambulatoria                     │
     │ Condición: ITU alta + no hospitalizado       │
     │ Acción: cefalexina (alternativa declarada)   │
     │ Fuente: frag_p4_t1_ambulatoria (p4)          │
     └──────────────────────┬───────────────────────┘
                            │
              [FLOW] «1 Reevaluar con urocultivo a las 48 horas
                      para ajuste» (nota 1 anclada a la fila;
                      intervalo declarativo, sin programación)
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │ rule_reevaluar_48h                           │
     │ Condición: tiempo desde inicio de terapia    │
     │ ≥ 48 horas                                   │
     │ Acción: urocultivo de control                │
     │ Fuente: frag_p4_t1_reevaluar (p4)            │
     └──────────────────────────────────────────────┘
```

## Component 3 — Tirilla de orina → descarte diagnóstico

```
     ┌──────────────────────────────────────────────┐
     │ rule_tirilla_descarta_diagnostico            │
     │ Condición: tirilla normal + baja sospecha    │
     │ clínica                                      │
     │ Acción: descartar diagnóstico (DECISION)     │
     │ Fuente: frag_p2_tirilla_descarta (p2)        │
     └──────────────────────┬───────────────────────┘
                            │
                [FLOW] resultado normal + baja sospecha
                «descarta el diagnóstico»
                            │
                            ▼
                 ╭─────────────────────────╮
                 │ Diagnóstico descartado  │
                 │ [TERMINAL] de presenta- │
                 │ ción — no es una regla  │
                 │ canónica                │
                 ╰─────────────────────────╯
```

## Component 4 — Sospecha de alteración estructural/funcional → imagen

```
        ┌──────────────────────────────────────────────┐
        │ rule_def_itu_complicada_estructural          │
        │ Condición: alteración estructural o          │
        │ funcional de vías urinarias                  │
        │ Fuente: frag_p1_def_itu_complicada_          │
        │ estructural (p1)                             │
        └───────────────┬───────────────┬──────────────┘
                        │               │
      [FLOW] sospecha   │               │  [FLOW] sospecha
      de alteración     │               │  de alteración
      estructural —     │               │  funcional —
      «la elección será │               │  «la elección será
      urotomografía»    │               │  ecografía»
                        ▼               ▼
      ┌───────────────────────────────┐  ┌───────────────────────────────┐
      │ rule_imagen_urotomografia    │  │ rule_imagen_ecografia_funcional│
      │ Acción: urotomografía        │  │ Acción: ecografía + residuo   │
      │ Fuente: frag_p3_imagen_      │  │ postmiccional                 │
      │ urotomografia (p3)           │  │ Fuente: frag_p3_imagen_       │
      │                              │  │ ecografia (p3)                │
      └───────────────────────────────┘  └───────────────────────────────┘
```

## Component 5 — Hospitalización → análisis de sangre

```
     ┌──────────────────────────────────────────────┐
     │ rule_hospitalizacion                         │
     │ Condición: OR de 8 criterios de              │
     │ hospitalización (ver §5)                     │
     │ Acción: act_hospitalizar (ADMIT)             │
     │ Fuente: frag_p3_hosp_* (p3)                  │
     └──────────────────────┬───────────────────────┘
                            │
          [FLOW] «En todo paciente con ITU que sea hospitalizado
                  debe obtenerse muestra de sangre…»
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │ rule_analisis_sangre                         │
     │ Acción: hemoleucograma, ionograma, función   │
     │ renal, PCR                                   │
     │ Fuente: frag_p3_analisis_sangre (p3)         │
     └──────────────────────────────────────────────┘
```

---

# 2. Branches and Clinical Alternatives

## [CONTEXTO] ITU alta en gestante — selección empírica según FR / choque

Contexto de presentación (no es una regla canónica, nunca se evalúa). Las tres
alternativas se seleccionan por sus **propias condiciones canónicas**; **no** son
una cadena secuencial (nunca: Cefazolina → Piperacilina → Meropenem).

```
        ┌──────────────────────────────────────────────┐
        │ [CONTEXTO] ITU alta en gestante —            │
        │ selección empírica según FR / choque         │
        │ Evidencia: Tabla 2, marcadores * / ** / ***  │
        │ (frag_p5_t2_itu_alta_row, frag_p5_t2_sin_fr, │
        │ frag_p5_t2_con_fr, frag_p5_t2_con_fr_choque, │
        │ p5)                                          │
        └──────────────┬──────────────┬────────────────┘
                       │              │
        sin FR         │   con FR,    │   con FR,
        (marcador *)   │   sin choque │   con choque
                       │   (marcador  │   (marcador
                       │   **)        │   ***)
                       ▼              ▼                ▼
        ┌───────────────────────────────────────┐ ┌───────────────────────────────────────┐
        │ rule_t2_itu_alta_gestante_cefazolina  │ │ rule_t2_itu_alta_gestante_piperacilina│
        │ Acción: cefazolina                    │ │ Acción: piperacilina tazobactam       │
        │ Fuente: frag_p5_t2_itu_alta_row,      │ │ Fuente: frag_p5_t2_itu_alta_row,      │
        │ frag_p5_t2_sin_fr (p5) · REFERENCE    │ │ frag_p5_t2_con_fr (p5)                │
        │                                       │ │ · BRANCH_CONTEXT                      │
        └───────────────────────────────────────┘ └───────────────────────────────────────┘

        ┌───────────────────────────────────────┐
        │ rule_t2_itu_alta_gestante_meropenem   │
        │ Acción: meropenem                     │
        │ Fuente: frag_p5_t2_itu_alta_row,      │
        │ frag_p5_t2_con_fr_choque (p5)         │
        │ · BRANCH_CONTEXT                      │
        └───────────────────────────────────────┘
```

Nota: en la reconciliación D2.5 las filas BRANCH_CONTEXT son `rel-itu-023`
(piperacilina) y `rel-itu-024` (meropenem); la rama cefazolina («sin FR») comparte
la misma evidencia de marcador (`frag_p5_t2_sin_fr`) documentada en `rel-itu-023` y
se conserva aquí como alternativa del mismo contexto.

---

# 3. Exceptions

El paquete canónico de ITU contiene **3 reglas con excepción**. La fuente declara la
excepción pero **no** declara qué ocurre después: no se inventan destinos ni
terminales. El resultado del motor es `EXCEPTED`.

```
┌──────────────────────────────────────┐
│ rule_citoquimico_orina               │
│ (sospecha de ITU en urgencias)       │
└──────────────────┬───────────────────┘
                   │
                   └── ⚠️ EXCEPTION
                       Condición: mujer + primer episodio + síntomas típicos
                       («excepto mujeres con primer episodio y síntomas típicos»,
                       frag_p2_citoquimico, p2)
                       Outcome: EXCEPTED
                       Destination: NOT DECLARED IN SOURCE

┌──────────────────────────────────────┐
│ rule_urocultivo_indicado             │
│ (sospecha de ITU)                    │
└──────────────────┬───────────────────┘
                   │
                   └── ⚠️ EXCEPTION
                       Condición: mujer + primer episodio + ITU baja no
                       complicada + premenopáusica
                       («excepto primer episodio de ITU baja no complicada en
                       mujer premenopáusica», frag_p3_urocultivo_indicacion, p3)
                       Outcome: EXCEPTED
                       Destination: NOT DECLARED IN SOURCE

┌──────────────────────────────────────┐
│ rule_t1_alta_hosp_con_fr_amikacina   │
│ (ITU alta hospitalaria con FR BGN)   │
└──────────────────┬───────────────────┘
                   │
                   └── ⚠️ EXCEPTION
                       Condición: choque séptico
                       («2 Evitar en choque», frag_p4_t1_nota_amikacina, p4)
                       Outcome: EXCEPTED
                       Destination: NOT DECLARED IN SOURCE
```

**Contexto de excepción (sin arista de flujo):** la fuente añade «3 Administrar
empíricamente si hay choque» (`frag_p4_t1_nota_meropenem`, p4), que corresponde a la
**condición** de `rule_t1_alta_hosp_con_fr_meropenem`. Esto es semántica de
excepción/alternativa condicional (`rel-itu-009`, EXCEPTION_CONTEXT): **no** es la
secuencia «amikacina → meropenem». La selección se resuelve con las condiciones
canónicas de cada regla (con choque → meropenem; sin choque → alternativas
aplicables; amikacina con choque → EXCEPTED).

---

# ⚠️ 4. Unresolved Evidence and Source Gaps

## Source conflicts

El artefacto de reconciliación de ITU **no contiene conflictos de fuente**.

## Extraction / representation gaps

Ninguna. La evidencia clínica de ITU es texto/tabla extraída; la única imagen del
PDF es el logo institucional.

## Source content gaps

- **`rel-itu-050` — Umbral universal de «recuento significativo».** Las definiciones
  de BA e ITU usan «recuento significativo de colonias bacterianas» sin umbral
  numérico universal (`vi_recuento_significativo_umbral`); los umbrales de la página
  3 (≥10⁵ / ≥10³ / ≥10² UFC) son contextuales y pertenecen a las reglas de
  interpretación del urocultivo (`rule_urocultivo_positivo_1e5/1e3/1e2`, ver §5).
  Estado: `GAP` — no se inventó un umbral universal.

## Inferred knowledge

Ningún elemento de ITU tiene estado INFERRED.

## Omisiones deliberadas (OMITTED, fuera de la vía)

- Ajuste según urocultivo/antibiograma (notas 1–2, Tabla 2): instrucción
  procedimental no computable (`rel-itu-060`).
- Cambio a semana 34 / hasta finalización del embarazo (`rel-itu-061`) y «Evitar en
  primer trimestre» (`rel-itu-062`): calendario/ambigüedad de fármaco.
- Criterio de hospitalización pediátrico (`rel-itu-063`), prostatitis (`rel-itu-064`)
  y piuria pediátrica (`rel-itu-065`): fuera del alcance adulto.
- Toma de muestra antes de la primera dosis de antibiótico (`rel-itu-066`):
  instrucción de procedimiento.

---

# 5. Rules Without Reconciled Flow Connection

Estas 46 reglas existen en el paquete canónico pero **no** participan en ninguna
relación FLOW reconciliada. No se fabricaron conectores. (Algunas conservan
relaciones REFERENCE/COMPOSITION en la reconciliación, que son contexto, no flujo.)

| Rule ID | Condición (resumen) | Acción | Estado / fuente |
|---|---|---|---|
| rule_citoquimico_orina | Sospecha de ITU en urgencias (excepción: mujer + 1er episodio + síntomas típicos) | Citoquímico de orina | NORMALIZED · frag_p2_citoquimico (p2) · ⚠️ EXCEPTION |
| rule_def_ba_cultivos | 2 urocultivos (mujer no embarazada) o 1 (hombre/gestante) | — | NORMALIZED · frag_p1_def_ba_cultivos (p1) · COMPOSITION |
| rule_def_ba_piuria_pediatrica | Población pediátrica + ausencia de piuria | — | NORMALIZED · frag_p1_def_ba_piuria (p1) · OMITTED (fuera de alcance) |
| rule_def_itu | Bacteriuria significativa + signos/síntomas de ITU | — | NORMALIZED · frag_p1_def_itu (p1) · REFERENCE |
| rule_def_itu_alto | Infección aguda del riñón + bacteriuria (pielonefritis) | Clasificar ITU alta | SOURCE_STATED · frag_p1_def_itu_alto (p1) · REFERENCE |
| rule_def_itu_bajo | Infección de vejiga/uretra + bacteriuria, sin fiebre ni dolor lumbar ni compromiso sistémico | Clasificar ITU baja | NORMALIZED · frag_p1_def_itu_bajo (p1) · REFERENCE |
| rule_def_itu_complicada_clinica | Pielonefritis / ITU febril bacteriémica / asociada a catéter | — | NORMALIZED · frag_p1_def_itu_complicada_clinica (p1) · OMITTED (prostatitis) |
| rule_ecografia_renal_gestante | Gestante + (pielonefritis o >1 episodio o sospecha de litiasis) | Ecografía renal | NORMALIZED · frag_p3_imagen_gestante (p3) · REFERENCE |
| rule_egreso_afebril_48h | Afebril ≥ 48 horas | — | NORMALIZED · frag_p3_egreso_afebril (p3) · COMPOSITION |
| rule_egreso_comorbilidades | Comorbilidades compensadas | — | SOURCE_STATED · frag_p4_egreso_comorbilidades (p4) · COMPOSITION |
| rule_egreso_fc | FC < 100 lpm | — | SOURCE_STATED · frag_p4_egreso_fc (p4) · COMPOSITION |
| rule_egreso_fr | FR < 24 rpm | — | SOURCE_STATED · frag_p4_egreso_fr (p4) · COMPOSITION |
| rule_egreso_sato2_pao2 | SatO2 > 90 % o PaO2 > 60 | — | SOURCE_STATED · frag_p4_egreso_sato2_pao2 (p4) · COMPOSITION |
| rule_egreso_social | Condiciones sociales lo permiten | — | NORMALIZED · frag_p4_egreso_social (p4) · COMPOSITION |
| rule_egreso_tas | TAS > 90 mmHg | — | NORMALIZED · frag_p3_egreso_tas (p3) · COMPOSITION |
| rule_egreso_tratamiento | Tratamiento ambulatorio asegurado | — | NORMALIZED · frag_p4_egreso_tratamiento (p4) · COMPOSITION |
| rule_egreso_via_oral | Tolerancia a la vía oral | — | SOURCE_STATED · frag_p4_egreso_via_oral (p4) · COMPOSITION |
| rule_fosfomicina_preferida | ITU recurrente o antibióticos en últimos 90 días | — (preferencia declarada) | SOURCE_STATED · frag_p4_t1_nota_fosfomicina (p4) · REFERENCE (nunca selección) |
| rule_fr_bgn_resistentes | Hospitalización >48 h (3 meses) / antibióticos (90 días) / BLEE | — | NORMALIZED · frag_p4_t1_nota_fr (p4) · COMPOSITION + REFERENCE |
| rule_gram_urgencias | En urgencias | Gram de orina | SOURCE_STATED · frag_p3_gram (p3) · REFERENCE |
| rule_hemocultivos | Pielonefritis + (fiebre, hipotermia o choque séptico) | Hemocultivos | NORMALIZED · frag_p3_hemocultivos (p3) · REFERENCE |
| rule_hosp_criterio_absceso | Absceso renal/pararrenal | — | SOURCE_STATED · frag_p3_hosp_absceso (p3) · COMPOSITION |
| rule_hosp_criterio_choque_septico | Choque séptico | — | SOURCE_STATED · frag_p3_hosp_choque_septico (p3) · COMPOSITION |
| rule_hosp_criterio_descompensacion | Descompensación de enfermedad de base | — | SOURCE_STATED · frag_p3_hosp_descompensacion (p3) · COMPOSITION |
| rule_hosp_criterio_funcion_renal | Deterioro de función renal asociado a ITU | — | SOURCE_STATED · frag_p3_hosp_funcion_renal (p3) · COMPOSITION |
| rule_hosp_criterio_germen_resistente | Germen resistente sin opción ambulatoria | — | NORMALIZED · frag_p3_hosp_resistente (p3) · COMPOSITION |
| rule_hosp_criterio_intolerancia_oral | Intolerancia a la vía oral | — | SOURCE_STATED · frag_p3_hosp_intolerancia (p3) · COMPOSITION |
| rule_hosp_criterio_itu_alta | ITU alta | — | SOURCE_STATED · frag_p3_hosp_itu_alta (p3) · COMPOSITION |
| rule_hosp_criterio_soporte_social | Soporte social inadecuado | — | NORMALIZED · frag_p3_hosp_social (p3) · COMPOSITION |
| rule_imagen_urgente | ITU + (choque séptico / FRA / complicación local / fiebre ≥72 h con tto correcto) | Ecografía o TC urgente | NORMALIZED · frag_p3_imagen_urgente (p3) · REJECTED (disparador interno) |
| rule_piuria_mayor_10 | Leucocitos en orina > 10 por campo | — | NORMALIZED · frag_p2_piuria (p2) |
| rule_plan_egreso | AND de 9 criterios de egreso | Alta (DISCHARGE) | NORMALIZED · frag_p3/p4_egreso_* · COMPOSITION |
| rule_t1_alta_hosp_con_fr_amikacina | ITU alta hospitalaria + FR BGN (excepción: choque séptico) | Amikacina | NORMALIZED · frag_p4_t1_con_fr_* (p4) · ⚠️ EXCEPTION |
| rule_t1_alta_hosp_con_fr_meropenem | ITU alta hospitalaria + FR BGN + choque | Meropenem | NORMALIZED · frag_p4_t1_con_fr_* (p4) · EXCEPTION_CONTEXT |
| rule_t1_alta_hosp_con_fr_piperacilina | ITU alta hospitalaria + FR BGN | Piperacilina tazobactam | NORMALIZED · frag_p4_t1_con_fr_* (p4) · REFERENCE |
| rule_t1_alta_hosp_sin_fr | ITU alta hospitalaria sin FR BGN | Cefazolina / amikacina (alternativas) | NORMALIZED · frag_p4_t1_sin_fr (p4) · REFERENCE |
| rule_t1_itu_baja | ITU baja | Nitrofurantoína / cefalexina / fosfomicina (alternativas) | NORMALIZED · frag_p4_t1_itu_baja (p4) · REFERENCE |
| rule_t2_itu_alta_gestante_cefazolina | ITU alta en gestante, sin FR | Cefazolina | NORMALIZED · frag_p5_t2_itu_alta_row, frag_p5_t2_sin_fr (p5) · REFERENCE (rama «sin FR» del contexto) |
| rule_t2_itu_baja_gestante | ITU baja en gestante | Nitrofurantoína / cefalexina / fosfomicina (alternativas) | NORMALIZED · frag_p4_t2_itu_baja_row (p4) · REFERENCE |
| rule_t2_preventiva_alta | ITU alta (gestante) — profilaxis «Sí» | Nitrofurantoína / cefalexina / TMP-SMX / fosfomicina | NORMALIZED · frag_p5_t2_preventiva_alta (p5) · REFERENCE |
| rule_t2_preventiva_baja | ITU baja + recurrencia — «sólo si hay recurrencia» | Nitrofurantoína / cefalexina / TMP-SMX / fosfomicina | NORMALIZED · frag_p4_t2_preventiva_baja (p4) · REFERENCE |
| rule_tc_abscesos_nefritis | Sospecha de absceso/nefritis local | TC con contraste | NORMALIZED · frag_p3_imagen_tc_abscesos (p3) |
| rule_urocultivo_indicado | Sospecha de ITU (excepción: 1er episodio ITU baja no complicada en mujer premenopáusica) | Urocultivo + restricción de muestra | NORMALIZED · frag_p3_urocultivo_indicacion (p3) · ⚠️ EXCEPTION |
| rule_urocultivo_positivo_1e5 | ≥10⁵ UFC + micción espontánea | Clasificar urocultivo positivo | NORMALIZED · frag_p3_urocultivo_positivo_1e5 (p3) · REJECTED (criterio contextual) |
| rule_urocultivo_positivo_1e3 | ≥10³ UFC + síntomas no explicados por otra patología | Clasificar urocultivo positivo | NORMALIZED · frag_p3_urocultivo_positivo_1e3 (p3) · REJECTED (criterio contextual) |
| rule_urocultivo_positivo_1e2 | ≥10² UFC + sonda vesical recién insertada | Clasificar urocultivo positivo | NORMALIZED · frag_p3_urocultivo_positivo_1e2 (p3) · REJECTED (criterio contextual) |

**Notas:**

- Los 8 criterios de hospitalización y `rule_hospitalizacion` forman una
  **COMPOSITION** (OR); los 9 criterios de egreso y `rule_plan_egreso` forman una
  **COMPOSITION** (AND). Estructura lógica, no secuencia clínica.
- Las filas de la Tabla 1 (`rule_t1_*`), la clasificación alta/baja→tratamiento
  (`rel-itu-030`), Gram→tratamiento empírico (`rel-itu-031`), la preferencia de
  fosfomicina (`rel-itu-032`) y BA→riesgo de pielonefritis (`rel-itu-033`) son
  **REFERENCE**: contexto, no flujo.
- Los umbrales de positividad del urocultivo (≥10⁵/10³/10²) son **criterios de
  interpretación contextuales** de cada regla (`rel-itu-014/015/016`, REJECTED como
  aristas); no son una secuencia umbral A → umbral B → umbral C.

---
