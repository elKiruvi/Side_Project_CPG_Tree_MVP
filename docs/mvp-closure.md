# MVP Closure Report

Phase 8 of Side_Project_CPG_Tree_MVP. This document closes the MVP and states,
with reproducible evidence, what the prototype demonstrates and what it does
not. It deliberately separates three assessment layers:

1. **Technical completeness** — structural consistency, deterministic
   execution, reproducibility, validation, test coverage, package integrity.
2. **Source traceability** — computable elements can be traced back to source
   fragments and source documents.
3. **Clinical/source fidelity** — whether the computable representation
   faithfully captures the intended clinical meaning of the original
   guideline.

**Layers 1 and 2 are demonstrated by the MVP. Layer 3 is NOT established.**
Technical completeness and provenance coverage are not evidence of clinical
validity or clinical semantic fidelity, and this report never treats them as
such.

All numbers below are derived programmatically from the canonical packages
(`protocols/<id>/<version>/package.yaml`) and the deterministic tooling; none
are hardcoded in the reporting code.

---

## 1. Technical completeness

### 1.1 Canonical packages

Both real protocols are committed as versioned knowledge artifacts:

| Protocol | Version | Approval date |
|---|---|---|
| CT-PL-193 (NAC) | v09 | 2024-08-12 |
| CT-PL-197 (ITU) | v06 | 2025-09-30 |

`package.yaml` is the canonical source of truth. The Python builders
(`src/cpg_tree/protocols/nac_v09.py`, `itu_v06.py`) are generators; the
committed artifact is byte-identical to the builder output and the identity
is pinned by tests (`test_yaml_artifact_matches_builder_exactly` in both
protocol structure suites).

### 1.2 Evidence matrix

Reproduce with:

```bash
uv run python -m cpg_tree inspect CT-PL-193 v09 --json
uv run python -m cpg_tree inspect CT-PL-197 v06 --json
```

| Metric | CT-PL-193 v09 | CT-PL-197 v06 |
|---|---|---|
| Documents | 1 | 1 |
| Fragments | 35 | 84 |
| Variables | 66 | 76 |
| Rules | 42 | 60 |
| Actions | 26 | 45 |
| Test cases (package harness) | 30 | 93 |
| Validation items | 8 | 12 |
| Validation errors / warnings / info | 0 / 0 / 2 | 0 / 0 / 0 |
| Test-case harness result | 30/30 pass | 93/93 pass |

### 1.3 Validation

The deterministic validator (`validate_package`) audits referential integrity
and provenance invariants only; it never evaluates conditions and never
claims clinical validity. Both packages validate with zero errors and zero
warnings. The NAC package carries exactly two INFO findings, each pinned by
tests to an exact `(code, path)` pair:

- `PROV.UNRESOLVED_NOT_EXECUTABLE` on `rule_hosp_criterio_curb65`
  (see §3.4).
- `PROV.INFERRED_NOT_VALIDATED` on `rule_uci_bullet1` (see §3.3).

`is_valid()` means "no traceability errors", nothing more.

### 1.4 Deterministic execution

- Same package + same case = same result: asserted by repeat-evaluation
  tests in both protocol suites and by the engine unit tests.
- Evaluation is pure: the package is never mutated
  (`test_package_evaluation_does_not_mutate_the_package`).
- Three-valued logic follows strong Kleene semantics; `AT_LEAST_N` uses the
  exact formula `t >= k → TRUE; t + u >= k → UNKNOWN; else FALSE`.
- Missing information evaluates to UNKNOWN, never FALSE
  (engine unit tests + `test_missing_data_preserves_unknown_not_false` in
  both protocol suites).
- Malformed input and unresolvable configuration raise deterministic errors
  (`CaseError`, `EngineInputError`, `EngineConfigurationError`).

### 1.5 Reproducibility

- Builder → `package.yaml` byte identity (tested).
- Serialization round-trips (`package → YAML → package` equality, tested).
- `validate`, `inspect`, `evaluate`, `tree`, `provenance` outputs are
  deterministic (JSON/text stable; `evaluate --json` repeat-run equality is
  tested in the CLI journeys).
- HTML visualization is byte-deterministic (tested).

### 1.6 Test coverage

`uv run pytest` runs the full suite (currently 659 tests, ~95% line coverage
of `src/cpg_tree`), including generic engine tests, protocol tests for both
packages, CLI integration journeys, and agnosticism guards (generic layers
never import protocol builders; a third protocol is modeled by a synthetic
package in tests without touching generic infrastructure).

---

