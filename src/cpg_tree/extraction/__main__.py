"""Command-line runner: python -m cpg_tree.extraction <pdf> [--out DIR]."""

from __future__ import annotations

import argparse
from pathlib import Path

from cpg_tree.extraction.artifacts import write_artifacts
from cpg_tree.extraction.extractor import extract_pdf

_DEFAULT_SPARSE_THRESHOLD = 100


def _default_out(document_id: str) -> Path:
    return Path("data") / "02_intermediate" / document_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cpg_tree.extraction",
        description="Extract a source PDF into traceable intermediate artifacts.",
    )
    parser.add_argument("pdf", help="path to the source PDF")
    parser.add_argument(
        "--out",
        help="target directory for artifacts (default: data/02_intermediate/<document_id>)",
    )
    parser.add_argument(
        "--sparse-threshold",
        type=int,
        default=_DEFAULT_SPARSE_THRESHOLD,
        help="char count at or below which a non-empty page is SPARSE_TEXT (default: 100)",
    )
    args = parser.parse_args(argv)
    result = extract_pdf(args.pdf, sparse_threshold=args.sparse_threshold)
    out_dir = Path(args.out) if args.out else _default_out(result.document.document_id)
    write_artifacts(result, out_dir)
    print(f"document_id : {result.document.document_id}")
    print(f"sha256      : {result.document.sha256}")
    print(f"pages       : {result.record.page_count}")
    print(f"artifacts   : {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
