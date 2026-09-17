# AGENTS.md

## 1. Project identity and purpose

This repository is **Side_Project_CPG_Tree_MVP**.

It is a research and engineering prototype for transforming institutional
clinical practice protocols into structured, traceable, versioned, and
executable computational knowledge.

The project is intended to investigate how narrative clinical protocols can
be transformed into computable representations that preserve clinical
meaning, provenance, uncertainty, exceptions, and decision logic.

The initial protocol corpus contains two institutional protocols:

- **CT-PL-193** — Protocolo de práctica clínica de neumonía adquirida en
  comunidad — version 9 — approved 2024-08-12.
- **CT-PL-197** — Protocolo infección del tracto urinario (ITU) y
  bacteriuria asintomática en población adulta — version 06 — approved
  2025-09-30.

The architecture must support additional protocols in the future without
requiring protocol-specific implementation in the generic pipeline or rule
engine.

This is a **research prototype**. It is not a production clinical
decision-support system, does not replace clinical judgment, and must not be
treated as an autonomous clinical decision maker.

---

## 2. Core architectural principle: protocol-agnostic infrastructure

The most important architectural requirement is **generalizability across
multiple clinical protocols**.

The project must implement reusable infrastructure for:

- protocol ingestion
- document extraction
- segmentation
- normalization
- knowledge representation
- rule modeling
- validation
- deterministic rule evaluation
- execution tracing
- protocol packaging
- testing
- evaluation
- visualization
- CLI workflows

Adding a new protocol should primarily require adding protocol-specific
knowledge artifacts, source data, metadata, and configuration.

Adding a new protocol must **not** normally require creating a new engine such
as:

```text
NACEngine
ITUEngine
```

Do not hardcode protocol-specific clinical logic into the generic engine.

Avoid patterns such as:

```python
if protocol_id == "CT-PL-193":
    ...
elif protocol_id == "CT-PL-197":
    ...
```

Clinical knowledge belongs in protocol-specific knowledge artifacts, not in
generic software infrastructure.

---

## 3. Separation between software and clinical knowledge

The project has two clearly separated layers.

### Generic software infrastructure

This includes:

- ingestion
- extraction
- normalization
- knowledge models
- rule models
- deterministic engine
- validation
- execution tracing
- pipelines
- CLI
- visualization
- tests
- evaluation utilities

### Protocol-specific knowledge

This includes:

- protocol metadata
- protocol version
- population/scope
- clinical concepts
- clinical variables
- conditions
- composite conditions
- thresholds
- ranges
- temporal conditions
- rules
- actions
- exceptions
- alternatives
- provenance
- validation status
- protocol-specific test cases

The generic infrastructure consumes protocol knowledge. It must not encode
the clinical meaning of NAC, ITU, or future protocols directly in Python.

---

## 4. Source documents and data policy

Original institutional protocol PDFs are **raw source data**.

They belong under:

```text
data/01_raw/
```

The raw source documents are immutable inputs to the project pipeline.

Do not modify the source PDFs.

Do not commit the original clinical PDFs to Git.

Do not commit generated raw/intermediate data artifacts unless the repository
explicitly defines them as version-controlled artifacts.

The existing `.gitignore` intentionally ignores `data/**` while preserving
the directory structure, `data/README.md`, and `.gitkeep` files. Preserve
this behavior unless there is a documented reason to change it.

Source documents must remain traceable through metadata such as:

- protocol identifier
- version
- source filename
- approval date when available
- source document status

---

## 5. Protocol versioning

Protocol versions are independent knowledge artifacts.

Never silently overwrite or merge distinct protocol versions.

For example:

```text
CT-PL-193
└── v09

CT-PL-197
└── v06
```

A future revision must be represented as a separate version.

The computable representation must preserve the relationship between:

```text
protocol
    ↓
version
    ↓
source document
    ↓
knowledge artifacts
    ↓
rules
    ↓
tests
```

A change in the source protocol must be detectable and traceable.

---

## 6. Provenance is mandatory

Every computable clinical rule must have provenance.

Whenever supported by the source, provenance should identify:

- protocol identifier
- protocol version
- source filename
- page
- section
- source fragment or extracted text
- extraction status
- validation status

The system should make it possible to trace a rule from:

```text
execution result
    ↓
rule
    ↓
knowledge artifact
    ↓
source fragment
    ↓
page / section
    ↓
protocol version
    ↓
original document
```

Do not create a clinical rule without identifying its source.

If provenance cannot be established, the rule should not be silently treated
as validated clinical knowledge.

---

## 7. Clinical source fidelity

The source protocol is the authority for the clinical knowledge encoded in
this project.

Do not silently replace source content with general medical knowledge.

Do not silently correct, reinterpret, complete, simplify, or reconcile a
source rule merely because another medical source would normally express it
differently.

When source wording is ambiguous, incomplete, contradictory, difficult to
formalize, or insufficient to determine an executable rule:

- preserve the source meaning as far as possible;
- mark the ambiguity explicitly;
- create a validation item when appropriate;
- keep the rule non-executable if necessary;
- preserve provenance to the original source.

The project must distinguish between:

1. what the protocol explicitly states;
2. what was extracted or normalized from the protocol;
3. what was inferred by a transformation process;
4. what was validated by a reviewer;
5. what remains unresolved.

Never present an inferred or draft rule as validated clinical truth.

---

## 8. No invented clinical logic

Do not invent clinical rules.

Do not invent:

- thresholds
- operators
- units
- contraindications
- exceptions
- temporal requirements
- treatment choices
- clinical classifications
- missing branches
- population restrictions
- causal relationships

If a rule cannot be represented faithfully, flag it rather than filling the
gap from assumptions.

LLMs may assist with extraction, normalization, ambiguity detection, or
language interaction, but generated content must remain distinguishable from
source-derived knowledge.

---

## 9. Deterministic rule execution

Clinical rules represented as executable knowledge must be evaluated by a
deterministic rule engine.

The engine should behave reproducibly:

```text
same protocol version
+
same case input
+
same rule package
=
same evaluation result
```

The execution engine must not depend on an LLM response to determine whether
a deterministic clinical condition is true or false.

LLMs may eventually assist with:

- document understanding
- candidate rule extraction
- terminology normalization
- ambiguity detection
- natural-language interaction
- explanation generation

but the final evaluation of an explicitly represented rule must be handled
by deterministic software.

---

## 10. Explicit uncertainty and missing data

Missing clinical information must never automatically be interpreted as
`FALSE`.

The rule engine must support explicit evaluation states.

At minimum:

```text
TRUE
FALSE
UNKNOWN
```

The architecture should remain extensible to states such as:

```text
NOT_COLLECTED
NOT_APPLICABLE
CONFLICTING
```

if those states are justified by the knowledge model.

Example:

```text
patient.curb65 = unknown
```

must not silently produce:

```text
curb65 >= 2 → FALSE
```

Instead, the engine should preserve the fact that the required information
is unknown.

---

## 11. Rule semantics

The knowledge model must be able to represent more than simple binary tree
branches.

The protocols may contain:

- equality
- inequality
- inclusive thresholds
- exclusive thresholds
- ranges
- categorical values
- AND logic
- OR logic
- NOT / negation
- counts of satisfied criteria
- temporal conditions
- sequence constraints
- alternatives
- exceptions
- contextual restrictions
- population restrictions
- actions
- follow-up requirements

Do not design the canonical model around the assumption that every protocol
can be represented as a simple binary decision tree.

---

## 12. Tree versus canonical knowledge representation

The project name contains `Tree`, but a tree is not necessarily the
canonical source of truth.

The canonical representation should preserve the clinical semantics needed
for execution and validation.

A tree, graph, decision table, or other visualization may be derived from the
canonical knowledge representation.

The architecture should therefore support:

```text
canonical computable knowledge
            │
      ┌─────┼─────┐
      ↓     ↓     ↓
    tree   graph  tables
```

Do not force information into a tree if doing so would lose:

- provenance
- shared conditions
- composite logic
- temporal relationships
- exceptions
- alternatives
- uncertainty
- context

---

## 13. Knowledge package concept

