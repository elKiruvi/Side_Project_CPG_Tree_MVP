# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Phase 7 — Views / CLI / MVP interface.** Generic protocol artifact
  discovery (`protocols/<id>/<version>/package.yaml`), deterministic logical
  expression rendering with structural fingerprints, package inspection and
  provenance chain views, a derived decision-tree projection with shared
  expression references, runtime case JSON loading (UNKNOWN-preserving),
  evaluation result rendering (declarative actions, treatment alternatives
  rendered as OR choices), and an 8-command local CLI
  (`python -m cpg_tree`: list, inspect, variables, rules, provenance, tree,
  validate, evaluate) with deterministic text/JSON output and exit codes
  0/1/2.
- **Phase 7 extension — static HTML visualization.** `visualize` CLI command
  generating a self-contained, byte-deterministic HTML presentation per
  protocol (sections, rule cards, conditions, exceptions, declarative
  actions, shared-expression badges, provenance chains). Presentation
  groupings come from an optional `visualization.yaml` sidecar manifest;
  `package.yaml` remains the canonical source of truth. Output goes to
  `data/08_reporting/` (gitignored).

### History backfill (Phases 0–6)

- Phase 0 — project identity, cleanup, runtime tooling.
- Phase 1 — canonical knowledge model (variables, conditions, logical
  expressions, rules, actions, provenance, deterministic YAML serialization).
- Phase 2 — generic PDF extraction with sectioning and content-addressed
  source documents.
- Phase 3 — provenance validation layer with deterministic reports.
- Phase 4 — deterministic rule engine (TRUE/FALSE/UNKNOWN;
  MATCHED/NOT_MATCHED/NOT_APPLICABLE/EXCEPTED/INDETERMINATE).
- Phase 5 — NAC CT-PL-193 v09 knowledge package.
- Phase 6 — ITU CT-PL-197 v06 knowledge package.

## [Released]
