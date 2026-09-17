"""Text helpers shared by the deterministic view renderers."""

from __future__ import annotations


def indent_text(text: str, prefix: str = "    ") -> str:
    """Prefix every line of a (possibly multi-line) rendering."""
    return "\n".join(prefix + line for line in text.splitlines())


def bullet_text(text: str, prefix: str = "      - ") -> str:
    """Prefix the first line with a bullet; align continuation lines."""
    lines = text.splitlines()
    continuation = " " * len(prefix)
    return "\n".join(
        (prefix + line) if index == 0 else (continuation + line)
        for index, line in enumerate(lines)
    )
