"""Deterministic HTML visualization of a knowledge package (derived view).

The visualization is a pure presentation layer: it renders the canonical
``ProtocolVersion`` (the single source of truth) into one self-contained,
static HTML document. It never evaluates conditions, never mutates the
package, and never invents clinical content.

Presentation groupings come from an optional sidecar manifest
(``visualization.yaml`` next to ``package.yaml``) that maps existing rule ids
to visual sections. The manifest is presentation metadata only: it contains
no conditions, thresholds, actions, or provenance. Without a manifest, every
rule is rendered in one neutral section sorted by rule id.

The output is deterministic: identical package + manifest + code always
produce byte-identical HTML (no timestamps, no randomness, stable ordering).
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cpg_tree.knowledge.enums import ActionType
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.rules import Rule
from cpg_tree.views.expression import render_operand
from cpg_tree.views.tree import build_projection

_FALLBACK_SECTION = "Reglas"
_OVERFLOW_SECTION = "Otras reglas"
_MANIFEST_FILENAME = "visualization.yaml"

_CSS = """
:root { --ink: #1f2937; --muted: #6b7280; --line: #d1d5db; --bg: #f6f7f9;
        --card: #ffffff; --accent: #0f4c81; --soft: #eef3f8; --alt: #7a4a9e; }
* { box-sizing: border-box; }
body { margin: 0; color: var(--ink); background: var(--bg);
       font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
       line-height: 1.45; }
header { background: var(--accent); color: #fff; padding: 1.6rem 2rem; }
header h1 { margin: 0 0 .35rem 0; font-size: 1.5rem; }
header .meta { font-size: .95rem; opacity: .95; }
header .derived { margin-top: .8rem; font-size: .8rem; opacity: .85;
                 font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
main { max-width: 1200px; margin: 0 auto; padding: 1.2rem 2rem 2rem 2rem; }
section.legend { background: var(--card); border: 1px solid var(--line);
                 border-radius: 6px; padding: .9rem 1.1rem; margin: 1rem 0 1.4rem 0;
                 font-size: .85rem; color: var(--muted); }
section.legend code { color: var(--ink); }
h2.domain { border-bottom: 2px solid var(--accent); padding-bottom: .25rem;
            margin: 1.6rem 0 .8rem 0; font-size: 1.15rem; }
h2.domain .count { color: var(--muted); font-weight: normal; font-size: .85rem; }
article.card { background: var(--card); border: 1px solid var(--line);
               border-radius: 6px; padding: .9rem 1.1rem; margin: 0 0 .8rem 0;
               break-inside: avoid; }
article.card header { background: none; color: inherit; padding: 0 0 .5rem 0;
                      border-bottom: 1px solid var(--line); margin-bottom: .6rem; }
.rule-id { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
           font-weight: 600; font-size: 1rem; }
.badge { display: inline-block; border-radius: 10px; padding: .05rem .55rem;
         font-size: .72rem; font-weight: 600; margin-left: .4rem;
         border: 1px solid var(--line); color: var(--muted); background: var(--soft); }
.badge.status { color: var(--accent); border-color: var(--accent); }
.badge.derivation { color: var(--alt); border-color: var(--alt); }
.badge.shared { color: var(--alt); }
.notes { font-style: italic; color: var(--muted); margin: 0 0 .6rem 0; font-size: .88rem; }
.eval-order { font-size: .75rem; color: var(--muted); margin: 0 0 .5rem 0; }
.expr-label { font-size: .75rem; font-weight: 700; text-transform: uppercase;
              letter-spacing: .04em; color: var(--muted); }
pre.expr { background: var(--soft); border-radius: 4px; padding: .5rem .7rem;
           margin: .2rem 0 .7rem 0; overflow-x: auto; font-size: .82rem;
           font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.actions ul { list-style: none; margin: .2rem 0 .7rem 0; padding: 0; }
.actions li { border-left: 3px solid var(--line); padding: .2rem .7rem;
              margin-bottom: .35rem; font-size: .88rem; }
.actions .type { font-weight: 700; font-size: .75rem; text-transform: uppercase;
                 color: var(--accent); }
.actions .alternative { color: var(--alt); font-size: .75rem; font-weight: 600; }
.actions .alt-note { color: var(--alt); font-size: .8rem; margin: .2rem 0 .7rem 0; }
.payload { color: var(--muted); font-size: .84rem; }
.provenance { font-size: .8rem; color: var(--muted); border-top: 1px solid var(--line);
              padding-top: .5rem; margin-top: .4rem; }
.provenance .chain { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
footer { max-width: 1200px; margin: 0 auto; padding: 1rem 2rem 2.5rem 2rem;
         font-size: .78rem; color: var(--muted); }
@media print { article.card { border: 1px solid var(--line); } }
"""

_SAFETY_NOTICE = (
    "Research prototype — not clinical advice. Actions are declarative and are "
    "not executed by this visualization. This document is a derived view; the "
    "canonical knowledge package remains the source of truth."
)

_ALTERNATIVES_NOTE = "Declared alternatives (OR choice) — never selected by this system."

_LEGEND = [
    "Derived view of the canonical knowledge package. The tree is a projection: "
    "rules are independent; sections are presentation groupings only and do not "
    "represent execution order or clinical workflow.",
    "Engine outcome semantics: MATCHED, NOT_MATCHED, NOT_APPLICABLE "
    "(applies_to evaluated FALSE), EXCEPTED (condition TRUE but an exception "
    "evaluated TRUE), INDETERMINATE (required information is UNKNOWN).",
    "Three-valued logic: TRUE / FALSE / UNKNOWN. Missing information is UNKNOWN, "
    "never silently FALSE.",
    "Validation status (EXTRACTED, DRAFT, REVIEWED, VALIDATED, UNRESOLVED) and "
    "derivation (SOURCE_STATED, EXTRACTED, NORMALIZED, INFERRED, VALIDATED, "
    "UNRESOLVED) are presented as declared by the package.",
    "Multiple PRESCRIBE actions on one rule are source-declared alternatives; "
    "they are never presented as a selection or ranking.",
]


@dataclass(frozen=True, slots=True)
class ManifestSection:
    """One presentation grouping: a title plus rule-id prefixes/explicit ids."""

    title: str
    prefixes: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VisualizationManifest:
    """Presentation-only groupings for one package version."""

    sections: tuple[ManifestSection, ...]


def load_manifest(path: Path) -> VisualizationManifest | None:
    """Load and validate a visualization manifest; None when absent.

    Malformed structure or invalid data raises ``ValueError`` deterministically;
    nothing is silently ignored. Rule-id existence is checked later against
    the package (see ``build_visual_document``).
    """
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"malformed visualization manifest at {path}: {error}") from error
    if data is None:
        raise ValueError(f"visualization manifest at {path} is empty")
    if not isinstance(data, Mapping):
        raise ValueError(f"visualization manifest at {path} must be a mapping")
    unknown_keys = set(data) - {"sections"}
    if unknown_keys:
        raise ValueError(
            f"visualization manifest at {path} has unknown keys: {sorted(unknown_keys)}"
        )
    raw_sections = data.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ValueError(f"visualization manifest at {path} requires a non-empty 'sections' list")
    sections: list[ManifestSection] = []
    for index, raw in enumerate(raw_sections):
        sections.append(_section_from_data(path, index, raw))
    return VisualizationManifest(sections=tuple(sections))


def _section_from_data(path: Path, index: int, raw: object) -> ManifestSection:
    if not isinstance(raw, Mapping):
        raise ValueError(f"section {index} of {path} must be a mapping")
    unknown_keys = set(raw) - {"title", "prefixes", "rules"}
    if unknown_keys:
        raise ValueError(f"section {index} of {path} has unknown keys: {sorted(unknown_keys)}")
    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"section {index} of {path} requires a non-empty 'title' string")
    prefixes = _string_list(raw.get("prefixes"), path, index, "prefixes")
    rules = _string_list(raw.get("rules"), path, index, "rules")
    if not prefixes and not rules:
        raise ValueError(f"section {index} of {path} requires 'prefixes' or 'rules'")
    return ManifestSection(title=title, prefixes=prefixes, rules=rules)


def _string_list(raw: object, path: Path, index: int, field: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(entry, str) and entry for entry in raw):
        raise ValueError(f"section {index} of {path}: '{field}' must be a list of non-empty strings")
    return tuple(raw)


def build_visual_document(
    package: ProtocolVersion,
    manifest: VisualizationManifest | None,
) -> str:
    """Render one package into a deterministic, self-contained HTML document."""
    grouped = _group_rules(package, manifest)
    shared = build_projection(package)
    shared_by_id = {entry.id: entry for entry in shared.shared_expressions}
    shared_ids_by_rule = {
        rule.rule_id: (
            rule.applies_to_shared_id,
            rule.condition_shared_id,
            rule.exception_shared_ids,
        )
        for rule in shared.rules
    }
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="es">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{_esc(package.protocol.name)} — {_esc(package.version)}</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        _render_header(package),
        '<section class="legend">',
        "  <strong>How to read this document</strong>",
    ]
    parts.extend(f"  <p>{item}</p>" for item in _LEGEND)
    parts.append("</section>")
    parts.append("<main>")
    for title, rule_ids in grouped:
        parts.append(
            f'<h2 class="domain">{_esc(title)} '
            f'<span class="count">({len(rule_ids)} rules)</span></h2>'
        )
        for rule_id in rule_ids:
            rule = package.rules[rule_id]
            shared_ids = shared_ids_by_rule.get(rule_id, (None, None, ()))
            parts.append(
                _render_rule_card(package, rule, shared_ids, shared_by_id)
            )
    parts.append("</main>")
    parts.append(f"<footer>{_SAFETY_NOTICE}</footer>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts) + "\n"


def visualize_package(
    package: ProtocolVersion,
    manifest: VisualizationManifest | None,
    out_dir: Path,
) -> Path:
    """Write the deterministic HTML document and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{package.protocol.id}-{package.version}.html"
    out_path.write_text(build_visual_document(package, manifest), encoding="utf-8")
    return out_path


def _group_rules(
    package: ProtocolVersion,
    manifest: VisualizationManifest | None,
) -> list[tuple[str, list[str]]]:
    """Assign every rule to exactly one section; nothing may be dropped."""
    if manifest is None:
        return [(_FALLBACK_SECTION, sorted(package.rules))]
    grouped: list[tuple[str, list[str]]] = []
    assigned: set[str] = set()
    for section in manifest.sections:
        matched: set[str] = set()
        for rule_id in section.rules:
            if rule_id not in package.rules:
                raise ValueError(
                    f"visualization manifest references unknown rule {rule_id!r}"
                )
            if rule_id in assigned:
                raise ValueError(
                    f"visualization manifest assigns rule {rule_id!r} more than once"
                )
            matched.add(rule_id)
        for prefix in section.prefixes:
            for rule_id in sorted(package.rules):
                if rule_id not in assigned and rule_id.startswith(prefix):
                    matched.add(rule_id)
        assigned.update(matched)
        grouped.append((section.title, sorted(matched)))
    remaining = sorted(set(package.rules) - assigned)
    if remaining:
        grouped.append((_OVERFLOW_SECTION, remaining))
    return grouped


def _render_header(package: ProtocolVersion) -> str:
    document_lines: list[str] = []
    for document in sorted(package.documents.values(), key=lambda doc: doc.document_id):
        size = f"{document.byte_size} bytes" if document.byte_size is not None else "unknown size"
        document_lines.append(
            f'<span class="chain">{_esc(document.filename)}</span> '
            f'— sha256 {_esc(document.sha256)} — {_esc(document.file_format)}, {size}'
        )
    meta = [
        f"<div class=\"meta\">{_esc(package.protocol.id)} · {_esc(package.version)}"
        + (f" · approved {_esc(package.approval_date)}" if package.approval_date else "")
        + "</div>",
    ]
    if package.protocol.description:
        meta.append(f"<p>{_esc(package.protocol.description)}</p>")
    counts = (
        f"{len(package.rules)} rules · {len(package.variables)} variables · "
        f"{len(package.actions)} actions · {len(package.fragments)} fragments · "
        f"{len(package.test_cases)} test cases"
    )
    meta.append(f'<div class="meta">{counts}</div>')
    document_block = (
        '<div class="meta">Source document: ' + "<br>".join(document_lines) + "</div>"
        if document_lines
        else ""
    )
    return (
        "<header>"
        f"<h1>{_esc(package.protocol.name)}</h1>"
        + "".join(meta)
        + document_block
        + (
            f'<div class="derived">Derived view — canonical source of truth: '
            f"protocols/{_esc(package.protocol.id)}/{_esc(package.version)}/package.yaml</div>"
        )
        + "</header>"
    )


def _render_rule_card(
    package: ProtocolVersion,
    rule: Rule,
    shared_ids: tuple[str | None, str | None, tuple[str | None, ...]],
    shared_by_id: Mapping[str, Any],
) -> str:
    applies_shared, condition_shared, exception_shared = shared_ids
    parts = [
        f'<article class="card" id="{_esc(rule.id)}">',
        "<header>",
        f'<span class="rule-id">{_esc(rule.id)}</span>',
        f'<span class="badge status">{_esc(rule.validation_status.value)}</span>',
        f'<span class="badge derivation">{_esc(rule.provenance.derivation.value)}</span>',
        "</header>",
    ]
    if rule.notes:
        parts.append(f'<p class="notes">{_esc(rule.notes)}</p>')
    parts.append(
        '<p class="eval-order">Evaluation order: '
        "applies_to → condition → exceptions</p>"
    )
    if rule.applies_to is not None:
        parts.append(
            _render_expression_block("Applies to", rule.applies_to, applies_shared, shared_by_id)
        )
    parts.append(
        _render_expression_block("Condition", rule.condition, condition_shared, shared_by_id)
    )
    for index, exception in enumerate(rule.exceptions):
        shared_ref = exception_shared[index] if index < len(exception_shared) else None
        parts.append(
            _render_expression_block(
                f"Exception {index + 1}", exception, shared_ref, shared_by_id
            )
        )
    parts.append(_render_actions(package, rule))
    parts.append(_render_provenance(package, rule))
    parts.append("</article>")
    return "\n".join(parts)


def _render_expression_block(
    label: str,
    operand: object,
    shared_ref: str | None,
    shared_by_id: Mapping[str, Any],
) -> str:
    rendered = render_operand(operand)  # type: ignore[arg-type]
    badge = ""
    if shared_ref is not None:
        entry = shared_by_id.get(shared_ref)
        if entry is not None:
            badge = (
                f' <span class="badge shared">@{_esc(shared_ref)} · used '
                f"{entry.usage_count} times</span>"
            )
    return (
        f'<div class="expr-block"><span class="expr-label">{_esc(label)}{badge}</span>'
        f"<pre class=\"expr\">{_esc(rendered)}</pre></div>"
    )


def _render_actions(package: ProtocolVersion, rule: Rule) -> str:
    if not rule.action_refs:
        return (
            '<div class="actions"><span class="expr-label">Declared actions</span>'
            "<p class=\"payload\">(none declared)</p></div>"
        )
    resolved = [(ref, package.actions.get(ref)) for ref in rule.action_refs]
    prescribe_count = sum(
        1 for _, action in resolved if action is not None and action.type is ActionType.PRESCRIBE
    )
    alternatives = prescribe_count > 1
    title = "Declared actions"
    if alternatives:
        title += " (multiple PRESCRIBE = alternatives declared by the source)"
    parts = [f'<div class="actions"><span class="expr-label">{_esc(title)}</span><ul>']
    for ref, action in resolved:
        if action is None:
            parts.append(f"<li><code>{_esc(ref)}</code> (unresolved)</li>")
            continue
        marker = ""
        if alternatives and action.type is ActionType.PRESCRIBE:
            marker = ' <span class="alternative">[alternative]</span>'
        label = f" — {_esc(action.label)}" if action.label else ""
        parts.append(
            f"<li><code>{_esc(ref)}</code> "
            f'<span class="type">{_esc(action.type.value)}</span>{label}{marker}'
        )
        if action.payload:
            payload_text = "; ".join(
                f"{_esc(key)}: {_esc(value)}" for key, value in action.payload.items()
            )
            parts.append(f'<div class="payload">{payload_text}</div>')
        parts.append("</li>")
    parts.append("</ul>")
    if alternatives:
        parts.append(f'<p class="alt-note">{_ALTERNATIVES_NOTE}</p>')
    parts.append("</div>")
    return "\n".join(parts)


def _render_provenance(package: ProtocolVersion, rule: Rule) -> str:
    parts = [
        '<div class="provenance">',
        f'<span class="expr-label">Source</span> '
        f'<span class="chain">{_esc(rule.provenance.derivation.value)}</span>',
    ]
    for ref in rule.provenance.fragment_refs:
        fragment = package.fragments.get(ref)
        if fragment is None:
            parts.append(f'<div class="chain">{_esc(ref)} (unresolved)</div>')
            continue
        details: list[str] = []
        if fragment.page is not None:
            details.append(f"page {fragment.page}")
        if fragment.section:
            details.append(_esc(fragment.section))
        document_ref = ""
        if fragment.document_id:
            short_id = fragment.document_id[:12]
            document_ref = f" → {_esc(short_id)}"
        suffix = f" ({', '.join(details)})" if details else ""
        parts.append(
            f'<div class="chain">{_esc(ref)}{suffix}{document_ref}</div>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def _esc(text: object) -> str:
    """HTML-escape any rendered scalar deterministically."""
    return html.escape(str(text), quote=True)
