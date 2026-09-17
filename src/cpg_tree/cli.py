"""Command-line interface for the CPG Tree MVP.

The CLI is a thin, protocol-agnostic front end over the existing canonical
packages, validator, and deterministic engine. It never contains clinical
logic and never branches on protocol identity. All outputs are derived views.

Exit code contract:

    0  success (including evaluations with INDETERMINATE results)
    1  operational failure (discovery, malformed input, invalid package)
    2  usage error (argparse)

Errors print one concise ``error: <message>`` line to stderr unless
``--debug`` is given, in which case the traceback is re-raised.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from cpg_tree.engine import Case, evaluate_package
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.validation import FindingSeverity, validate_package
from cpg_tree.views.case_loader import load_case
from cpg_tree.views.discovery import discover_protocols, load_protocol
from cpg_tree.views.inspection import (
    build_summary,
    render_rule_detail,
    render_rules,
    render_summary,
    render_variables,
    rules_to_json,
    summary_to_json,
    variables_to_json,
)
from cpg_tree.views.provenance_view import provenance_to_json, render_provenance
from cpg_tree.views.results import evaluation_to_json, render_evaluation
from cpg_tree.views.tree import build_projection, projection_to_json, render_projection
from cpg_tree.views.visualize import load_manifest, visualize_package

EXIT_OK = 0
EXIT_ERROR = 1

_DESCRIPTION = "Inspect and evaluate computable clinical protocols (research prototype)."


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m cpg_tree",
        description=_DESCRIPTION,
    )
    parser.add_argument(
        "--protocols-root",
        default="protocols",
        help="directory tree of package artifacts (default: protocols/)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="re-raise failures with a full traceback instead of a one-line error",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list discovered protocols and versions")
    _add_json_argument(list_parser)
    list_parser.set_defaults(handler=_cmd_list)

    inspect_parser = subparsers.add_parser("inspect", help="show protocol metadata and counts")
    _add_protocol_arguments(inspect_parser)
    _add_json_argument(inspect_parser)
    inspect_parser.set_defaults(handler=_cmd_inspect)

    variables_parser = subparsers.add_parser("variables", help="show variable definitions")
    _add_protocol_arguments(variables_parser)
    _add_json_argument(variables_parser)
    variables_parser.set_defaults(handler=_cmd_variables)

    rules_parser = subparsers.add_parser("rules", help="list rules or show one rule in detail")
    _add_protocol_arguments(rules_parser)
    rules_parser.add_argument("--rule", help="show this rule in detail")
    _add_json_argument(rules_parser)
    rules_parser.set_defaults(handler=_cmd_rules)

    provenance_parser = subparsers.add_parser(
        "provenance", help="trace one element to its source evidence"
    )
    _add_protocol_arguments(provenance_parser)
    provenance_targets = provenance_parser.add_mutually_exclusive_group(required=True)
    provenance_targets.add_argument("--rule", help="rule id")
    provenance_targets.add_argument("--variable", help="variable id")
    provenance_targets.add_argument("--action", help="action id")
    provenance_targets.add_argument("--fragment", help="fragment id")
    provenance_parser.add_argument(
        "--no-evidence", action="store_true", help="hide verbatim source evidence"
    )
    _add_json_argument(provenance_parser)
    provenance_parser.set_defaults(handler=_cmd_provenance)

    tree_parser = subparsers.add_parser("tree", help="show the derived decision projection")
    _add_protocol_arguments(tree_parser)
    _add_json_argument(tree_parser)
    tree_parser.set_defaults(handler=_cmd_tree)

    validate_parser = subparsers.add_parser("validate", help="run package validation")
    _add_protocol_arguments(validate_parser)
    _add_json_argument(validate_parser)
    validate_parser.set_defaults(handler=_cmd_validate)

    visualize_parser = subparsers.add_parser(
        "visualize", help="generate a static HTML visualization of a protocol"
    )
    _add_protocol_arguments(visualize_parser)
    visualize_parser.add_argument(
        "--out",
        default="data/08_reporting",
        help="output directory (default: data/08_reporting)",
    )
    visualize_parser.set_defaults(handler=_cmd_visualize)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="evaluate a runtime case with the deterministic engine"
    )
    evaluate_parser.add_argument("protocol", help="protocol id")
    evaluate_parser.add_argument("case", help="path to the case JSON file")
    evaluate_parser.add_argument("version", nargs="?", help="protocol version")
    evaluate_parser.add_argument(
        "--show-expressions",
        action="store_true",
        help="render the condition expressions alongside each result",
    )
    _add_json_argument(evaluate_parser)
    evaluate_parser.set_defaults(handler=_cmd_evaluate)

    return parser


def _add_protocol_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("protocol", help="protocol id")
    parser.add_argument("version", nargs="?", help="protocol version (required if ambiguous)")


def _add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        handler: Callable[[argparse.Namespace], int] = args.handler
        return handler(args)
    except ValueError as error:
        if getattr(args, "debug", False):
            raise
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR


def _load_package(args: argparse.Namespace) -> tuple[ProtocolVersion, Path]:
    root = Path(args.protocols_root)
    package: ProtocolVersion
    artifact_path: Path
    package, artifact_path = load_protocol(discover_protocols(root), args.protocol, args.version)
    return package, artifact_path


def _print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.protocols_root)
    index = discover_protocols(root)
    entries: list[dict[str, Any]] = []
    for protocol_id in sorted(index):
        for version_id in sorted(index[protocol_id]):
            package, _ = load_protocol(index, protocol_id, version_id)
            if not args.json:
                print(
                    f"{protocol_id:<12} {version_id:<6} {package.protocol.name}"
                    + (f"  (approved {package.approval_date})" if package.approval_date else "")
                )
            entries.append(
                {
                    "id": protocol_id,
                    "name": package.protocol.name,
                    "versions": [
                        {
                            "version": version_id,
                            "approval_date": package.approval_date,
                            "path": str(index[protocol_id][version_id]),
                        }
                    ],
                }
            )
    if args.json:
        _print_json({"protocols": entries})
    return EXIT_OK


def _cmd_inspect(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    report = validate_package(package)
    summary = build_summary(package, report)
    if args.json:
        _print_json(summary_to_json(summary))
    else:
        print(render_summary(summary))
    return EXIT_OK


def _cmd_variables(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    if args.json:
        _print_json(variables_to_json(package))
    else:
        print(render_variables(package))
    return EXIT_OK


def _cmd_rules(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    if args.rule:
        if args.rule not in package.rules:
            raise ValueError(f"unknown rule {args.rule!r} in protocol {package.protocol.id!r}")
        if args.json:
            data = rules_to_json(package)
            selected = [entry for entry in data["rules"] if entry["id"] == args.rule]
            _print_json(
                {
                    "protocol_id": package.protocol.id,
                    "version": package.version,
                    "rules": selected,
                }
            )
        else:
            print(render_rule_detail(package, args.rule))
        return EXIT_OK
    if args.json:
        _print_json(rules_to_json(package))
    else:
        print(render_rules(package))
    return EXIT_OK


def _cmd_provenance(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    target_type, target_id = _provenance_target(args)
    if args.json:
        _print_json(provenance_to_json(package, target_type, target_id))
    else:
        print(
            render_provenance(package, target_type, target_id, show_evidence=not args.no_evidence)
        )
    return EXIT_OK


def _provenance_target(args: argparse.Namespace) -> tuple[str, str]:
    if args.rule:
        return "rule", args.rule
    if args.variable:
        return "variable", args.variable
    if args.action:
        return "action", args.action
    return "fragment", args.fragment


def _cmd_tree(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    projection = build_projection(package)
    if args.json:
        _print_json(projection_to_json(projection))
    else:
        print(render_projection(projection, package))
    return EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    report = validate_package(package)
    if args.json:
        _print_json(
            {
                "protocol_id": report.protocol_id,
                "version": report.version,
                "valid": report.is_valid(),
                "error_count": report.error_count,
                "warning_count": report.warning_count,
                "info_count": report.info_count,
                "findings": [
                    {
                        "code": finding.code,
                        "severity": finding.severity.value,
                        "message": finding.message,
                        "path": finding.path,
                        "related_ids": list(finding.related_ids),
                    }
                    for finding in report.findings
                ],
            }
        )
        return EXIT_OK
    valid = "yes" if report.is_valid() else "no"
    print(f"Validation : {report.protocol_id} {report.version}")
    print(
        f"  valid: {valid}  errors: {report.error_count}  warnings: "
        f"{report.warning_count}  info: {report.info_count}"
    )
    print(
        "  note: 'valid' means structural/provenance integrity of the package; "
        "it does not mean clinical validation"
    )
    if report.findings:
        print("  findings:")
        for finding in report.findings:
            related = f"  related: {', '.join(finding.related_ids)}" if finding.related_ids else ""
            location = f"  path: {finding.path}" if finding.path else ""
            print(f"    - [{finding.severity.value}] {finding.code}{location}{related}")
            print(f"        {finding.message}")
    return EXIT_OK


def _cmd_visualize(args: argparse.Namespace) -> int:
    package, artifact_path = _load_package(args)
    manifest = load_manifest(artifact_path.parent / "visualization.yaml")
    out_path = visualize_package(package, manifest, Path(args.out))
    print(out_path)
    return EXIT_OK


def _cmd_evaluate(args: argparse.Namespace) -> int:
    package, _ = _load_package(args)
    report = validate_package(package)
    if report.error_count > 0:
        codes = ", ".join(
            sorted(
                {
                    finding.code
                    for finding in report.findings
                    if finding.severity is FindingSeverity.ERROR
                }
            )
        )
        raise ValueError(
            f"package validation failed with {report.error_count} error(s) [{codes}]; "
            "refusing to evaluate"
        )
    case: Case = load_case(Path(args.case), package.variables)
    result = evaluate_package(package, case)
    if args.json:
        _print_json(evaluation_to_json(result, package, case))
    else:
        print(render_evaluation(result, package, case, show_expressions=args.show_expressions))
    return EXIT_OK
