"""Shared type aliases for scalar values in the knowledge model."""

from __future__ import annotations

type ScalarOperand = int | float
"""Numeric operand accepted by comparison and temporal conditions."""

type Scalar = str | int | float | bool | None
"""YAML-safe scalar used in action payloads and test-case inputs."""
