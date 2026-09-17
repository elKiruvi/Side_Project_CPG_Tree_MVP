"""Deterministic error types for the rule evaluation engine.

The engine distinguishes three failure categories and never conflates them:

- ``CaseError``: malformed case data rejected at construction.
- ``EngineInputError``: case data whose type is incompatible with a condition.
- ``EngineConfigurationError``: knowledge configuration that is invalid for
  execution (unresolvable references, type/unit mismatches, malformed
  expressions).

All three inherit from ``ValueError``, matching the repository convention for
deterministic domain errors.
"""

from __future__ import annotations


class EngineError(ValueError):
    """Base class for every deterministic engine error."""


class CaseError(EngineError):
    """Raised when a Case or CaseValue is malformed at construction."""


class EngineInputError(EngineError):
    """Raised when a CaseValue type is incompatible with a condition."""


class EngineConfigurationError(EngineError):
    """Raised when knowledge configuration is invalid for execution."""
