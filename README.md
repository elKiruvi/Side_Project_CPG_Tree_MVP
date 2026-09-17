# Side_Project_CPG_Tree_MVP

Research prototype for transforming institutional clinical practice protocols into
structured, traceable, versioned, and executable computational knowledge.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3120/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

## Status

MVP closed (Phases 0–8). The MVP demonstrates **technical completeness** and
**source traceability** for two institutional protocols. It does **not**
establish **clinical/source fidelity**: every encoded rule remains
`EXTRACTED` pending clinical review, and provenance coverage is not a
clinical accuracy metric. See [docs/mvp-closure.md](docs/mvp-closure.md).

This is a research prototype, not a production clinical decision-support
system, and does not replace clinical judgment.

## About

- Generic, protocol-agnostic infrastructure for protocol ingestion, extraction,
  knowledge representation, deterministic rule evaluation, and traceability.
- Initial protocol corpus: two institutional clinical protocols (`CT-PL-193`,
  `CT-PL-197`) kept locally under `data/01_raw/` and ignored by Git.
- Local-first: core functionality runs locally with Python 3.12 and uv.

## Tooling

- [uv](https://docs.astral.sh/uv/) — environment and dependency management
- [pytest](https://docs.pytest.org/) — testing
- [Ruff](https://docs.astral.sh/ruff/) — linting and formatting
- [mypy](https://mypy-lang.org/) — static type checking
- [pre-commit](https://pre-commit.com/) — quality gates

## Development

```bash
make install_env      # sync the environment and install pre-commit hooks
uv run pytest         # run tests
make check            # run the full quality gate (pre-commit)
```

## CLI

The MVP ships a local, deterministic command-line interface over the committed
knowledge packages (no server, no database, no cloud):

```bash
uv run python -m cpg_tree --help
uv run python -m cpg_tree list
uv run python -m cpg_tree inspect CT-PL-197 v06
uv run python -m cpg_tree rules CT-PL-197 v06 --rule rule_t1_itu_baja
uv run python -m cpg_tree provenance CT-PL-197 v06 --rule rule_t1_itu_baja
uv run python -m cpg_tree tree CT-PL-197 v06
uv run python -m cpg_tree validate CT-PL-197 v06
uv run python -m cpg_tree evaluate CT-PL-197 v06 case.json
uv run python -m cpg_tree visualize CT-PL-197 v06
```

- `case.json` maps variable ids to `string | number | boolean | null`; `null`
  means explicitly missing information (evaluated as UNKNOWN, never FALSE).
- Every data command accepts `--json` for deterministic machine-readable output.
- Exit codes: `0` success, `1` operational/input failure, `2` usage error.
- Protocol artifacts are discovered from `protocols/<id>/<version>/package.yaml`;
  a new protocol becomes available by adding its versioned artifact directory.
- All output is derived from the canonical packages and the deterministic rule
  engine. Actions are declarative and are never executed; multiple `PRESCRIBE`
  actions on one rule are source-declared alternatives, never a selection.
  This is a research prototype, not clinical advice.

`visualize` generates a self-contained static HTML presentation of a protocol
into `data/08_reporting/<PROTOCOL_ID>-<VERSION>.html` (open it locally in any
browser). Rules are grouped into presentation sections by an optional sidecar
manifest (`protocols/<id>/<version>/visualization.yaml`); sections are display
groupings only — they do not represent clinical workflow or execution order.
`package.yaml` remains the single source of truth for all clinical content.

## Evaluation evidence

- `docs/mvp-closure.md` — MVP closure report: acceptance criteria, evidence
  matrix (reproducible via `inspect --json`), five engine outcomes, fidelity
  accounting (extracted / normalized / inferred / unresolved), limitations.
- `evaluation/cases/` — committed synthetic demonstration cases (non-patient
  data), one per engine outcome where reachable:

```bash
uv run python -m cpg_tree evaluate CT-PL-193 evaluation/cases/CT-PL-193/v09/nac_matched.json
uv run python -m cpg_tree evaluate CT-PL-197 evaluation/cases/CT-PL-197/v06/itu_excepted.json
```

## Credits

This repository originated from the
[JoseRZapata/data-science-project-template](https://github.com/JoseRZapata/data-science-project-template)
template and remains tracked through Cruft (`.cruft.json`).