Each computable protocol should eventually be representable as a versioned
knowledge package.

A conceptual package may contain:

```text
metadata
concepts
variables
rules
actions
exceptions
provenance
validation status
test cases
derived views
```

A possible future organization is:

```text
protocols/
├── CT-PL-193/
│   └── v09/
│       ├── metadata.yaml
│       ├── concepts.yaml
│       ├── rules.yaml
│       ├── actions.yaml
│       ├── provenance.yaml
│       └── tests/
│
└── CT-PL-197/
    └── v06/
        ├── metadata.yaml
        ├── concepts.yaml
        ├── rules.yaml
        ├── actions.yaml
        ├── provenance.yaml
        └── tests/
```

This is an architectural direction, not a requirement to create this exact
directory structure immediately.

Do not implement a structure merely because it appears in this example if
the implementation investigation demonstrates a better design.

---

## 14. Pipeline architecture

The generic pipeline should conceptually follow:

```text
source document
      ↓
ingestion
      ↓
document extraction
      ↓
segmentation
      ↓
candidate knowledge extraction
      ↓
normalization
      ↓
candidate computable rules
      ↓
validation
      ↓
validated knowledge package
      ↓
deterministic execution
      ↓
traceable result
```

Each stage should have a clear responsibility.

Intermediate artifacts should be preserved when useful for:

- reproducibility
- debugging
- validation
- provenance
- comparison between extraction methods
- research evaluation

Do not collapse the entire transformation into one opaque script.

---

## 15. Pipeline generalization requirement

The pipeline must be designed so that the same implementation can process:

```text
CT-PL-193
```

and:

```text
CT-PL-197
```

without protocol-specific branches in the core pipeline.

The pipeline should operate on generic concepts such as:

```text
ProtocolDocument
ProtocolMetadata
Section
SourceFragment
Variable
Condition
CompositeCondition
Rule
Action
Provenance
ValidationItem
```

Protocol-specific clinical concepts should be represented as data.

The architecture must allow a future third or fourth protocol to be added
without rewriting the generic pipeline.

---

## 16. Current protocols are test cases for generalization

The two initial protocols must not be treated merely as two datasets.

They should be used to test whether the architecture generalizes across
different clinical structures.

The NAC protocol contains, among other things:

- diagnostic criteria
- hospitalization criteria
- ICU/UCE criteria
- threshold-based variables
- a composite rule based on satisfying multiple criteria
- treatment recommendations
- discharge criteria
- follow-up requirements

The ITU protocol contains, among other things:

- bacteriuria asymptomatic versus symptomatic infection
- upper versus lower urinary tract infection
- complicated infection
- pregnancy-specific considerations
- hospitalization criteria
- antimicrobial resistance risk factors
- treatment tables
- temporal conditions
- discharge/step-down criteria

The architecture must be able to represent these differences without
creating separate protocol-specific engines.

---

## 17. LLM usage

LLMs may be investigated as assistants for knowledge extraction and
transformation.

Potential uses include:

- extracting candidate variables
- identifying candidate conditions
- identifying candidate actions
- detecting temporal expressions
- identifying potential exceptions
- normalizing terminology
- flagging ambiguities
- generating candidate structured representations

However:

- LLM output is not automatically validated knowledge;
- LLM output must retain provenance;
- LLM output must be distinguishable from source-derived facts;
- LLMs must not silently execute deterministic clinical rules;
- hallucinated rules must never be accepted as clinical knowledge.

The project should preserve intermediate artifacts so that LLM-assisted
extraction can be compared with source material and validated independently.

---

## 18. RAG relationship

The project is expected to eventually integrate with a medical RAG system.

Keep the responsibilities conceptually separate:

```text
RAG
→ retrieves evidence and source documents

Computable knowledge
→ represents explicit clinical logic

Rule engine
→ evaluates explicit rules

Protocol Agent
→ interacts with the user/case and collects required information

Provenance
→ explains where the knowledge came from
```

Do not introduce a vector database or RAG dependency into the MVP unless it
is necessary for the current research objective.

The Protocol Agent and RAG should remain separable components.

