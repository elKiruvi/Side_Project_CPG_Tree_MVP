# Evaluation case library (MVP closure)

Synthetic demonstration cases for the deterministic rule engine.

## What these files are

- **Synthetic, non-patient data.** Every file here is a hand-crafted
  demonstration input; nothing in this directory came from a real patient
  record.
- Runtime inputs for the existing `evaluate` CLI command. Each file maps
  variable ids to `string | number | boolean | null`; `null` means explicitly
  missing information and is evaluated as UNKNOWN, never FALSE.
- **Not clinical validation.** A case demonstrating a `MATCHED` outcome only
  proves that the deterministic engine mechanically produced that outcome for
  that input. It says nothing about the clinical validity of the underlying
  rule. Provenance status is carried along per rule; UNRESOLVED rules are
  mechanically evaluated and must not be treated as validated knowledge.

## Layout

```text
evaluation/cases/
├── CT-PL-193/v09/   # NAC demo cases (4 of 5 engine outcomes reachable)
└── CT-PL-197/v06/   # ITU demo cases (all 5 engine outcomes reachable)
```

## Documented outcomes

| Case file | Demonstrated outcome |
|---|---|
| `nac_matched.json` | `MATCHED` |
| `nac_not_matched.json` | `NOT_MATCHED` |
| `nac_not_applicable.json` | `NOT_APPLICABLE` (population gate evaluates FALSE) |
| `nac_indeterminate.json` | `INDETERMINATE` (UNKNOWN never becomes FALSE) |
| `itu_matched.json` | `MATCHED` (treatment alternatives declared, never selected) |
| `itu_not_matched.json` | `NOT_MATCHED` |
| `itu_not_applicable.json` | `NOT_APPLICABLE` (gestational rules gated by `gestante`) |
| `itu_indeterminate.json` | `INDETERMINATE` (UNKNOWN never becomes FALSE) |
| `itu_excepted.json` | `EXCEPTED` (amikacina exception in septic shock) |

**Known gap:** CT-PL-193 v09 contains no rule with an exception, so `EXCEPTED`
is not demonstrable on real NAC knowledge. It is demonstrated generically by
the engine unit tests (`tests/unit/engine/test_rules.py`) and at package level
for ITU. No exception was invented to fill this gap.

## Usage

```bash
uv run python -m cpg_tree evaluate CT-PL-193 evaluation/cases/CT-PL-193/v09/nac_matched.json
uv run python -m cpg_tree evaluate CT-PL-197 evaluation/cases/CT-PL-197/v06/itu_excepted.json
```

The protocol tests under `tests/protocols/{nac,itu}/` assert that each
committed case produces its documented outcome through the generic loader and
engine.
