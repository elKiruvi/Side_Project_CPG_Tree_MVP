# Phase 10 — D3: Clinical Pathway Visualization

Status: **presentation layer implemented; NOT clinically validated.** D3
presents the D2.5-reconciled relationships; it never discovers or infers
clinical relationships.

> **D3 no descubre ni infiere relaciones clínicas nuevas; únicamente presenta
> relaciones reconciliadas en D2.5.**

## 1. Purpose

The `visualize` command now renders a third, clinically oriented view — the
**Vía clínica de decisión** — as the first section of the self-contained
static HTML document:

```
Vía clínica de decisión  (D3 pathway, new)
Vista de conocimiento clínico  (Phase 9 map, unchanged)
Vista técnica  (unchanged)
```

Every Rule node links to its Technical View card; every technical card links
back to its pathway node. The Technical View is not replaced.

## 2. Relationship between D2.5 and D3

- D2.5 (`evaluation/pathway/<id>-<version>-reconciliation.yaml`) is the
  semantic contract; D3 consumes it with the existing reconciliation loader
  and re-validates it in strict mode before rendering. Invalid
  reconciliation fails clearly (`ValueError` → CLI exit code 1); an absent
  artifact renders an explicit notice while the other views remain available.
- D3 adds no new relationship semantics. Every presentation edge carries its
  D2.5 `candidate_id` and fragment ids.

## 3. Presentation graph model

`src/cpg_tree/views/pathway.py` builds a typed presentation graph:

- **RULE node** — exactly one per canonical Rule (Rule node invariant:
  NAC 42 nodes, ITU 60 nodes; tested).
- **BRANCH_CONTEXT node** — presentation-only anchor (`BRANCH_CONTEXT: …`),
  never a canonical Rule, never evaluated.
- **TERMINAL node** — presentation-only terminal (`TERMINAL: …`), never a
  canonical Rule (e.g., ITU «diagnóstico descartado»).
- **Edges** — `FLOW` (Rule→Rule, or Rule→TERMINAL exclusively for typed
  terminals) and `BRANCH` (context→Rule), each with its candidate id,
  branch label, and fragment ids.

## 4. FLOW policy

Only D2.5 candidates with `presentation_role = FLOW` create pathway edges,
and every FLOW edge must have canonical Rule endpoints (or an explicitly
typed presentation terminal). The authoritative FLOW list lives in the
reconciliation artifacts — the generic renderer contains no protocol ids.
FLOW means the source explicitly establishes a transition, dependency, or
branch between the concrete rules; it does not mean "these rules look
related".

## 5. Presentation-only elements

- **Branch contexts**: `rel-itu-023/024` render as one context node —
  «ITU alta en gestante — selección empírica según FR/choque» — with branches
  «con FR, sin choque» → piperacilina tazobactam and «con FR, con choque» →
  meropenem. The cefazolina alternative («sin FR») is documented in the
  candidate evidence; the context node is presentation-only and is never
  serialized into the canonical package nor evaluated by the engine.
- **Terminals**: `rel-itu-011` renders «Diagnóstico descartado» as a
  presentation terminal; it is not counted among the 60 Rule nodes and not
  added to the package.

## 6. Exception semantics

`EXCEPTION_CONTEXT` candidates (rel-itu-009/012/013) never create topology.
The canonical Rule exception mechanism is rendered inside the Rule node
(«EXCEPCIÓN n … excepción TRUE → EXCEPTED»), including amikacina's
`choque_septico` exception. No invented destinations, no invented terminals.
Medication sequences are prohibited: no FLOW edge may connect
amikacina→meropenem, cefazolina→piperacilina, or piperacilina→meropenem
(tested).

## 7. UNKNOWN semantics

Every Rule node shows the engine's static lanes:
`TRUE → MATCHED`, `FALSE → NOT_MATCHED`, `UNKNOWN → INDETERMINATE (nunca
FALSE)`. UNKNOWN is never presented as FALSE.

## 8. Non-topological D2.5 roles

- **INTERNAL** (rel-nac-016/017): no Rule→Action pathway edges; the
  declarative actions remain inside the Rule node's action section (and the
  Technical View).
- **REFERENCE / COMPOSITION**: omitted from pathway topology (preserved in
  reconciliation/provenance). Compositions are visible only as the canonical
  condition text inside the nodes.
- **GAP / UNRESOLVED_MAPPING**: rendered as deterministic notices under the
  SVG plus per-rule badges (e.g., CURB-65 GAP badge).
- **CONFLICT**: per-rule «conflicto de fuente sin resolver» badges plus the
  SC-NAC-001…004 notices; never resolved in presentation.
- **INFERRED_STRUCTURE**: «estructura inferida — no validada» badge; never
  FLOW.

## 9. Deterministic layout

Pure Python layout in `src/cpg_tree/views/pathway_render.py`:

- Kahn-style layering with sorted tie-breaking; residual cycles are appended
  deterministically as a final layer (with a visible note) — never crashes,
  never deletes edges, never invents direction.
- Connected components ordered by smallest node key and packed
  shortest-column-first into at most four columns; disconnected rules remain
  visible without manufactured connectors.
- Uniform node size (height of the tallest node) guarantees no overlapping
  boxes (tested).
- Rule-id ordering is used only as a deterministic layout fallback; it never
  creates edges.
- Byte-deterministic output: no timestamps, no randomness, no browser
  measurements (tested twice-render equality for both protocols).

## 10. SVG requirements

Static, self-contained SVG: pure `<text>` lines (no `foreignObject`), no
JavaScript, no external assets, escaped text, fixed line heights, predictable
wrapping. Grayscale-safe semantics: node kind is encoded by border style
(solid / dashed / dotted pill) and by explicit labels, never by color alone.

## 11. CLI

`visualize` gained an optional `--reconciliation PATH` argument. When
omitted, the artifact is auto-discovered from
`protocols/<id>/<version>/reconciliation.yaml` or
`evaluation/pathway/<id>-<version>-reconciliation.yaml`. Missing explicit
path → deterministic operational error (exit 1); absent auto-discovery → the
pathway section shows the explicit "no reconciliation artifact" notice.

## 12. Limitations

- NAC page 6 flowchart: image evidence not machine-readable; the pathway
  uses the reconciled text layer only, and the diagram conflicts remain
  visible (SC-NAC-001…004).
- NAC treatment section: source content absent; shown as a GAP notice, never
  reconstructed.
- No automatic clinical workflow inference: the graph presents exactly the
  reconciled relationships, including disconnected rules and open conflicts.
- This view is a research presentation; it is not clinical validation.

## 13. Files

- `src/cpg_tree/views/pathway.py` — presentation graph model, builder, and
  validation (D2.5 consumption).
- `src/cpg_tree/views/pathway_render.py` — deterministic layout and static
  SVG renderer.
- `src/cpg_tree/views/visualize.py` — three-view HTML integration and
  cross-links.
- `src/cpg_tree/cli.py` — `--reconciliation` argument and artifact
  auto-discovery.
- Tests: `tests/unit/views/test_pathway.py`,
  `tests/unit/views/test_pathway_render.py`,
  `tests/unit/views/test_pathway_protocols.py`,
  `tests/integration/cli/test_cli_pathway.py`.