---

## 19. Local-first architecture

The project should remain local-first.

Do not introduce a mandatory cloud service dependency for core functionality.

The MVP should be executable locally using the project environment and
version-controlled code.

Future LLM, retrieval, or interoperability components may be evaluated
independently.

---

## 20. Clinical safety and scope

This project is not a production clinical system.

Do not:

- connect to real patient systems;
- issue real clinical orders;
- prescribe autonomously;
- represent prototype outputs as medical advice;
- claim clinical efficacy without appropriate validation;
- claim regulatory compliance without evidence;
- silently use outdated protocol versions;
- mix rules from different protocol versions;
- silently apply rules outside their documented population or context.

Clinical knowledge must remain traceable and versioned.

---

## 21. Evaluation and validation

Validation is a first-class component of the project.

Potential evaluation layers include:

### Source/document layer

- extraction completeness
- page/section preservation
- text fidelity

### Knowledge layer

- concept extraction
- variable extraction
- rule extraction
- threshold correctness
- operator correctness
- unit correctness
- negation correctness
- temporal logic correctness
- AND/OR correctness
- exception preservation
- provenance completeness

### Execution layer

- deterministic evaluation
- TRUE/FALSE/UNKNOWN behavior
- expected action selection
- rule trace correctness
- consistency across repeated runs

### Protocol layer

- protocol-specific test cases
- edge cases
- synthetic cases
- expert review when available

Do not claim clinical validation merely because software tests pass.

---

## 22. Testing principles

Tests are part of the knowledge engineering process.

New clinical logic must have tests where practical.

Tests should cover:

- positive cases
- negative cases
- missing data
- boundary thresholds
- operator boundaries
- composite conditions
- temporal conditions
- exceptions
- alternative paths
- protocol versioning
- provenance
- deterministic repeatability

Protocol-specific tests should be kept separate from generic engine tests.

The engine tests should verify generic behavior.

Protocol tests should verify that a particular protocol knowledge package
produces the expected behavior.

---

## 23. Development environment

The repository is based on a Data Science project template.

Use:

- Python 3.12
- uv
- pytest
- pytest-cov
- Ruff
- Mypy
- pre-commit
- Commitizen
- Git

The repository uses `.python-version` to select Python 3.12.

Prefer:

```bash
uv run python ...
uv run pytest
```

rather than relying on the system Python executable.

Dependencies must be managed through `uv`.

When adding a runtime dependency:

```bash
uv add <package>
```

When adding a development dependency:

```bash
uv add --group dev <package>
```

Always keep `uv.lock` synchronized.

Do not use `uv init` because this repository already contains an existing
`pyproject.toml` and `uv.lock`.

---

## 24. Code quality

The repository already contains configuration for:

- Ruff
- Mypy
- pre-commit
- pytest
- coverage

Preserve these quality controls.

Ruff configuration is located at:

```text
.code_quality/ruff.toml
```

Mypy configuration is located at:

```text
.code_quality/mypy.ini
```

Do not create conflicting duplicate configurations without a documented
reason.

New Python functions should have explicit type annotations because the
project's mypy configuration enforces typed function definitions.

Keep functions focused and avoid unnecessary complexity.

---

## 25. Verification commands

For the full quality gate:

```bash
make check
```

For test coverage:

```bash
make test_coverage
```

For tests:

```bash
uv run pytest
```

For a focused test:

```bash
uv run pytest tests/<path> -k <name>
```

For pre-commit directly:

```bash
uv run pre-commit run -a
```

Run appropriate verification after changes.

Before considering a meaningful implementation complete, run the relevant
tests and quality checks.

---

## 26. Git workflow

Use Gitflow-style branches.

Do not work directly on `main`.

Use branch names such as:

```text
feature/<name>
fix/<name>
docs/<name>
chore/<name>
```

The current development branch is expected to be:

```text
feature/mvp-foundation
```

Use Conventional Commits.

Do not commit:

- raw clinical PDFs
- local virtual environments
- generated caches
- temporary files
- secrets
- private keys
- unreviewed generated clinical artifacts

