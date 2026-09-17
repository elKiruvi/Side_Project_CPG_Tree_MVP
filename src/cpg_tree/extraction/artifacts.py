"""Write extraction results as reproducible intermediate artifacts.

Artifacts live under an intermediate directory (typically
``data/02_intermediate/<document_id>/``) and contain extraction facts only —
never canonical clinical knowledge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cpg_tree.extraction.model import ExtractionResult
from cpg_tree.knowledge.provenance import SourceFragment


def write_artifacts(result: ExtractionResult, target_dir: str | Path) -> list[Path]:
    """Write source_document.yaml, pages/page_NNN.txt, fragments.yaml, report.txt.

    Returns the list of written paths. With a fixed ``extracted_at``, writing
    the same result twice produces byte-identical artifacts.
    """
    directory = Path(target_dir)
    pages_dir = directory / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    source_path = directory / "source_document.yaml"
    source_path.write_text(
        yaml.safe_dump(_document_to_dict(result), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    written.append(source_path)

    for page in result.record.pages:
        page_path = pages_dir / f"page_{page.page_number:03d}.txt"
        page_path.write_text(page.text, encoding="utf-8")
        written.append(page_path)

    fragments_path = directory / "fragments.yaml"
    fragments_path.write_text(
        yaml.safe_dump(
            [_fragment_to_dict(fragment) for fragment in result.fragments],
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    written.append(fragments_path)

    report_path = directory / "report.txt"
    report_path.write_text(_render_report(result), encoding="utf-8")
    written.append(report_path)

    return written


def _document_to_dict(result: ExtractionResult) -> dict[str, Any]:
    document = result.document
    record = result.record
    return {
        "document": {
            "document_id": document.document_id,
            "filename": document.filename,
            "sha256": document.sha256,
            "file_format": document.file_format,
            "byte_size": document.byte_size,
        },
        "extraction": {
            "document_id": record.document_id,
            "tool": record.tool,
            "tool_version": record.tool_version,
            "extracted_at": record.extracted_at,
            "page_count": record.page_count,
            "sparse_threshold": record.sparse_threshold,
            "pages": [
                {
                    "page_number": page.page_number,
                    "char_count": page.char_count,
                    "status": page.status.value,
                    "embedded_image_count": page.embedded_image_count,
                }
                for page in record.pages
            ],
        },
    }


def _fragment_to_dict(fragment: SourceFragment) -> dict[str, Any]:
    return {
        "id": fragment.id,
        "document_id": fragment.document_id,
        "page": fragment.page,
        "section": fragment.section,
        "verbatim_text": fragment.verbatim_text,
    }


def _render_report(result: ExtractionResult) -> str:
    document = result.document
    record = result.record
    lines = [
        f"Extraction report - {document.document_id}",
        "=" * 40,
        f"source file  : {document.filename}",
        f"sha256       : {document.sha256}",
        f"format       : {document.file_format}",
        f"bytes        : {document.byte_size}",
        f"pages        : {record.page_count}",
        f"tool         : {record.tool} {record.tool_version}",
        f"extracted at : {record.extracted_at}",
        "",
        "Page table",
        "----------",
        f"{'page':>4}  {'status':<16} {'chars':>6}  {'images':>6}  section candidate",
    ]
    for page in record.pages:
        section = next(
            (
                fragment.section
                for fragment in result.fragments
                if fragment.page == page.page_number
            ),
            None,
        )
        images = str(page.embedded_image_count) if page.embedded_image_count is not None else "n/a"
        lines.append(
            f"{page.page_number:>4}  {page.status.value:<16} "
            f"{page.char_count:>6}  {images:>6}  {section or '-'}"
        )
    lines.append("")
    lines.append(
        "Status vocabulary: OK = text extracted; SPARSE_TEXT = few characters; "
        "NO_TEXT = no extractable text detected; EXTRACTION_ERROR = text "
        "extraction raised an error. 'images' counts embedded image XObjects "
        "(n/a = not inspectable). Section values are detected uppercase-line "
        "candidates only; they are not semantic claims."
    )
    return "\n".join(lines) + "\n"