## 2. Source traceability

### 2.1 Provenance coverage

Reproduce with the two `inspect` commands above.

| Coverage | CT-PL-193 v09 | CT-PL-197 v06 |
|---|---|---|
| Rules with source evidence | 42/42 | 60/60 |
| Variables with source evidence | 66/66 | 76/76 |
| Actions with source evidence | 26/26 | 45/45 |
| Fragments with document | 35/35 | 84/84 |
| Fragments with page | 35/35 | 84/84 |
| Fragments with verbatim text | 35/35 | 84/84 |

### 2.2 The traceability chain

Every rule, variable, and action carries `Provenance` with fragment refs.
Every fragment anchors to a content-addressed `SourceDocument`
(SHA-256 over the source PDF bytes). The chain is:

```text
execution result → rule → provenance → fragment (verbatim text, page, section)
→ document (filename, sha256) → original source PDF
```

Walkthrough:

```bash
uv run python -m cpg_tree provenance CT-PL-197 v06 --rule rule_t1_itu_baja
```

When the local extraction artifacts exist (`data/02_intermediate/`), the
traceability tests additionally verify that each fragment's verbatim text
occurs verbatim on its cited page
(`tests/protocols/*/test_*_source_traceability.py`), and the chain tests
re-extract the raw PDFs and confirm content-addressed identity
(`tests/integration/{nac,itu}/test_*_chain.py`). Raw PDFs are source data and
are never committed to Git, so those tests skip when the PDFs are absent —
the committed packages remain fully usable either way.

Provenance coverage is a traceability fact. **It is not a clinical accuracy
metric**: 100% coverage means every element points at a source fragment, not
that the encoding captures the clinical intent of that fragment.

---

## 3. Clinical/source fidelity

**Status: not established.** The MVP provides fidelity *signals* — an honest
accounting of how each element was derived from its source — but no element
in either package has been clinically reviewed or validated. Every rule
carries `validation_status = EXTRACTED` (or `UNRESOLVED` for one NAC rule);
none carries `REVIEWED` or `VALIDATED`. The MVP does not establish that the
computable representation faithfully captures the intended clinical meaning
of the original guidelines, and this report does not claim it does.

The content of both packages falls into these categories (counts derived
from the packages via the `inspect` commands):

### 3.1 Directly extracted content

`DerivationState.SOURCE_STATED` — the element mirrors a source statement
verbatim, with fragment evidence:

| Element kind | CT-PL-193 v09 | CT-PL-197 v06 |
|---|---|---|
| Rules | 19 | 15 |
| Variables | 47 | 53 |
| Actions | 22 | 17 |

### 3.2 Normalized content

`DerivationState.NORMALIZED` — the element consolidates source wording into
one canonical concept; the transformation must be documented in
`provenance.notes` (enforced by validator warnings when missing):

| Element kind | CT-PL-193 v09 | CT-PL-197 v06 |
|---|---|---|
| Rules | 21 | 45 |
| Variables | 18 | 23 |
| Actions | 4 | 28 |

Normalized content is transformed content, not source-stated content; it
carries a higher review burden than directly extracted content.

### 3.3 Inferred content

`DerivationState.INFERRED` — content inferred by a transformation process,
not stated by the source. It must not be treated as validated knowledge
(validator emits `PROV.INFERRED_NOT_VALIDATED`):

- CT-PL-193 v09: 1 rule (`rule_uci_bullet1`).
- CT-PL-197 v06: none.

### 3.4 Unresolved content

`DerivationState.UNRESOLVED` or open validation items — the source did not
support a faithful formalization, so the gap is explicit:

- CT-PL-193 v09: 1 rule + 1 variable (the CURB-65 score and its
  hospitalization criterion). The rule is still mechanically evaluated, and
  evaluation output marks it "UNRESOLVED derivation — not validated
  knowledge".
- CT-PL-197 v06: no UNRESOLVED elements.

Open validation items recording ambiguities or pending review:

- CT-PL-193 v09: 8 OPEN.
- CT-PL-197 v06: 12 OPEN.

### 3.5 Content requiring clinical validation

Strictly: **all** rules in both packages (42 + 60), plus every normalized,
inferred, or unresolved element and every open validation item. The MVP
treats nothing as clinically validated, and no reviewer has marked any
element `VALIDATED`. Clinical review is an explicit next step outside the
MVP scope.

---

## 4. Engine outcome demonstration

The deterministic engine produces exactly five outcomes. The committed
synthetic case library (`evaluation/cases/`, synthetic, non-patient data)
demonstrates them reproducibly:

```bash
uv run python -m cpg_tree evaluate CT-PL-193 evaluation/cases/CT-PL-193/v09/nac_matched.json
uv run python -m cpg_tree evaluate CT-PL-197 evaluation/cases/CT-PL-197/v06/itu_excepted.json
```

| Outcome | NAC case | ITU case |
|---|---|---|
| MATCHED | `nac_matched.json` | `itu_matched.json` |
| NOT_MATCHED | `nac_not_matched.json` | `itu_not_matched.json` |
| NOT_APPLICABLE | `nac_not_applicable.json` | `itu_not_applicable.json` |
| INDETERMINATE | `nac_indeterminate.json` | `itu_indeterminate.json` |
| EXCEPTED | **not reachable** (see below) | `itu_excepted.json` |

Tests pin these outcomes: `tests/protocols/{nac,itu}/test_*_outcome_
demonstration.py` plus CLI journey tests. The UNKNOWN semantics are
demonstrated by `nac_indeterminate.json` / `itu_indeterminate.json` (`null`
→ UNKNOWN → INDETERMINATE, never FALSE).

**Honest gap:** CT-PL-193 v09 contains no rule with an exception, so
`EXCEPTED` is not demonstrable on real NAC knowledge. It is demonstrated
generically by the engine unit tests and at package level for ITU. No
exception was invented to fill the gap.

---

## 5. MVP limitations

What the MVP does **not** demonstrate or provide:

- **No clinical validation.** Software tests, validation reports, and
  provenance coverage say nothing about clinical correctness of the encoded
  rules. The packages are `EXTRACTED`, not reviewed.
- **No clinical fidelity guarantee.** Fidelity signals (derivation states,
  validation items) exist, but formal assessment of clinical semantic
  fidelity against the source guidelines has not been performed and would
  require clinical expertise.
- **Manual knowledge engineering.** Rule encoding is done by human-authored
  builders; the extraction stage automates only document/page/fragment
  extraction. Full automatic rule extraction from PDFs is out of scope.
- **Raw PDFs are not committed.** Chain tests that re-extract source PDFs
  run only where the local raw data exists.
- **TestCase projection limitation.** `run_test_cases` projects EXCEPTED and
  NOT_APPLICABLE onto FALSE because `TestCase.expected_results` supports
  only TruthValue. Full outcomes remain available per-rule on
  `RuleEvaluation`; the demonstration cases above exercise them directly.
- **Population/scope is descriptive only.** Scope lives in the protocol
  `description`; there is no structured population model.
- **Temporal data is modeled as scalar durations** (e.g. `afebril_horas`)
  with explicit temporal conditions; there is no timeline/event model.
- **Actions are declarative.** The engine never executes actions; multiple
  `PRESCRIBE` actions are source-declared alternatives, never selections.
- **No production features.** No EHR integration, no FHIR/CQL, no RAG/LLM
  dependency, no database, no network service; local-first by design.

---

## 6. MVP acceptance criteria and status

| # | Criterion | Status |
|---|---|---|
| 1 | Generic protocol metadata | Met (both packages) |
| 2 | Generic protocol ingestion | Met (content-addressed extraction) |
| 3 | Source document extraction | Met (pages, sections, fragments) |
| 4 | Structured knowledge representation | Met (canonical model) |
| 5 | Explicit conditions and rules | Met (42 + 60 rules) |
| 6 | Provenance | Met (100% coverage, see §2) |
| 7 | Deterministic rule evaluation | Met (see §1.4) |
| 8 | TRUE/FALSE/UNKNOWN semantics | Met (UNKNOWN never FALSE) |
| 9 | Protocol-specific test cases | Met (30/30, 93/93) |
| 10 | Support for both initial protocols | Met |
| 11 | Reproducible execution | Met (see §1.5) |
| 12 | Basic traceable outputs | Met (CLI views + visualization) |

All criteria are demonstrated by the automated test suite; none of them
asserts clinical validity.

## 7. Final closure statement

The MVP demonstrates, for both real institutional protocols, a working chain:

```text
source PDF → extraction artifacts → canonical package.yaml → validation
→ deterministic rule evaluation → provenance traceability → derived views
```

Technical completeness and source traceability are established with
reproducible evidence. Clinical/source fidelity remains open: the packages
are faithful *records* of what was extracted, normalized, inferred, or left
unresolved, but not yet validated clinical knowledge. Closing the clinical
gap requires expert review of every rule, variable, and action against the
source documents — work that belongs after the MVP.