`AGENTS.md` itself should be version-controlled because it contains the
project instructions used by OpenCode.

---

## 27. Template preservation

The repository originated from the
`JoseRZapata/data-science-project-template` template and is tracked through
Cruft.

Preserve useful template infrastructure such as:

- `uv`
- pre-commit
- Ruff
- Mypy
- pytest
- coverage
- Makefile conventions
- `.code_quality/`
- `.github/`
- `.devcontainer/`
- notebook conventions

However, do not allow the original Data Science/ML terminology to dictate
the architecture of the CPG project when it conflicts with the clinical
knowledge-engineering requirements.

The project should evolve from the template rather than remain a generic
Data Science template.

---

## 28. Repository structure

The current repository structure comes from the template.

The target architecture should progressively introduce domain-specific
modules without unnecessarily deleting useful template infrastructure.

Conceptually:

```text
data/
├── 01_raw/
├── 02_intermediate/
├── 03_primary/
└── ...

src/
└── cpg_tree/
    ├── ingestion/
    ├── extraction/
    ├── knowledge/
    ├── engine/
    ├── validation/
    ├── pipelines/
    └── cli/

protocols/
    └── versioned knowledge packages

tests/
    ├── unit/
    ├── integration/
    └── protocols/

evaluation/
    ├── cases/
    └── results/

docs/
notebooks/
```

This is a target direction, not permission to create all directories
immediately.

Implement only the structure needed for the current milestone.

---

## 29. MVP scope

The first MVP should establish the foundation for a reusable protocol
computabilization system.

The MVP should focus on:

1. Generic protocol metadata.
2. Generic protocol ingestion.
3. Source document extraction.
4. Structured knowledge representation.
5. Explicit conditions and rules.
6. Provenance.
7. Deterministic rule evaluation.
8. TRUE/FALSE/UNKNOWN semantics.
9. Protocol-specific test cases.
10. Support for both initial protocols.
11. Reproducible execution.
12. Basic traceable outputs.

The MVP should demonstrate that the same generic infrastructure can process
both CT-PL-193 and CT-PL-197.

---

## 30. Explicitly out of scope for the initial MVP

Do not prematurely implement:

- production clinical deployment
- EHR integration
- autonomous clinical decision making
- autonomous prescribing
- real clinical orders
- full FHIR interoperability
- full CQL implementation
- universal clinical ontology
- complete terminology mapping
- vector database infrastructure
- mandatory cloud infrastructure
- complex web frontend
- production authentication/authorization
- clinical efficacy validation
- complete automatic extraction of every protocol rule

These topics may be investigated later if justified by the research
objectives.

---

## 31. Change discipline

Before modifying architecture or introducing a new technology:

1. Inspect the current repository.
2. Understand existing template conventions.
3. Identify the research/engineering reason for the change.
4. Prefer the smallest coherent implementation.
5. Preserve provenance and reproducibility.
6. Add or update tests.
7. Run the appropriate quality checks.
8. Do not introduce technology merely because it is popular.

Do not add:

- a database
- a vector store
- an LLM
- an ontology
- FHIR/CQL
- a frontend
- a rule-engine framework

unless the current milestone demonstrates a concrete need for it.

Technology choices should remain open to comparison and future evaluation.

---

## 32. Important implementation principle

The central architectural test is:

> **Can a third protocol be added without modifying the generic rule engine?**

If the answer is no, reconsider the design.

The intended relationship is:

```text
                    GENERIC INFRASTRUCTURE
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
      CT-PL-193        CT-PL-197       Future protocols
        v09               v06
          │                │
          └────────────────┼────────────────┘
                           ↓
                  deterministic engine
                           ↓
                    traceable result
```

The engine should understand concepts such as:

```text
Protocol
Variable
Condition
CompositeCondition
Rule
Action
Case
Evaluation
Provenance
```

It should not need to understand the medical domain of a protocol in order
to evaluate its explicitly represented rules.

---

## 33. Research mindset

This project is exploratory.

Do not turn an implementation convenience into an unquestioned architectural
decision.

For example:

- JSON is not automatically the canonical representation merely because it
  is easy to parse.
