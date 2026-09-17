"""End-to-end chain test: synthetic PDF -> SourceDocument -> SourceFragment
-> Rule, audited by the generic validator.

No clinical content is involved: the synthetic PDF carries generic text and
the package uses only generic model classes.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from unit.extraction.fixtures import make_minimal_pdf

from cpg_tree.extraction import ExtractionResult, extract_pdf
from cpg_tree.knowledge import (
    Action,
    ActionType,
    Condition,
    ConditionKind,
    DerivationState,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    Variable,
    VariableType,
)
from cpg_tree.validation import validate_package

FIXED_TIMESTAMP = "2026-09-17T00:00:00+00:00"


def _package_from_result(result: ExtractionResult) -> ProtocolVersion:
    return ProtocolVersion(
        protocol=Protocol(id="TEST-PL-900", name="Chain Protocol"),
        version="v01",
        documents={result.document.document_id: result.document},
        fragments={fragment.id: fragment for fragment in result.fragments},
        variables={"flag_y": Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)},
        actions={"act_decide": Action(id="act_decide", type=ActionType.DECISION)},
        rules={
            "rule_x": Rule(
                id="rule_x",
                condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
                action_refs=("act_decide",),
                provenance=Provenance(
                    derivation=DerivationState.SOURCE_STATED,
                    fragment_refs=(result.fragments[0].id,),
                ),
            )
        },
    )


def _extract(tmp_path: Path) -> ExtractionResult:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf(["CRITERION TEXT", "SECOND PAGE TEXT"]))
    return extract_pdf(pdf_path, extracted_at=FIXED_TIMESTAMP)


def test_extraction_chain_validates_clean(tmp_path: Path) -> None:
    result = _extract(tmp_path)
    report = validate_package(_package_from_result(result))
    assert report.is_valid()
    assert report.findings == ()


def test_broken_fragment_reference_breaks_the_chain(tmp_path: Path) -> None:
    result = _extract(tmp_path)
    package = _package_from_result(result)
    rule = replace(
        package.rules["rule_x"],
        provenance=Provenance(derivation=DerivationState.SOURCE_STATED),
    )
    broken = replace(package, rules={"rule_x": rule})
    report = validate_package(broken)
    codes = {finding.code for finding in report.findings}
    assert "PROV.SOURCE_STATED_NO_REFERENCE" in codes
    assert not report.is_valid()


def test_fragment_document_mismatch_breaks_the_chain(tmp_path: Path) -> None:
    result = _extract(tmp_path)
    package = _package_from_result(result)
    first = package.fragments[result.fragments[0].id]
    tampered = replace(first, document_id="doc-0000000000000000")
    fragments = dict(package.fragments)
    fragments[tampered.id] = tampered
    broken = replace(package, fragments=fragments)
    report = validate_package(broken)
    codes = {finding.code for finding in report.findings}
    assert "PROV.UNKNOWN_DOCUMENT" in codes
    assert not report.is_valid()


def test_fragment_identity_is_content_addressed(tmp_path: Path) -> None:
    first = _extract(tmp_path)
    second = _extract(tmp_path)
    assert first.document.document_id == second.document.document_id
    assert [fragment.id for fragment in first.fragments] == [
        fragment.id for fragment in second.fragments
    ]
