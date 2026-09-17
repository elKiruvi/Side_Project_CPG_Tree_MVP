"""Minimal hand-crafted PDF builder for extraction tests.

Builds tiny, deterministic PDFs in memory so tests need neither binary
fixtures nor additional dependencies. Only plain Latin-1 text is supported,
which is sufficient for the generic extraction-layer tests.
"""

from __future__ import annotations

_XREF_ENTRY_LENGTH = 20


def make_minimal_pdf(pages: list[str]) -> bytes:
    """Build a minimal PDF with one page per entry in ``pages``.

    An empty string produces a page with an empty content stream, which text
    extractors report as a page with no extractable text.
    """
    page_count = len(pages)
    if page_count < 1:
        raise ValueError("at least one page is required")
    font_id = 2 * page_count + 3
    objects: list[tuple[int, bytes]] = []
    page_ids = [2 * index + 3 for index in range(page_count)]
    content_ids = [2 * index + 4 for index in range(page_count)]

    objects.append((1, _render_object(1, b"<< /Type /Catalog /Pages 2 0 R >>")))
    kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
    objects.append(
        (
            2,
            _render_object(
                2,
                b"<< /Type /Pages /Kids ["
                + kids
                + b"] /Count "
                + str(page_count).encode()
                + b" >>",
            ),
        )
    )
    for page_id, content_id, text in zip(page_ids, content_ids, pages, strict=True):
        stream = _content_stream(text)
        objects.append(
            (
                content_id,
                _render_object(
                    content_id,
                    b"<< /Length "
                    + str(len(stream)).encode()
                    + b" >>\nstream\n"
                    + stream
                    + b"\nendstream",
                ),
            )
        )
        objects.append(
            (
                page_id,
                _render_object(
                    page_id,
                    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents "
                    + str(content_id).encode()
                    + b" 0 R /Resources << /Font << /F1 "
                    + str(font_id).encode()
                    + b" 0 R >> >> >>",
                ),
            )
        )
    objects.append(
        (
            font_id,
            _render_object(font_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        )
    )
    objects.sort(key=lambda pair: pair[0])

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    document_body = header + b"".join(object_body for _, object_body in objects)
    offsets: dict[int, int] = {}
    position = len(header)
    for object_id, object_body in objects:
        offsets[object_id] = position
        position += len(object_body)
    xref_offset = position

    total_objects = len(objects) + 1
    xref_lines = [f"xref\n0 {total_objects}\n".encode()]
    xref_lines.append(b"0000000000 65535 f \r\n")
    for object_id in range(1, total_objects):
        xref_lines.append(f"{offsets[object_id]:010d} 00000 n \r\n".encode())
    xref_lines.append(
        b"trailer\n<< /Size "
        + str(total_objects).encode()
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF\n"
    )
    return document_body + b"".join(xref_lines)


def _render_object(object_id: int, content: bytes) -> bytes:
    return str(object_id).encode() + b" 0 obj\n" + content + b"\nendobj\n"


def _content_stream(text: str) -> bytes:
    segments = [f"({_escape(segment)}) Tj T*" for segment in text.split("\n")]
    if not segments:
        return b""
    return ("BT /F1 12 Tf 72 720 Td " + " ".join(segments) + " ET").encode("latin-1")


def _escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