- YAML is not automatically superior because it is human-readable.
- A tree is not automatically the correct representation because the project
  is named CPG Tree.
- An LLM is not automatically the correct extraction method.
- A vector database is not automatically required because the project may
  later integrate with RAG.
- A rule engine library is not automatically better than a small deterministic
  implementation.

Technology choices should be evaluated against:

- clinical semantics
- reproducibility
- traceability
- versioning
- validation
- execution correctness
- missing data
- temporal logic
- exceptions
- extensibility
- local execution

---

## 34. Working rule for agents

When working on this repository:

1. Read the relevant project instructions.
2. Inspect existing code before modifying it.
3. Do not assume the protocol is a simple decision tree.
4. Do not invent clinical rules.
5. Preserve provenance.
6. Keep protocol-specific knowledge outside generic infrastructure.
7. Prefer deterministic execution.
8. Treat missing data explicitly.
9. Keep protocol versions separate.
10. Add tests for meaningful behavior.
11. Run appropriate quality checks.
12. Keep changes small and reproducible.
13. Do not introduce unnecessary technologies.
14. Clearly distinguish source-derived knowledge from inference or generated
    content.
15. When the source does not support a conclusion, leave the uncertainty
    explicit rather than filling the gap.

## 35. Current project status

At the beginning of the MVP:

- the repository is based on the Data Science project template;
- Python 3.12 is managed by uv;
- the development branch is `feature/mvp-foundation`;
- the two source PDFs are local raw data;
- no production clinical system exists;
- no clinical rule should be assumed to be validated merely because it has
  been extracted or encoded;
- the generic architecture is still being established.

The first implementation goal is to build the reusable foundation before
encoding a large amount of protocol-specific clinical knowledge.

## 36. CLI interface (Phase 7)

The project has a local, deterministic CLI:

```bash
uv run python -m cpg_tree --help
uv run python -m cpg_tree list
uv run python -m cpg_tree inspect <PROTOCOL_ID> [VERSION]
uv run python -m cpg_tree variables <PROTOCOL_ID> [VERSION]
uv run python -m cpg_tree rules <PROTOCOL_ID> [VERSION] [--rule RULE_ID]
uv run python -m cpg_tree provenance <PROTOCOL_ID> [VERSION] (--rule|--variable|--action|--fragment) ID
uv run python -m cpg_tree tree <PROTOCOL_ID> [VERSION]
uv run python -m cpg_tree validate <PROTOCOL_ID> [VERSION]
uv run python -m cpg_tree evaluate <PROTOCOL_ID> case.json [VERSION]
uv run python -m cpg_tree visualize <PROTOCOL_ID> [VERSION] [--out DIR]
```

Conventions:

- Protocol discovery scans `protocols/<protocol_id>/<version>/package.yaml`;
  the CLI never imports protocol builders and must stay protocol-agnostic.
- Case files map variable ids to `string | number | boolean | null`; `null`
  means explicitly missing information (UNKNOWN, never FALSE).
- `--json` emits deterministic JSON on data commands; outputs are derived
  views only, and the tree is a projection, never a source of truth.
- Exit codes: `0` success, `1` operational/input failure, `2` usage error.
- Views/CLI code lives in `src/cpg_tree/views/` and `src/cpg_tree/cli.py`;
  it must never duplicate engine semantics or contain protocol knowledge.

### visualize command (Phase 7 extension)

```bash
uv run python -m cpg_tree visualize <PROTOCOL_ID> [VERSION] [--out DIR]
```

- Generates a self-contained static HTML presentation into
  `data/08_reporting/` (gitignored; never committed).
- `protocols/<id>/<version>/visualization.yaml` is OPTIONAL presentation
  metadata (section titles + rule-id prefixes/explicit ids) only. It must not
  contain clinical content; every clinical fact comes from package.yaml.
- Sections are display groupings only, never clinical workflow order.
- Output must remain byte-deterministic (no timestamps, stable ordering).
- The renderer is generic (`src/cpg_tree/views/visualize.py`); a third
  protocol needs only package.yaml (manifest optional, fallback "Reglas").
