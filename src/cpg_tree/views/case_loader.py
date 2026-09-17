"""Runtime case input adapter: JSON files to engine ``Case`` objects.

A case file is a JSON object mapping variable ids to values:

    {"flag_y": true, "count_x": 101, "span_t": null}

Accepted values are ``string``, ``number``, ``boolean``, and ``null``.
``null`` denotes explicitly missing information and becomes the engine's
``UNKNOWN`` case state; an absent key stays absent from the case. Inputs are
checked against the package's variable registry before the engine is called:
unknown variable ids and values whose type is incompatible with the declared
``VariableType`` are rejected deterministically with ``CaseLoadError``.

Case files are runtime data: they are never written into a knowledge package
and never mutate one.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path

from cpg_tree.engine.case import Case
from cpg_tree.knowledge.enums import VariableType
from cpg_tree.knowledge.types import Scalar
from cpg_tree.knowledge.variables import Variable


class CaseLoadError(ValueError):
    """Deterministic failure while loading or validating a runtime case."""


def load_case(path: Path, variables: Mapping[str, Variable]) -> Case:
    """Load a case JSON file validated against the package variables."""
    return load_case_text(path.read_text(encoding="utf-8"), variables)


def load_case_text(text: str, variables: Mapping[str, Variable]) -> Case:
    """Parse and validate case JSON text against the package variables."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise CaseLoadError(f"case file is not valid JSON: {error.msg}") from error
    if not isinstance(data, Mapping):
        raise CaseLoadError(
            f"case root must be a JSON object mapping variable ids to values; "
            f"got {type(data).__name__}"
        )
    inputs: dict[str, Scalar] = {}
    for key, raw_value in data.items():
        if not isinstance(key, str) or not key:
            raise CaseLoadError("case keys must be non-empty strings")
        variable = variables.get(key)
        if variable is None:
            available = ", ".join(sorted(variables)) or "(package declares no variables)"
            raise CaseLoadError(f"unknown variable {key!r} in case; available: {available}")
        inputs[key] = _checked_value(key, raw_value, variable)
    return Case.from_inputs(inputs)


def _checked_value(key: str, raw_value: object, variable: Variable) -> Scalar:
    if raw_value is None:
        return None
    if isinstance(raw_value, bool):
        if variable.type is not VariableType.BOOLEAN:
            raise CaseLoadError(
                f"case value for {key!r} is boolean but the variable is {variable.type.value}"
            )
        return raw_value
    if isinstance(raw_value, (int, float)):
        if isinstance(raw_value, float) and not math.isfinite(raw_value):
            raise CaseLoadError(f"case value for {key!r} must be finite")
        if variable.type not in (VariableType.NUMERIC, VariableType.DURATION):
            raise CaseLoadError(
                f"case value for {key!r} is numeric but the variable is {variable.type.value}"
            )
        return raw_value
    if isinstance(raw_value, str):
        if variable.type is not VariableType.CATEGORICAL:
            raise CaseLoadError(
                f"case value for {key!r} is a string but the variable is {variable.type.value}"
            )
        return raw_value
    raise CaseLoadError(
        f"case value for {key!r} must be a string, number, boolean, or null; "
        f"got {type(raw_value).__name__}"
    )
