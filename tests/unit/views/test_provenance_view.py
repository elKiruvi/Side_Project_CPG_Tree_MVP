"""Tests for the provenance chain view."""

from __future__ import annotations

from dataclasses import replace

import pytest

from cpg_tree.knowledge import (
    DerivationState,
    ProtocolVersion,
    Provenance,
    Rule,
)
from cpg_tree.views.provenance_view import (
    provenance_to_json,
    render_provenance,
)


def test_rule_chain_reaches_fragment_and_document(
    synthetic_package: ProtocolVersion,
) -> None:
    text = render_provenance(synthetic_package, "rule", "rule_composite")
    assert "Target     : rule rule_composite" in text
    assert "Derivation : SOURCE_STATED" in text
    assert "frag_1" in text
    assert "document : doc-0123456789abcdef" in text
    assert "page     : 3" in text
    assert "section  : Criterios" in text
    assert "Fuente sintética" in text
    assert "sha256   : " + "a" * 64 in text


def test_evidence_can_be_hidden(synthetic_package: ProtocolVersion) -> None:
    text = render_provenance(synthetic_package, "rule", "rule_composite", show_evidence=False)
    assert "Fuente sintética" not in text
    assert "page     : 3" in text


def test_variable_and_action_targets(synthetic_package: ProtocolVersion) -> None:
    variable_text = render_provenance(synthetic_package, "variable", "count_x")
    assert "Target     : variable count_x" in variable_text
    assert "Derivation : SOURCE_STATED" in variable_text
    action_text = render_provenance(synthetic_package, "action", "act_request")
    assert "Provenance : (none declared for this element)" in action_text


def test_fragment_target(synthetic_package: ProtocolVersion) -> None:
    text = render_provenance(synthetic_package, "fragment", "frag_1")
    assert "Target     : fragment frag_1" in text
    assert "document : doc-0123456789abcdef" in text
    assert "page     : 3" in text


def test_unknown_targets_fail_deterministically(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(ValueError, match="unknown rule 'nope'"):
        render_provenance(synthetic_package, "rule", "nope")
    with pytest.raises(ValueError, match="unknown provenance target type 'clinical'"):
        render_provenance(synthetic_package, "clinical", "anything")


def test_unresolved_fragment_ref_is_rendered_explicitly(
    synthetic_package: ProtocolVersion,
) -> None:
    rule = Rule(
        id="rule_broken",
        condition=synthetic_package.rules["rule_alternatives"].condition,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("missing_frag",)),
    )
    package = replace(synthetic_package, rules={**synthetic_package.rules, "rule_broken": rule})
    text = render_provenance(package, "rule", "rule_broken")
    assert "(unresolved: no such fragment in the package)" in text


def test_provenance_json_schema_is_stable(synthetic_package: ProtocolVersion) -> None:
    data = provenance_to_json(synthetic_package, "rule", "rule_composite")
    assert list(data) == [
        "protocol_id",
        "version",
        "target",
        "provenance",
        "fragments",
        "documents",
    ]
    assert data["target"] == {"type": "rule", "id": "rule_composite"}
    assert data["fragments"][0]["id"] == "frag_1"
    assert data["fragments"][0]["verbatim_text"].startswith("Fuente sintética")
    assert data["documents"][0]["document_id"] == "doc-0123456789abcdef"
