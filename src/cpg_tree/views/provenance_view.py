"""Provenance chain view: rule/variable/action/fragment to source evidence.

The chain follows the canonical model only:

    target -> provenance -> fragment_refs -> SourceFragment -> SourceDocument

Verbatim evidence is rendered exactly as preserved by the package; nothing is
corrected, completed, or retrieved from outside. Unresolvable references are
shown explicitly and never silently repaired.
"""

from __future__ import annotations

from typing import Any

from cpg_tree.knowledge.documents import SourceDocument
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.provenance import Provenance, SourceFragment
from cpg_tree.knowledge.serialization import to_dict

_TARGET_TYPES = ("rule", "variable", "action", "fragment")


def render_provenance(
    version: ProtocolVersion,
    target_type: str,
    target_id: str,
    show_evidence: bool = True,
) -> str:
    """Render the provenance chain of one package element as plain text."""
    target, provenance = _resolve_target(version, target_type, target_id)
    lines = [f"Target     : {target_type} {target_id}"]
    if target_type == "fragment":
        lines.append("Note       : a fragment is itself source evidence; it has no provenance field")
    elif provenance is None:
        lines.append("Provenance : (none declared for this element)")
    else:
        lines.append(f"Derivation : {provenance.derivation.value}")
        if provenance.reviewer:
            lines.append(f"Reviewer   : {provenance.reviewer}")
        if provenance.reviewed_at:
            lines.append(f"Reviewed   : {provenance.reviewed_at}")
        if provenance.notes:
            lines.append(f"Notes      : {provenance.notes}")
        lines.append(f"Fragments  : {', '.join(provenance.fragment_refs) or '(none)'}")
    fragments = _referenced_fragments(version, target_type, target)
    if fragments:
        lines.append("Source fragments:")
        for fragment_id, fragment in fragments:
            lines.append(f"  {fragment_id}")
            if fragment is None:
                lines.append("    (unresolved: no such fragment in the package)")
                continue
            if fragment.document_id:
                lines.append(f"    document : {fragment.document_id}")
            if fragment.page is not None:
                lines.append(f"    page     : {fragment.page}")
            if fragment.section:
                lines.append(f"    section  : {fragment.section}")
            if show_evidence and fragment.verbatim_text:
                lines.append(f"    evidence : {fragment.verbatim_text!r}")
    documents = _referenced_documents(version, target_type, target)
    if documents:
        lines.append("Source documents:")
        for document in documents:
            size = f"{document.byte_size} bytes" if document.byte_size is not None else "unknown"
            lines.append(f"  {document.document_id}")
            lines.append(f"    filename : {document.filename}")
            lines.append(f"    sha256   : {document.sha256}")
            lines.append(f"    format   : {document.file_format}")
            lines.append(f"    size     : {size}")
    return "\n".join(lines)


def provenance_to_json(
    version: ProtocolVersion,
    target_type: str,
    target_id: str,
) -> dict[str, Any]:
    """Project the provenance chain into primitives in fixed key order."""
    target, provenance = _resolve_target(version, target_type, target_id)
    fragments = [
        {
            "id": fragment_id,
            "document_id": fragment.document_id if fragment is not None else None,
            "page": fragment.page if fragment is not None else None,
            "section": fragment.section if fragment is not None else None,
            "verbatim_text": fragment.verbatim_text if fragment is not None else None,
        }
        for fragment_id, fragment in _referenced_fragments(version, target_type, target)
    ]
    documents = [
        to_dict(document) for document in _referenced_documents(version, target_type, target)
    ]
    return {
        "protocol_id": version.protocol.id,
        "version": version.version,
        "target": {"type": target_type, "id": target_id},
        "provenance": to_dict(provenance) if provenance is not None else None,
        "fragments": fragments,
        "documents": documents,
    }


def _resolve_target(
    version: ProtocolVersion,
    target_type: str,
    target_id: str,
) -> tuple[object, Provenance | None]:
    if target_type not in _TARGET_TYPES:
        raise ValueError(f"unknown provenance target type {target_type!r}")
    if target_type == "fragment":
        fragment = version.fragments.get(target_id)
        if fragment is None:
            raise ValueError(f"unknown fragment {target_id!r} in protocol {version.protocol.id!r}")
        return fragment, None
    if target_type == "rule":
        element: object | None = version.rules.get(target_id)
    elif target_type == "variable":
        element = version.variables.get(target_id)
    else:
        element = version.actions.get(target_id)
    if element is None:
        raise ValueError(
            f"unknown {target_type} {target_id!r} in protocol {version.protocol.id!r}"
        )
    return element, getattr(element, "provenance", None)


def _referenced_fragments(
    version: ProtocolVersion,
    target_type: str,
    target: object,
) -> list[tuple[str, SourceFragment | None]]:
    if target_type == "fragment" and isinstance(target, SourceFragment):
        return [(target.id, target)]
    provenance: Provenance | None = getattr(target, "provenance", None)
    refs = provenance.fragment_refs if provenance is not None else ()
    return [(ref, version.fragments.get(ref)) for ref in refs]


def _referenced_documents(
    version: ProtocolVersion,
    target_type: str,
    target: object,
) -> list[SourceDocument]:
    document_ids: set[str] = set()
    for _, fragment in _referenced_fragments(version, target_type, target):
        if fragment is not None and fragment.document_id is not None:
            document_ids.add(fragment.document_id)
    return [
        version.documents[document_id]
        for document_id in sorted(document_ids)
        if document_id in version.documents
    ]
