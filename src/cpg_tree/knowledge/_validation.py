"""Private structural validation helpers for the knowledge model."""

from __future__ import annotations

import re
from datetime import datetime

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def validate_identifier(value: str, field_name: str) -> None:
    """Raise ValueError unless value is a non-empty identifier without whitespace."""
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must match {_IDENTIFIER_PATTERN.pattern!r}; got {value!r}"
        )


def validate_iso_date(value: str, field_name: str) -> None:
    """Raise ValueError unless value parses as an ISO-8601 date."""
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 date; got {value!r}") from exc
