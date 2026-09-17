# Clinical Protocol Agent — Technical and Academic Rationale

**A knowledge document for project understanding and thesis defense preparation.**

- Repository: `Side_Project_CPG_Tree_MVP`
- Scope: research prototype for computabilizing institutional clinical practice
  protocols into traceable, versioned, deterministic knowledge artifacts, with a
  defined evolution path toward a Protocol Agent integrated with a medical RAG
  architecture.
- Status statement: this document describes what has been **implemented and
  verified by tests**; everything marked "future work", "intended", or "open
  design question" is **not implemented**. No clinical validation is claimed.
  The system is not production-ready and is not an autonomous clinical
  decision-maker.

---

## Table of contents

1. Problem statement
2. Why clinical guidelines need computational representation
3. What was actually implemented (project evolution)
4. Canonical knowledge model
5. Deterministic engine and three-valued logic
6. Provenance and traceability
7. D2.5 source reconciliation
8. D3 clinical pathway visualization
9. Human-readable Markdown trees
10. Source conflicts and unresolved knowledge
11. Validation and testing strategy
12. Relationship to Computer-Interpretable Guidelines (CIG)
13. Relationship to Clinical Decision Support (CDS)
14. Relationship to Knowledge Representation
15. Relationship to RAG — and why RAG alone is not enough
16. The intended hybrid architecture: RAG + Protocol Agent
17. How the Protocol Agent will eventually work
18. Protocol selection, routing, and variable mapping
19. Weaknesses and limitations
20. Safety and human-in-the-loop
21. Evaluation framework and experimental design
22. Reproducibility and local-first architecture
23. Research contribution and candidate research questions
24. Future roadmap
25. Final academic position
26. References

---

## 1. Problem statement

Institutional clinical practice protocols (guías/protocolos de práctica clínica)
are narrative documents: prose, bullet lists, tables, and flowcharts written by
hospital committees for human clinicians. Two such institutional documents form
the corpus of this project:

- **CT-PL-193 v09** — *Protocolo de práctica clínica de neumonía adquirida en
  comunidad* (NAC), approved 2024-08-12 (7 pages).
- **CT-PL-197 v06** — *Protocolo infección del tracto urinario (ITU) y
  bacteriuria asintomática en población adulta*, approved 2025-09-30 (5 pages).

These documents are authoritative in their institution, but their form is
inconvenient for computation: the clinical logic (criteria, thresholds,
exceptions, alternatives) is embedded in narrative text and tables, is not
machine-executable, and is easy to interpret inconsistently. Meanwhile, modern
assistive systems built on large language models (LLMs) and retrieval-augmented
generation (RAG) can *retrieve and paraphrase* such documents, but they do not
natively *evaluate* the explicit decision logic they contain.

The problem this side project addresses is therefore twofold:

1. **Representation problem.** How can the clinical knowledge of an
   institutional protocol be transformed into structured, traceable, versioned,
   machine-readable knowledge without inventing or silently "correcting" the
   clinical content?
2. **Complementarity problem.** What role can such structured, deterministic
   knowledge play next to a semantic RAG system, so that protocol-oriented
   questions are answered by *executing the protocol's own logic* rather than by
   paraphrasing a retrieved passage?

The project's answer is a layered architecture that keeps **source evidence**,
**structured knowledge**, **presentation**, and **execution** strictly separate.

> Source text ≠ structured knowledge ≠ presentation ≠ execution ≠ generated
> explanation.

---

## 2. Why clinical guidelines need computational representation

Clinical practice guidelines capture institutional consensus about diagnosis,
treatment, and follow-up. Their value for decision support depends on three
properties that narrative text alone provides only weakly:

- **Precision.** Narrative documents tolerate ambiguity (e.g., "recuento
  significativo" without a universal numeric threshold). Computational
  representation forces every threshold, operator, and branch to be explicit —
  or to be *declared* as unresolved.
- **Traceability.** A recommendation is only auditable if it can be traced back
  to the sentence, table, or page that supports it. This is mandatory for
  institutional protocols that change over time.
- **Determinism.** The same protocol version applied to the same patient context
  must yield the same outcome. This is a property of software, not of human
  reading, and it is the property that makes a protocol *testable*.

This motivation is the core subject of the Computer-Interpretable Clinical
Guideline (CIG) research tradition, which Peleg's methodological review
characterizes around recurring themes: knowledge acquisition, representation
languages, execution engines, exception handling, validation and verification,
maintenance and versioning, and sharing (Peleg 2013, PMID 23806274). The side
project deliberately maps each of these themes to a concrete implementation
component (Section 12).

---

## 3. What was actually implemented (project evolution)

The repository evolved in reviewable phases. Each phase added a generic layer;
none of them introduced protocol-specific branches into the infrastructure.

**TABLE 1 — Project evolution / phases**

| Phase | Layer | What it delivered (verified in-repo) |
|---|---|---|
| 0 | Foundation | Data-science template (Python 3.12, uv, ruff, mypy, pre-commit, commitizen, pytest + coverage), Gitflow branch `feature/mvp-foundation` (later phases on `feature/clinical-knowledge-view`, `feature/clinical-pathways`) |
| 1–2 | Canonical knowledge model | `src/cpg_tree/knowledge/`: Protocol, ProtocolVersion, Variable, Condition, LogicalExpression, Rule, Action, Provenance, SourceFragment, ValidationItem, TestCase, TruthValue; explicit YAML serialization |
| 2 | Source extraction | `src/cpg_tree/extraction/`: generic pypdf extraction (v6.19.0), SourceDocument with SHA-256 identity, page text, sectioning, sparse-page detection, reproducible artifacts under `data/02_intermediate/` |
| 3 | Provenance + validation | `src/cpg_tree/validation/`: deterministic package validator (`validate_package`) auditing referential integrity and provenance invariants; validation items |
| 4 | Deterministic engine | `src/cpg_tree/engine/`: pure evaluation of rules with strong Kleene three-valued logic; RuleOutcome semantics; Case model; test-case harness |
| 5 | NAC package | `protocols/CT-PL-193/v09/package.yaml` via builder `src/cpg_tree/protocols/nac_v09.py`: 42 rules, 66 variables, 26 actions, 35 fragments, 30 test cases, 8 validation items |
| 6 | ITU package | `protocols/CT-PL-197/v06/package.yaml` via `itu_v06.py`: 60 rules, 76 variables, 45 actions, 84 fragments, 93 test cases, 12 validation items |
| 7 | Views + CLI | `src/cpg_tree/views/` (technical view, decision-tree projection, provenance chains, evaluation rendering, discovery, case loading) and `src/cpg_tree/cli.py` (`list`, `inspect`, `variables`, `rules`, `provenance`, `tree`, `validate`, `evaluate`, `visualize`) |
| 8 | MVP closure | `docs/mvp-closure.md`; synthetic outcome-demonstration case library (`evaluation/cases/`); three-layer assessment (technical completeness, source traceability, clinical/source fidelity — the latter explicitly NOT established) |
| 9 | Clinical Knowledge View | `src/cpg_tree/views/clinical.py` + `visualization.yaml` manifests: deterministic static SVG map of all rules with static TRUE/FALSE/UNKNOWN lanes; presentation-only reference connectors |
| 10 — D2.5 | Source reconciliation | `src/cpg_tree/reconciliation/` + `evaluation/pathway/<id>-<version>-reconciliation.yaml`: candidate relationship inventories with evidence classes and presentation roles; source-conflict records; human-review workflow |
| 10 — D3 | Clinical pathway visualization | `src/cpg_tree/views/pathway.py` + `pathway_render.py`: typed presentation graph (RULE / BRANCH_CONTEXT / TERMINAL nodes; FLOW / BRANCH edges) rendered as deterministic static SVG inside the existing HTML |
| 10 — reports | Human-readable Markdown trees | `docs/clinical-tree-CT-PL-193-v09.md`, `docs/clinical-tree-CT-PL-197-v06.md` (PR #4, merged into `main`) |

Repository state used for this document: PRs #1–#4 merged; `origin/main` includes
commit `29ea041` ("docs: add human-readable clinical tree reports"); working
branch `feature/clinical-pathways`. Test suite: **849 tests passing**,
approximately 95% line coverage of `src/cpg_tree` (reported by `pytest --cov`).

---

## 4. Canonical knowledge model

The canonical model is a set of immutable dataclasses with explicit enums,
serialized deterministically to YAML. It is the computational source of truth;
everything else (validation, engine, views, reconciliation) reads it.

**TABLE 2 — Canonical knowledge model components**

| Component | File | Purpose |
|---|---|---|
| `Protocol` | `knowledge/protocol.py` | Stable identity of one institutional protocol (id, name, description) |
| `ProtocolVersion` | `knowledge/protocol.py` | Versioned container: variables, rules, actions, test cases, validation items, fragments, documents — keyed by id |
| `Variable` | `knowledge/variables.py` | Typed clinical datum (NUMERIC, CATEGORICAL, BOOLEAN, DURATION) with label, unit, allowed values, provenance |
| `Condition` | `knowledge/conditions.py` | Atomic predicate: COMPARISON (EQ/NE/LT/LE/GT/GE), MEMBERSHIP, FLAG, TEMPORAL (AT_LEAST_FOR_LAST, WITHIN_LAST) |
| `LogicalExpression` | `knowledge/conditions.py` | Composite logic: AND, OR, NOT, AT_LEAST_N(threshold) |
| `Rule` | `knowledge/rules.py` | `applies_to` (population scope) → `condition` → `exceptions` → `action_refs`, plus `validation_status`, `notes`, `provenance` |
| `Action` | `knowledge/rules.py` | Typed consequence: DECISION, REQUEST_TEST, ADMIT, DISCHARGE, PRESCRIBE, FOLLOW_UP, CLASSIFY, EDUCATE, RESTRICTION — **declarative, never executed** |
| `Provenance` | `knowledge/provenance.py` | Derivation state (SOURCE_STATED, EXTRACTED, NORMALIZED, INFERRED, VALIDATED, UNRESOLVED) + fragment refs + reviewer |
| `SourceFragment` | `knowledge/provenance.py` | Verbatim text span anchored to a SourceDocument (page, section) |
| `ValidationItem` | `knowledge/provenance.py` | Explicit record of an ambiguity, gap, or pending review |
| `TestCase` | `knowledge/test_case.py` | Deterministic inputs → expected `TruthValue` per rule |
| `TruthValue` | `knowledge/enums.py` | TRUE, FALSE, UNKNOWN |
| `SourceDocument` | `knowledge/documents.py` | File identity: filename, SHA-256, format, byte size |
| `Case` / `CaseValue` | `engine/case.py` | Runtime inputs: `string \| number \| boolean \| null`; `null` = explicitly missing (UNKNOWN, never FALSE) |

Design decisions worth defending in an oral exam:

1. **Model is data, not behavior.** Knowledge objects carry no evaluation
   methods. This mirrors the CIG literature's separation of a guideline's
   *specification* from its *execution* (see GLIF3's level distinction in
   Section 12) and makes the model serializable, diffable, and testable.
2. **Engine operates over the model.** The engine imports the model, never the
   reverse. A third protocol (the test suite models a synthetic `TEST-PL-999`)
   can be added without touching the engine — the project's central
   architectural test stated in `AGENTS.md`.
3. **References are identifiers, not pointers.** `action_refs` and
   `fragment_refs` are plain ids resolved and audited by the validator, which
   keeps serialization simple and referential integrity explicitly checked.
4. **Versioning is identity.** A protocol version is a separate knowledge
   artifact; nothing silently merges versions. Version + document + fragments +
   rules + tests form one traceable chain.

---

## 5. Deterministic engine and three-valued logic

The engine (`src/cpg_tree/engine/`) evaluates a `Rule` mechanically:

```
applies_to  →  condition  →  exceptions
```

with outcome semantics:

| Outcome | Meaning |
|---|---|
| `MATCHED` | applies_to TRUE, condition TRUE, no exception TRUE |
| `NOT_MATCHED` | condition evaluated FALSE |
| `NOT_APPLICABLE` | applies_to evaluated FALSE |
| `EXCEPTED` | condition TRUE but an exception evaluated TRUE |
| `INDETERMINATE` | a required truth value is UNKNOWN |

Three-valued logic follows strong Kleene semantics; `AT_LEAST_N` uses the exact
formula `t >= k → TRUE; t + u >= k → UNKNOWN; else FALSE`. The engine:

- never executes actions (actions are declarative);
- never mutates the package or the case;
- never reads a clock or performs I/O;
- never consults an LLM;
- raises deterministic errors (`CaseError`, `EngineInputError`,
  `EngineConfigurationError`) on malformed input.

**Why UNKNOWN matters.** A missing clinical datum must not silently become
FALSE, because FALSE *selects the other branch*. Example (NAC): if CURB-65
cannot be computed because the source never defines the scale, then
`rule_hosp_criterio_curb65` must not evaluate to FALSE; it evaluates through
UNKNOWN to INDETERMINATE, and every consumer — including the visualizations —
shows "UNKNOWN → INDETERMINATE (nunca FALSE)". This property is asserted by
tests in both protocol suites and by the missing-data demonstration cases
(`evaluation/cases/`).

The deterministic engine is the component that makes the future Protocol Agent
capable of **reproducible branch traversal** — the property RAG alone cannot
guarantee (Section 15).

---

## 6. Provenance and traceability

Provenance is central, not decorative. Every rule, variable, and action carries a
`DerivationState` and fragment references; every fragment carries a page, a
section, and the verbatim source text; every fragment anchors to a
`SourceDocument` with a SHA-256 hash. The validator enforces invariants such as
`SOURCE_STATED` requiring non-empty evidence, `NORMALIZED` requiring a
transformation note, `INFERRED` being flagged as not-validated, and `UNRESOLVED`
being flagged as not-executable-as-validated-knowledge (`PROV.*` finding codes).

The intended answer shape for the future agent is:

> "This result comes from protocol X, version Y, rule Z, supported by source
> fragment F, page P of document D (SHA-256 H)."

This is also the property that distinguishes the project from "the model says
so": an LLM answer without a pointer to the institutional protocol is not
auditable in a clinical governance setting.

Derivation states deliberately distinguish *what the source states* from *what a
transformation inferred*. In the NAC package this is visible concretely:
`rule_hosp_criterio_curb65` is `UNRESOLVED` (the source references the scale
without defining it) and `rule_uci_bullet1` is `INFERRED` (comma parsing); both
carry visible badges in every presentation layer instead of being silently
normalized.

---

## 7. D2.5 source reconciliation

The source PDFs contain more than clean linear text: flowcharts, tables,
duplicated expressions, contextual references, missing content, and internal
disagreements. Directly turning every observed relationship into a clinical
arrow would be unsafe. D2.5 therefore introduced a **controlled reconciliation
layer** (`src/cpg_tree/reconciliation/`, schema v2) between the canonical
package and the presentation layers.

Two orthogonal dimensions are recorded per candidate relationship:

- **evidence_class** — how the relationship was derived from the source:
  `SOURCE_STATED`, `EXTRACTED`, `NORMALIZED`, `INFERRED`, `UNRESOLVED`.
- **presentation_role** — what the relationship may become in presentation:
  `FLOW`, `REFERENCE`, `COMPOSITION`, `INTERNAL`, `EXCEPTION_CONTEXT`,
  `BRANCH_CONTEXT`, `GAP`, `OMITTED`.

The central semantic rule: **only FLOW relationships with source-class evidence
may become Rule-to-Rule pathway edges**, and INFERRED/UNRESOLVED evidence can
never carry FLOW. Machine checks enforce this (`RECON.*` invariants), and every
candidate keeps `review_status: PROPOSED` until a human reviews it.

Reconciled counts (committed artifacts `evaluation/pathway/<id>-<version>-
reconciliation.yaml`):

- **NAC**: 30 candidates — 18 READY_FOR_REVIEW, 2 CONFLICT, 1
  INFERRED_STRUCTURE, 1 UNRESOLVED_MAPPING, 2 GAP, 4 REJECTED, 2 OMITTED;
  9 FLOW relationships; 4 source conflicts (SC-NAC-001…004).
- **ITU**: 43 candidates — 31 READY_FOR_REVIEW, 4 REJECTED, 7 OMITTED, 1 GAP;
  8 FLOW relationships; 1 presentation BRANCH_CONTEXT; 1 presentation terminal;
  3 EXCEPTION_CONTEXT relationships; 0 conflicts.

The distinction defended here is the project's most important architectural
decision:

> Source evidence ≠ presentation relationship ≠ clinical workflow ≠ executable
> rule.

A table row is not a workflow arrow; a duplicated expression is not sequencing;
a declared preference ("Preferir en…") is not a selection; an exception without
a declared destination is not a transition. The reconciliation layer makes
these distinctions machine-checkable instead of leaving them to the
imagination of a renderer.

---

## 8. D3 clinical pathway visualization

D3 (`src/cpg_tree/views/pathway.py`, `pathway_render.py`) consumes the D2.5
contract to render a typed presentation graph:

- **RULE nodes** — exactly one per canonical rule (invariant tested: 42/42 NAC,
  60/60 ITU).
- **BRANCH_CONTEXT nodes** — presentation-only anchors (ITU: "ITU alta en
  gestante — selección empírica según FR/choque"); never canonical rules, never
  evaluated.
- **TERMINAL nodes** — presentation-only (ITU: "diagnóstico descartado").
- **Edges** — `FLOW` (rule→rule, or rule→typed terminal) and `BRANCH`
  (context→rule), each carrying its D2.5 candidate id and fragment refs.

Layout is pure Python and deterministic: Kahn-style layering with sorted
tie-breaking, cycles appended deterministically as a final layer (with a
visible note — never a crash, never an invented direction), connected
components packed shortest-column-first, uniform node height guaranteeing no
overlaps. Output is static SVG with pure `<text>` (no foreignObject), no
JavaScript, no external resources, byte-identical across runs.

Safety invariants tested: no medication sequence is ever rendered as flow
(amikacina→meropenem, cefazolina→piperacilina, piperacilina→meropenem are
prohibited); exceptions render inside the rule node without invented
destinations; UNKNOWN lanes appear in every node; conflicts, gaps, and inferred
structures surface as badges and notices, never as edges.

D3 is a **presentation layer**. It never modifies canonical knowledge, never
evaluates conditions, and never imports the engine.

---

## 9. Human-readable Markdown trees

After D3, two plain-Markdown audit documents were produced
(`docs/clinical-tree-CT-PL-193-v09.md`, `docs/clinical-tree-CT-PL-197-v06.md`,
published in PR #4). Where D3 is the machine-generated presentation, the
Markdown trees are the human-readable audit artifact: Unicode box drawings,
branch labels, and plain tables, with no SVG, JavaScript, or Mermaid.

They implement the same semantic contract: only reconciled FLOW relationships
become transitions; rules without FLOW connections are listed explicitly
(30 NAC, 46 ITU) rather than forced into a tree; the four NAC source conflicts,
the page-6 flowchart extraction gap, the missing treatment content, the CURB-65
gap, the inferred bullet structure, and the ITU universal-threshold gap all
remain visibly unresolved. Coverage is machine-verified (42/42 and 60/60 rule
ids; 9/9 and 8/8 FLOW markers). This is the artifact layer intended for
professor review, clinical review, and the thesis document itself.

---

## 10. Source conflicts and unresolved knowledge

Unresolved information is a *feature of the system's honesty*, not merely a
failure. The following items are documented, machine-checked, and preserved in
every layer (reconciliation YAML, D3 badges/notices, Markdown trees):

**TABLE 9 (in place) — Human review / unresolved evidence**

| Item | What it represents | Why it cannot be safely resolved | Human action required |
|---|---|---|---|
| SC-NAC-001 | CURB-65 threshold: text says "≥2" (p4), diagram reported "> 2" (p6) | Diagram is a raster image not machine-readable; the two representations disagree | Visual confirmation of p6; institutional adjudication |
| SC-NAC-002 | BUN threshold: text "BUN > 30" vs diagram "BUN > 20" | Same as above | Visual confirmation; adjudication |
| SC-NAC-003 | UCI-UCE criterion count/set: text "3 of 9" vs diagram potentially different | Same as above | Visual confirmation; adjudication |
| SC-NAC-004 | "TAS < 90": absent in textual list, reported present in diagram | Same as above | Visual confirmation; adjudication |
| rel-nac-050 | Page-6 diagnostic/management flowchart exists only as an embedded image | No text layer; OCR/vision unavailable in the toolchain; reconstruction would fabricate flow | Human reading of the original PDF |
| rel-nac-051 | Empirical antibiotic treatment section: heading present, body absent from the PDF (no text, no image on pages 4–5) | The content is not in the source document | Verify whether an authoritative source document exists |
| rel-nac-052 | CURB-65 scale: referenced but not defined in the source | Definition absent | Adjudicate SC-NAC-001 first, then revisit |
| rel-nac-043 | `rule_uci_bullet1` comma-separated sentence parsed as OR of five alternatives | Punctuation is the only structural evidence | Human validation before any clinical use |
| rel-itu-050 | "Recuento significativo" without a universal threshold | Source defines thresholds only per context (p3) | Institutional decision on a universal definition |

The design rule throughout: inventing a value, a threshold, or a transition
would be **worse** than exposing UNKNOWN/GAP, because a fabricated clinical
value is indistinguishable from a source-derived one in downstream use.

---

## 11. Validation and testing strategy

The validation stack is layered and each layer has a distinct meaning:

| Layer | What it checks | Where |
|---|---|---|
| Package validation | Referential integrity, provenance invariants (`PROV.*`), serialization identity | `src/cpg_tree/validation/` |
| Engine tests | Three-valued truth tables, AT_LEAST_N formula, outcome order, purity (no mutation), deterministic errors | `tests/unit/engine/` |
| Protocol acceptance | Positive/negative/boundary/missing-data cases per protocol; five engine outcomes demonstrated with committed synthetic cases | `tests/protocols/`, `evaluation/cases/` |
| View invariants | Every rule rendered exactly once; UNKNOWN lanes; exception lanes only where canonical; escaping; no scripts; byte determinism | `tests/unit/views/` |
| Reconciliation invariants | INFERRED/UNRESOLVED can never be FLOW; no wildcards; conflicts ≥2 representations and never pick winners; byte-stable round-trip | `tests/unit/reconciliation/` |
| Pathway invariants | Exact FLOW topology per protocol; no forbidden medication sequences; terminals are not rules; branch anchors are presentation-only; cycles don't crash | `tests/unit/views/test_pathway*` |
| Markdown coverage | 42/42 and 60/60 rule coverage; FLOW marker counts | verified programmatically (reporting phase) |
| Quality gates | ruff, mypy, pre-commit, `make check`, `git diff --check` | repository Makefile |

Final state: **849 tests passing**; `make check` green; ~95% line coverage of
`src/cpg_tree`.

The distinction that must survive any defense:

> **Software correctness ≠ clinical correctness.** The tests prove that the
> implementation faithfully behaves according to the encoded artifacts and
> architectural invariants. They do **not** prove that the original clinical
> guideline was interpreted correctly in every unresolved area, and they do
> not constitute clinical validation (this is stated explicitly in
> `docs/mvp-closure.md`).

---

## 12. Relationship to Computer-Interpretable Guidelines (CIG)

The project belongs conceptually to the CIG research tradition, without
implementing any established CIG formalism.

**Peleg's methodological review** (PMID 23806274) organizes CIG research around
knowledge acquisition, modeling languages, acquisition/specification
methodologies, EHR/workflow integration, validation and verification, execution
engines, exception handling, maintenance, versioning, and sharing. The mapping
to this project:

| Literature concept | Project implementation | Remaining gap |
|---|---|---|
| Knowledge acquisition | PDF extraction + structured modeling by knowledge engineers | Manual/assisted, not automated end-to-end |
| Representation | Protocol / Variable / Condition / Rule / Action | Subset of CIG expressiveness (see below) |
| Validation | `validate_package()` + reconciliation checks | Structural/provenance only, not clinical |
| Execution | Deterministic rule engine | No workflow/sequence execution model |
| Exception handling | Canonical exception semantics + EXCEPTION_CONTEXT | No destination semantics (source declares none) |
| Versioning | Protocol + ProtocolVersion + document hashes | Institutional change workflow not modeled |
| Traceability | Provenance + SourceFragment | Human-readable review still pending for most rules |

**GLIF3** (Boxwala et al., PMID 15196480) introduced the key distinction
between three levels of a guideline specification: the *conceptual flowchart*,
the *computable specification*, and the *implementable specification*. This
project deliberately separates the analogous levels:

- conceptual level → the human-readable Markdown trees (Section 9);
- computable level → the canonical package + reconciliation semantics;
- implementable level → the deterministic engine contract.

The project does **not** implement GLIF3; it is conceptually compatible with
the idea that one guideline needs several representation levels with different
purposes and audiences.

**PROforma** (Sutton & Fox, PMID 12807812) demonstrated that guidelines can be
modeled as executable process models (plans, decisions, actions, enquiries)
with explicit semantics. This project shares the *idea* of explicit decision
and action types (DECISION, REQUEST_TEST, PRESCRIBE…) with *declarative*
semantics, but does not implement PROforma's process/workflow model, and
claims no compliance.

**Arden Syntax** (PMID 22342733) is a historical standard for shareable medical
logic modules (MLMs), and its maintenance/validation experience is directly
relevant to the project's provenance and versioning choices. The project does
not use Arden Syntax; it only borrows the lesson that executable medical
knowledge needs versioning, provenance, and review machinery.

**Representation primitives literature** (PMID 12467791) surveys the primitives
found across guideline models — actions, decisions, patient states, execution
states, sequences, alternatives, loops, temporal constraints. The current
model implements: actions (typed), decisions (conditions/rules), alternatives
(multiple declarative PRESCRIBE actions + BRANCH_CONTEXT presentation),
execution states (RuleOutcome), and a minimal temporal vocabulary
(AT_LEAST_FOR_LAST, WITHIN_LAST). **Loops and arbitrary sequences are not
modeled** — an explicit, documented limitation (Section 19).

---

## 13. Relationship to Clinical Decision Support (CDS)

Classical CDS literature (e.g., PMID 10094063, "Computer-based guideline
implementation systems") identifies what moves a system from "text available"
to "decision support": patient-specific recommendations, explanation services,
integration with care processes, and evaluation. The project implements the
*content and explanation* foundations (rules + provenance + deterministic
outcomes) but deliberately does **not** implement integration (no EHR
connection, no order entry, no autonomous recommendation delivery), which
keeps it on the safe side of the "research prototype, not a production CDS"
line drawn in `AGENTS.md`. The contemporary scoping review (PMID 38148352)
shows this remains an active research direction spanning content extraction,
knowledge representation, verification, and CDS integration — which is exactly
the arc this project follows.

---

## 14. Relationship to Knowledge Representation

Knowledge representation (KR) distinguishes *syntax*, *semantics*, and
*inference*. This project's KR choices are deliberately conservative:

- **Syntax**: typed dataclasses + explicit YAML — boring but diffable,
  serializable, and tool-friendly.
- **Semantics**: deterministic three-valued evaluation defined in the engine,
  separate from the syntax. The meaning of a Rule is the engine's evaluation
  function; nothing else interprets it.
- **Inference**: none beyond the explicit logic. There is no probabilistic
  reasoning, no ontology reasoning, no default logic. Where the source is
  ambiguous, the system represents the ambiguity (UNRESOLVED, INFERRED, GAP,
  CONFLICT) instead of inferring through it.

The reconciliation layer extends this: it adds a small, checked *meta-vocabulary*
(presentation roles, evidence classes) so that what is allowed to become a
pathway edge is decided by evidence, not by layout convenience.

---

## 15. Relationship to RAG — and why RAG alone is not enough

RAG (Lewis et al., 2020) augments parametric LLM knowledge with retrieved,
non-parametric evidence, improving grounding and updateability. In healthcare,
systematic reviews report real benefits but also heterogeneous evaluation,
ethical concerns, and a lack of standardized validation (PMID 40498738;
PMID 39812777), and scoping reviews distinguish text RAG, knowledge-graph-
enhanced RAG, agentic RAG, and multimodal RAG (PMID 41118646).

A pure RAG pipeline is excellent at:

- retrieving evidence and relevant passages;
- answering natural-language questions;
- grounding generated text in citations.

A pure RAG pipeline does **not** inherently provide:

- deterministic rule execution;
- explicit three-valued logic;
- reproducible branch traversal;
- formal exception semantics;
- guaranteed application of a specific protocol *version*;
- executable condition/action semantics with test coverage.

Concretely: for "¿cumple este paciente los criterios de hospitalización del
protocolo NAC v09?", RAG retrieves the bullets and the LLM paraphrases them;
the Protocol Agent evaluates `rule_hospitalizacion` over mapped variables and
returns MATCHED/NOT_MATCHED/INDETERMINATE plus provenance — the same answer
every time, for the same inputs. These are **complementary**, not competing,
capabilities.

---

## 16. The intended hybrid architecture: RAG + Protocol Agent

This architecture is **future work**. Nothing below is implemented as an
integrated system.

```
                          USER
                            |
                            v
                     RAG ORCHESTRATOR
                            |
              +-------------+-------------+
              |                           |
              v                           v
       GENERAL RAG                 PROTOCOL AGENT
              |                           |
              v                           v
      document retrieval          protocol selection
      semantic retrieval          structured rules
      source grounding            deterministic engine
              |                           |
              +-------------+-------------+
                            |
                            v
                   RESPONSE COMPOSER
                            |
                            v
                     USER / CLINICIAN
```

The orchestrator should **not** blindly delegate every question to the Protocol
Agent. Routing examples:

- "What does the protocol say about hospitalization criteria?" → Protocol Agent
  + provenance.
- "What does the cited study say about test sensitivity?" → General RAG.
- "According to the protocol, does this patient satisfy the hospitalization
  criteria, and what evidence supports it?" → Protocol Agent (evaluation) +
  RAG (supporting source context).

This routing logic is a future architecture, not fully implemented.

**Why the Protocol Agent exists.** It handles a different class of information
than a retriever:

> Narrative evidence ("what does the guideline say?") ≠ computable normative
> logic ("given these inputs, which explicit rule conditions are satisfied?").

The Protocol Agent's intended guarantees: deterministic evaluation, explicit
conditions, explicit outcomes, explicit UNKNOWN, provenance, protocol version,
source traceability, reproducible results, auditable decision paths. It solves
only the subset of knowledge that has been successfully formalized — and it
says so.

---

## 17. How the Protocol Agent will eventually work

Illustrative future request lifecycle ("Según el protocolo de NAC, ¿este
paciente cumple criterios para hospitalización?"):

1. Orchestrator classifies the question as protocol-oriented.
2. Relevant protocol (and version) is selected.
3. Protocol Agent loads the canonical package.
4. Patient/context data is mapped to canonical variables.
5. Missing variables remain UNKNOWN.
6. The engine evaluates the rules deterministically.
7. Provenance is attached to the result.
8. RAG may retrieve the supporting source fragments.
9. The response composer generates a human-readable explanation.
10. The user receives: result, applicable rule, conditions, source, protocol
    and version, uncertainty, and warnings where relevant.

**The LLM must not silently override deterministic engine results.** If an LLM
is used to *explain* the result, explanation and execution remain conceptually
separate components.

---

## 18. Protocol selection, routing, and variable mapping

**Protocol selection** (open design question): how does the orchestrator know
to invoke the Protocol Agent? Candidate strategies: metadata-based routing, a
protocol registry, semantic retrieval over protocol descriptions, a
classifier/router, hybrid retrieval + rules, or explicit user selection. Each
has precision/recall and governance trade-offs; none is chosen yet.

**Variable mapping** (major future research challenge): the protocol consumes
age, sex, symptoms, laboratory values, vital signs, diagnoses, medication
history, and findings; the user provides natural language or the EHR provides
structured data. The mapping

```
Natural language / EHR data → canonical variables → rule engine
```

is **not solved by the current MVP**. Future sources include FHIR resources,
EHR APIs, structured clinical databases, terminology mapping, and NLP
extraction. Terminology alignment (institutional codes → canonical variable
ids) is the principal interoperability cost and connects directly to the
CQL/FHIR Clinical Reasoning literature (Section 20).

---

## 19. Weaknesses and limitations

**TABLE 7 — Known limitations**

| Area | Limitation | Status |
|---|---|---|
| Source | PDF text extraction; image-only flowchart (NAC p6) not machine-read; OCR not implemented; tables flattened by extraction | Known; visible as GAP/UNRESOLVED |
| Source | NAC treatment section body absent from the PDF itself | Source gap; not an extraction bug |
| Knowledge engineering | Manual reconciliation; most rules PROPOSED, not human-approved | Human review pending |
| Knowledge engineering | Two protocols only; generalization beyond the pair is demonstrated synthetically (`TEST-PL-999`) | Limitation of corpus |
| Semantics | Temporal reasoning minimal (durations only; no calendars/scheduling) | Documented in validation items (`vi_temporal_no_representable`, `vi_semana34_calendar`) |
| Semantics | No full clinical ontology; no terminology normalization | Future work |
| Engine | No workflow/sequence execution; no loops; no probabilistic reasoning; no causal inference; no drug-interaction or treatment-optimization logic | Out of scope by design |
| Engine | Actions are declarative and never executed; no order/planning | Out of scope by design |
| AI | LLM not used for rule outcomes (by design); future agent still requires safeguards | By design / future |
| AI | RAG can retrieve incorrect or incomplete evidence; generated explanations require evaluation | Inherent to RAG; future evaluation needed |
| Clinical | No clinical validation; no prospective evaluation; no clinician approval of all rules; no deployment; no evidence of patient-outcome improvement | Not claimed |

---

## 20. Safety and human-in-the-loop

The intended control loop is:

```
LLM proposes → structured knowledge constrains → deterministic engine evaluates
→ provenance explains → human validates / supervises
```

The system is not, and must not be described as, autonomous clinical
decision-making. It is a research prototype for knowledge representation and
decision support whose outputs are inspectable artifacts (packages,
evaluations, visualizations, reports). Even the future agent is conceived as a
supervised assistant, with the human deciding and the system showing its work.

---

## 21. Evaluation framework and experimental design

**TABLE 8 — Future evaluation metrics (proposal; nothing measured yet)**

| Layer | Metrics (proposal) |
|---|---|
| Extraction quality | source-fragment coverage; extraction accuracy vs original PDF |
| Knowledge representation | rule completeness; condition/action correctness; provenance coverage |
| Engine correctness | deterministic test cases; expected outcomes; branch coverage; UNKNOWN behavior |
| Retrieval quality | Precision@k, Recall@k, MRR, nDCG@k |
| Generated response | faithfulness, answer relevance, citation correctness, completeness |
| Clinical expert evaluation | correctness, completeness, interpretability, usefulness, safety, inter-reviewer agreement |
| System performance | retrieval latency, rule-evaluation latency, total response latency |

Different metrics evaluate different layers; collapsing them into one score
would obscure which layer fails.

**Candidate experimental comparison (hypotheses only, no results):** baseline
pure semantic RAG vs RAG + Protocol Agent, asking whether the structured
addition improves factual correctness, citation/source traceability, resistance
to hallucinated protocol recommendations, consistency across repeated queries,
handling of explicit clinical conditions, retrieval ambiguity, and response
faithfulness.

---

## 22. Reproducibility and local-first architecture

Reproducibility mechanisms already in place: Git + Gitflow; versioned protocol
packages with builder↔artifact byte-identity tests; source document hashes;
deterministic extraction, engine, visualization, and serialization; committed
synthetic evaluation cases; reconciliation artifacts with machine-checked
invariants. These properties matter academically because they make the
*knowledge engineering process* auditable, not just the final software.

The project is **local-first**: no cloud service is required for any core
function. Benefits: institutional control, reduced external data exposure,
offline operation, reproducible demos. But local execution is **not** security:
authentication, authorization, audit logging, encryption, and model governance
remain separate engineering concerns for any future deployment.

---

## 23. Research contribution and candidate research questions

The project does **not** claim to invent a new CIG formalism. Its potential
contribution is the *combination*: source extraction + structured clinical
knowledge representation + provenance + deterministic three-valued execution +
explicit source reconciliation + human-auditable pathways + a defined
integration path with RAG, in a small, reproducible, local-first prototype.

**Candidate research questions (proposals, not final):**

- RQ1: Can institutional guideline knowledge be transformed into a structured
  representation that preserves source traceability and deterministic rule
  semantics?
- RQ2: Does adding a computable Protocol Agent to a semantic RAG system improve
  retrieval-grounded answers to protocol-oriented clinical questions?
- RQ3: Does deterministic rule execution reduce inconsistencies in
  protocol-based responses compared with pure LLM/RAG generation?
- RQ4: How much human effort is required to convert institutional guidelines
  into validated computable knowledge?
- RQ5: How should unresolved source evidence be represented so that
  uncertainty is preserved rather than silently resolved?

---

## 24. Future roadmap

**TABLE 10 — Future roadmap**

| Stage | Activity | State |
|---|---|---|
| 1 | Human validation of D2.5 candidates (NAC 18 + ITU 31) | Planned (pending) |
| 2 | Resolve source conflicts/gaps where authoritative evidence exists (SC-NAC-001…004, rel-nac-050/051/052, rel-itu-050) | Planned |
| 3 | Expand protocol coverage (third/fourth protocols) | Planned |
| 4 | Improve terminology/variable mapping | Research question |
| 5 | Integrate Protocol Agent with RAG orchestrator | Future work |
| 6 | Implement protocol routing/selection | Open design question |
| 7 | Patient/EHR structured data integration | Future work |
| 8 | Evaluation against pure RAG baseline | Research question |
| 9 | Clinical expert evaluation | Planned |
| 10 | Security/governance/deployment research | Future work |

---

## 25. Final academic position

This project should be understood as a prototype for transforming narrative
clinical protocols into traceable, structured, and deterministically evaluable
knowledge artifacts. Its conceptual foundation belongs to the established
field of computer-interpretable clinical guidelines and clinical decision
support; its integration with the broader thesis RAG architecture is intended
to complement semantic retrieval with explicit protocol reasoning rather than
to replace RAG. The current implementation demonstrates the engineering
feasibility of the knowledge-representation, provenance, reconciliation, and
deterministic-evaluation layers. Source reconciliation, clinical validation,
terminology mapping, patient-data integration, and empirical comparison with
pure RAG remain open research and validation tasks.

---

## 26. References

### Peer-reviewed literature (verified identifiers as cited)

1. **Peleg, M.** "Computer-interpretable clinical guidelines: a methodological
   review." *Journal of Biomedical Informatics*, 2013. PMID 23806274.
   DOI 10.1016/j.jbi.2013.06.009.
   *Relevance:* primary conceptual reference for CIG themes (acquisition,
   languages, validation, execution, exceptions, maintenance, versioning,
   sharing) mapped to this project in Section 12.

2. **Boxwala et al.** "GLIF3: a representation format for sharable
   computer-interpretable clinical practice guidelines." *Journal of Biomedical
   Informatics*, 2004. PMID 15196480. DOI 10.1016/j.jbi.2004.04.002.
   *Relevance:* the conceptual-flowchart / computable / implementable
   specification-level distinction adopted by this project's layered
   architecture.

3. **Sutton & Fox.** "The syntax and semantics of the PROforma guideline
   modeling language." *JAMIA*, 2003. PMID 12807812. DOI 10.1197/jamia.M1264.
   *Relevance:* precedent for executable process-oriented guideline models
   with explicit decisions/actions; the project shares the idea, not the
   formalism.

4. "The Arden Syntax standard for clinical decision support: experiences and
   directions." PMID 22342733.
   *Relevance:* historical standard for executable medical knowledge modules;
   its validation/maintenance experience motivates the project's provenance
   and versioning machinery. The project does not use Arden Syntax.

5. "Representation primitives, process models and patient data in
   computer-interpretable clinical practice guidelines: a literature review of
   guideline representation models." PMID 12467791.
   *Relevance:* inventory of guideline primitives (actions, decisions, patient
   states, execution states, sequences, alternatives, loops, temporal
   constraints) used to position the current model's coverage and gaps
   (Section 12).

6. "Computer-based guideline implementation systems: a systematic review of
   functionality and effectiveness." PMID 10094063.
   *Relevance:* motivates patient-specific recommendations, explanation
   services, care integration, and evaluation as the properties that separate
   CDS from passive documentation (Section 13).

7. "The Application of Computer Technology to Clinical Practice Guideline
   Implementation: A Scoping Review." PMID 38148352.
   *Relevance:* situates content extraction, representation, verification, and
   CDS integration as an active contemporary research direction.

8. **Lewis et al.** "Retrieval-Augmented Generation for Knowledge-Intensive NLP
   Tasks." NeurIPS, 2020.
   *Relevance:* foundational RAG reference: parametric vs external knowledge,
   retrieval, grounding; motivates the hybrid architecture (Sections 15–16).

9. **Liu et al.** "Improving large language model applications in biomedicine
   with retrieval-augmented generation: a systematic review, meta-analysis,
   and clinical development guidelines." 2025. PMID 39812777.
   *Relevance:* biomedical RAG state of the art, evaluation practice, and
   clinical development guidance. Numerical findings are not reproduced here
   and are not assumed to transfer to this prototype.

10. "Retrieval augmented generation for large language models in healthcare: A
    systematic review." *PLOS Digital Health*, 2025. PMID 40498738.
    *Relevance:* documents heterogeneous evaluation, ethical considerations,
    and missing standardized validation in healthcare RAG — the exact gaps the
    Protocol Agent layer is intended to mitigate structurally.

11. "Improving Large Language Model Applications in the Medical and Nursing
    Domains With Retrieval-Augmented Generation: Scoping Review." PMID 41118646.
    *Relevance:* taxonomizes text RAG, knowledge-graph-enhanced RAG, agentic
    RAG, and multimodal RAG; positions the future orchestrator + Protocol
    Agent architecture within that taxonomy.

### Formal standards / specifications (not peer-reviewed research)

12. **HL7 Clinical Quality Language (CQL), Release 1** — specification at
    cql.hl7.org.
    *Relevance:* the de-facto expression language of computable clinical
    quality knowledge; comparison target in Sections 19–20. The project does
    not implement CQL.

13. **HL7 FHIR Clinical Reasoning Module** — hl7.org/fhir (Clinical Reasoning).
    *Relevance:* FHIR-based representation of clinical knowledge artifacts and
    their evaluation; relevant to the future variable-mapping problem.

14. **CDS Hooks** — specification at cds-hooks.hl7.org.
    *Relevance:* standard mechanism for invoking CDS services from clinical
    workflows; relevant to any future integration of the Protocol Agent with
    clinical systems.

15. **HL7 Arden Syntax** (ANSI/HL7 standard).
    *Relevance:* formal standards context for item 4 above.

### Project documentation (primary sources for implementation claims)

16. `AGENTS.md` — governing architecture and working rules.
17. `docs/mvp-closure.md` — Phase 8 closure: technical completeness, source
    traceability, and the explicit statement that clinical/source fidelity is
    NOT established.
18. `docs/phase-10-source-reconciliation.md` — D2.5 methodology, decisions, and
    presentation-semantics contract.
19. `docs/phase-10-d3-clinical-pathway.md` — D3 pathway view design and
    invariants.
20. `docs/clinical-tree-CT-PL-193-v09.md`, `docs/clinical-tree-CT-PL-197-v06.md`
    — human-readable pathway audit reports.

---

## Appendix: required diagrams

**Diagram 1 — Current side-project architecture (implemented)**

```
        SOURCE PDFs (data/01_raw, immutable, hashed)
                     │
                     ▼
        EXTRACTION (pypdf, pages/sections/fragments)
                     │
                     ▼
        CANONICAL KNOWLEDGE PACKAGES (protocols/<id>/<version>/package.yaml)
                     │
        ┌────────────┼──────────────────┬──────────────────┐
        ▼            ▼                  ▼                  ▼
   VALIDATION    D2.5 RECONCILIATION  DETERMINISTIC     PRESENTATION (views/)
   (integrity/   (evaluation/pathway/  ENGINE             ├─ technical view
   provenance)   *-reconciliation.yaml)(TRUE/FALSE/      ├─ clinical map
                     │                 UNKNOWN;           ├─ D3 pathway SVG
                     ▼                 outcomes)          └─ Markdown trees
              relationship contract        │
                     └──────────┬──────────┘
                                ▼
                   D3 PATHWAY PRESENTATION GRAPH
                   (consumes the contract; never invents)
```

**Diagram 2 — Source → knowledge → engine → agent pipeline (future)**

```
SOURCE → RECONCILIATION → CANONICAL MODEL → ENGINE → PROTOCOL AGENT → USER
```

**Diagram 3 — Relationship of the five layers**

```
   Source evidence (PDF text/tables/images)
          ↓ reconciles
   Reconciliation contract (roles + evidence classes)
          ↓ constrains
   Canonical model (rules/conditions/actions, never edited by presentation)
          ↓ executes
   Engine (deterministic three-valued evaluation)
          ↓ explains
   Presentation (SVG pathway, technical cards, Markdown trees)
```

**Diagram 4 — Future RAG + Protocol Agent architecture** (see Section 16).

**Diagram 5 — Future user-question flow** (see Section 17, steps 1–10).

---

*End of document. Version: based on repository state at `origin/main` =
e456093 (PR #4 merged), working branch `feature/clinical-pathways`, 849 tests
passing.*
