# Phase 10 — D2.5 Source Reconciliation Report

Status: **reconciled against source evidence — NOT clinically validated and NOT
approved.** All candidates keep `review_status: PROPOSED`; nothing here converts
the inventories into approved clinical logic.

Terminology: outputs below are "source-reconciled" and "structurally/source
reviewed". Nothing in this report claims clinical validity, and no source
conflict has been resolved.

## 1. Scope

- Two relationship inventories (`evaluation/pathway/*-relationships.md`) were
  reviewed candidate by candidate against the original PDFs (text layer, page
  layout, embedded-object inventory) and the canonical packages.
- Result: two machine-validated reconciliation records
  (`evaluation/pathway/*-reconciliation.yaml`) plus this report.
- The canonical model, engine, and packages were NOT modified (§ "Canonical
  model impact" in the session report).

## 2. Source documents

| | CT-PL-193 v09 (NAC) | CT-PL-197 v06 (ITU) |
|---|---|---|
| Protocol code | CT-PL-193 | CT-PL-197 |
| Version | v09 | v06 |
| document_id | doc-3a1654757801b7b6 | doc-800af94bc0654138 |
| Filename | CT-PL-193 PROTOCOLO PRACTICA CLINICA NEUMONIA ADQUIRIDA EN COMUNIDAD -NAC (v9-ago-2024) (5).pdf | CT-PL-197 PROTOCOLO INFECCION TRACTO URINARIO -ITU ADULTOS (v6-sep-2025).pdf |
| Pages | 7 | 5 |
| SHA-256 | 3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882 | 800af94bc0654138a8e213cd1e42ad2e6021a955226a142b36c5b3f24e24777a |
| Embedded images (pdfimages) | p1 logo; p2 "Gráfico 1. Etiología" (1200×742); p6 flowchart (1270×976) | p1 logo only |
| Source representation types | TEXT, TABLE (n/a — no treatment tables in text layer), IMAGE, DIAGRAM | TEXT, TABLE |

## 3. Method

PDF-first review: for every candidate, (1) the quoted evidence was re-verified
against the package fragments and the extracted page text (`data/02_intermediate`),
(2) the PDF object inventory (`pdfimages -list`) was used to distinguish
extraction limitation from source absence, (3) the raw page-6 content stream of
NAC was inspected to confirm the flowchart is raster-only, and (4) each candidate
was reclassified with the decision hierarchy FLOW / REFERENCE / COMPOSITION /
GAP / OMITTED / SOURCE_CONFLICT. Machine checks enforce the invariants
(`src/cpg_tree/reconciliation/`), including: INFERRED and UNRESOLVED evidence can
never carry FLOW; wildcard ids are rejected; every GAP/OMITTED row retains
evidence; conflicts carry at least two representations and never pick a winner.

Environment limitation, stated honestly: this environment has no vision and no
OCR, so the NAC page-6 raster flowchart could not be machine-read. Its existence
is verified; its internal content remains subject to human visual confirmation,
and every claim about its content is recorded as `PENDING_VISUAL_CONFIRMATION`.

## 4. NAC results (30 candidates)

| Reconciliation status | Count | Candidates |
|---|---|---|
| READY_FOR_REVIEW | 18 | rel-nac-002, 003, 005, 006, 009–017, 030, 031, 040, 044, 045 |
| INFERRED_STRUCTURE | 1 | rel-nac-043 |
| CONFLICT | 2 | rel-nac-041, 042 (SC-NAC-003) |
| UNRESOLVED_MAPPING | 1 | rel-nac-050 |
| GAP | 2 | rel-nac-051, 052 |
| REJECTED | 4 | rel-nac-001, 004, 007, 008 |
| OMITTED | 2 | rel-nac-060, 061 |

Final presentation roles: FLOW 9 · REFERENCE 4 · COMPOSITION 6 · GAP 3 ·
OMITTED 6 · INTERNAL 2.

Key NAC decisions:

- **Flowchart (p6)**: exists as DIAGRAM evidence (single 1270×976 raster between
  "ALGORITMOS DE DIAGNÓSTICO Y MANEJO:" and "REFERENCIAS BIBLIOGRÁFICAS:",
  confirmed via the content-stream analysis: one image operator, no flowchart
  text objects). It is **not** a source gap: it is an extraction limitation.
  rel-nac-050 → `UNRESOLVED_MAPPING` + `source_representation: DIAGRAM`.
- **Treatment section**: page 4 ends at the "TRATAMIENTO ANTIBIÓTICO EMPÍRICO:"
  heading; page 5 starts with "PLAN DE EGRESO."; **neither page contains an
  embedded image** (pdfimages: images only on pages 1, 2, 6). The treatment body
  is genuinely absent from this PDF — `SOURCE_CONTENT_ABSENT`, not an extraction
  limitation. rel-nac-051 remains GAP with corrected evidence.
- **CURB-65 / BUN / criterion count / TAS<90**: recorded as four OPEN,
  UNRESOLVED source conflicts (see §6); the diagram side of each is
  `PENDING_VISUAL_CONFIRMATION`. No threshold was corrected; the canonical
  package is untouched.
- **Panels (rel-nac-014/015)**: FLOW → REFERENCE; no exclusivity in the source;
  "como primera opción" is a declared preference (vi_filmarray_seleccion_panel).
- **Variable-triggered gates (001, 004, 007, 008)**: REJECTED as edges — the
  triggers are conditions inside the rules themselves (node semantics for D3).
- **Discharge actions (016, 017)**: FLOW → INTERNAL (`relation: attaches`); the
  actions already belong to `rule_plan_egreso`; never Rule→Action pathway edges;
  the temporal anchors ("al momento del alta", "4 semanas") remain declarative
  action metadata.
- **Labs → hospitalization (005)**: stays FLOW but with `relation: supports`
  ("apoya la decisión de hospitalización") — a support relationship, not a
  strict temporal sequence.
- **UCI bullet (043)**: stays COMPOSITION with INFERRED evidence
  (`INFERRED_STRUCTURE`); never FLOW, presentation must show the non-validated
  badge (vi_uci_bullet1_parsing).

## 5. ITU results (43 candidates)

| Reconciliation status | Count | Candidates |
|---|---|---|
| READY_FOR_REVIEW | 31 | rel-itu-001–013, 017, 018, 020–026, 030–033, 040–044 |
| REJECTED | 4 | rel-itu-014, 015, 016, 019 |
| OMITTED | 7 | rel-itu-060–066 |
| GAP | 1 | rel-itu-050 |

Final presentation roles: FLOW 8 · REFERENCE 13 · COMPOSITION 5 · GAP 1 ·
OMITTED 11 · EXCEPTION_CONTEXT 3 · BRANCH_CONTEXT 2.

Key ITU decisions:

- **BA vs ITU (001)**: FLOW → REFERENCE; definitional contrast is not a workflow
  transition. The entry split is classification/node semantics in D3.
- **Table rows (005–008)**: FLOW → REFERENCE; row applicability is a contextual
  mapping, not a transition. Table layout never implies workflow.
- **Amikacin/meropenem (009)**: FLOW → EXCEPTION_CONTEXT (`relation: excepts`,
  branch "excepción (choque)") — exception/conditional-alternative semantics
  driven by the canonical `choque_septico` exception and condition; never a
  drug-to-drug sequence, never an ordinary FLOW edge.
- **Exceptions (012/013)**: FLOW → EXCEPTION_CONTEXT; destination remains
  `EXCEPTED: destino no declarado en la fuente` — no invented terminal states.
- **Gestante branches (023/024)**: FLOW → BRANCH_CONTEXT with a single
  presentation-only anchor (`BRANCH_CONTEXT: ITU alta en gestante — selección
  empírica según FR/choque`); cefazolina / piperacilina tazobactam / meropenem
  are condition-based alternatives, never a sequential chain.
- **Tirilla terminal (011)**: stays FLOW toward `TERMINAL: diagnóstico
  descartado` — a presentation-only terminal (the state is named by the
  source), never a new canonical Rule.
- **Culture thresholds (014–016)**: REJECTED; contextual positivity criteria are
  each rule's own condition, not edges between rules.
- **Wildcard (019)**: eliminated; the 72 h temporal trigger is condition
  semantics of `rule_imagen_urgente` (vi_fiebre_72h_dos_condiciones).
- **Conditional tests (021/022)**: FLOW → REFERENCE; the additional conditions
  (fever/hypothermia/shock; pregnancy/episodes/lithiasis) belong to each rule.
- **Preventive therapy (025/026)**: FLOW → REFERENCE; "Sólo si hay recurrencia"
  and the "Sí" cell are conditions/attributes, not workflow.
- Source headings "Indicaciones de hospitalización…" / "Indicaciones para paso a
  terapia oral y/o egreso:" exist in the page text layer but are not package
  fragments; cited in `source_location` (rel-itu-041/042). No "se dará de alta"
  sentence exists in the ITU source.

## 6. Source conflicts

| conflict_id | topic | representation A | representation B | page(s) | status |
|---|---|---|---|---|---|
| SC-NAC-001 | CURB-65 hospitalization threshold | TEXT: "Escala de severidad CURB-65 ≥2" (VERIFIED_TEXT) | DIAGRAM: "CURB > 2" (PENDING_VISUAL_CONFIRMATION) | 4 / 6 | OPEN — UNRESOLVED |
| SC-NAC-002 | UCI-UCE BUN threshold | TEXT: "BUN > 30" (VERIFIED_TEXT) | DIAGRAM: "BUN > 20" (PENDING_VISUAL_CONFIRMATION) | 4 / 6 | OPEN — UNRESOLVED |
| SC-NAC-003 | UCI-UCE criterion count/set | TEXT: "3 o más criterios" + 9 criteria (VERIFIED_TEXT) | DIAGRAM: potentially different count/set (PENDING_VISUAL_CONFIRMATION) | 4 / 6 | OPEN — UNRESOLVED |
| SC-NAC-004 | "TAS < 90" presence in UCI-UCE | TEXT: criterion absent from textual list (VERIFIED_TEXT) | DIAGRAM: "TAS < 90" present (PENDING_VISUAL_CONFIRMATION) | 4 / 6 | OPEN — UNRESOLVED |

No winner is declared anywhere. The canonical rules remain exactly as extracted
from the text layer. The diagram side of each conflict is recorded as reported
by the human reviewer and requires final visual confirmation because the raster
image is not machine-readable in this environment.

## 7. Image-derived evidence

- **NAC page 6 flowchart**: exists (raster, 1270×976 px). Content not
  machine-readable here (no OCR/vision). Its mapping to canonical rules is
  UNRESOLVED_MAPPING (rel-nac-050) and its reported discrepancies are held in
  SC-NAC-001…004 with PENDING_VISUAL_CONFIRMATION. Human visual reading is a
  required D3 input.
- **NAC page 2 "Gráfico 1. Etiología…"**: image (1200×742 px) of institutional
  etiology data; epidemiological evidence, no decision relationship
  inventoried.
- **NAC pages 4–5**: no embedded images — the missing treatment body is source
  absence, not an image we failed to read.
- **ITU**: the only image is the institutional logo; all clinical evidence is
  text/tables, fully machine-verified.

## 8. Remaining unresolved items

| Kind | Item |
|---|---|
| Extraction limitation | NAC p6 flowchart content (machine-unreadable raster). |
| Source absence | NAC empirical antibiotic treatment body (heading only; no text, no image on pages 4–5). |
| Ambiguous source | NAC rule_uci_bullet1 comma structure (INFERRED, stays flagged). |
| Source conflict | SC-NAC-001…004 (thresholds, criterion set, TAS<90). |
| Unresolved mapping | NAC flowchart → canonical rules (rel-nac-050). |
| Unresolved canonical | ITU "recuento significativo" without universal threshold (rel-itu-050). |
| Non-computable by design | Calendar constructs (semana 34, primer trimestre), procedural instructions (antibiograma, toma de muestra), future scheduling (48 h / 4 semanas). |

## 9. Presentation semantics contract (D3 input)

This reconciliation layer is a presentation/reconciliation aid: it never alters
the canonical computable protocol package. The following principles are
enforced by machine checks (`src/cpg_tree/reconciliation/`) and by the
committed-artifact tests:

1. **FLOW is reserved for source-supported transitions/dependencies/branches
   between specific Rules.** It requires SOURCE_STATED/EXTRACTED/NORMALIZED
   evidence and at least one fragment or source location. Presentation-only
   anchors can never be FLOW sources.
2. **REFERENCE represents contextual/documentary relationships and is not
   workflow.** Classification/definitional context, table-row applicability,
   and declared preferences stay REFERENCE.
3. **COMPOSITION represents internal logical structure and is not workflow.**
   OR/AND/AT_LEAST_N compositions and duplicated `applies_to` expressions never
   become sequential edges.
4. **EXCEPTION_CONTEXT represents exceptions by the canonical Rule exception
   mechanism.** An exception does not imply a destination unless the source
   explicitly declares one; `EXCEPTED:` pseudo-refs carry no invented terminal.
5. **INTERNAL represents relationships inside a Rule.** Actions belong to Rules
   (canonical `action_refs`) and never become Rule→Action pathway edges; their
   temporal metadata remains declarative.
6. **BRANCH_CONTEXT represents condition-based alternatives.** Alternatives are
   selected by their own canonical conditions, never rendered as sequential
   chains (amikacina→meropenem and cefazolina→piperacilina→meropenem are
   prohibited as FLOW).
7. **Presentation-only branch contexts and terminals are not canonical Rules.**
   `BRANCH_CONTEXT:` anchors and `TERMINAL:` targets are presentation-only.
8. **UNKNOWN remains UNKNOWN.** No reconciliation decision silently converts
   missing information into FALSE or any other value.
9. **No missing source content is invented.** GAP rows retain their evidence
   and never receive fabricated thresholds, criteria, or rules.
10. **Conflicts, gaps, and inferred structures remain explicitly marked.**
    SOURCE_CONFLICT records never pick a winner; INFERRED evidence never becomes
    FLOW.

## 10. Readiness for D3

- **READY_FOR_REVIEW** (human may approve in D3): NAC 18 candidates; ITU 31
  candidates. Approval is a human act; this report approves nothing.
- **INFERRED_STRUCTURE**: rel-nac-043 — only presentable with a non-validated
  badge, never as flow.
- **CONFLICT**: rel-nac-041, 042 — blocked until the human resolves or
  documents SC-NAC-003.
- **UNRESOLVED_MAPPING**: rel-nac-050 — blocked until the human visually reads
  the flowchart.
- **GAP**: NAC treatment section, CURB-65 definition, ITU universal threshold —
  represented as explicit GAP terminals if D3 proceeds.
- **REJECTED / OMITTED**: 10 NAC + 11 ITU candidates remain in the audit trail
  with their evidence and rejection rationale.

The resulting pathway, when D3 is executed, will be a source-reconciled
representation — not a clinically validated workflow.
