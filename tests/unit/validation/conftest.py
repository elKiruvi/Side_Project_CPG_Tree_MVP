"""Shared builders for validation-layer tests.

All fixtures are synthetic and protocol-agnostic: they exercise the generic
knowledge model without any clinical content.
"""

from __future__ import annotations

import pytest

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
    SourceDocument,
    SourceFragment,
    ValidationItem,
    ValidationStatus,
    Variable,
    VariableType,
)

VALID_SHA256 = "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882"
DOCUMENT_ID = "doc-3a1654757801b7b6"
FRAGMENT_ID = "frag_1"
VERBATIM_TEXT = "criterion expressed in the source text"


@pytest.fixture
def valid_package() -> ProtocolVersion:
    return _build_valid_package()


def _build_valid_package() -> ProtocolVersion:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    document = SourceDocument(
        document_id=DOCUMENT_ID,
        filename="synthetic_protocol.pdf",
        sha256=VALID_SHA256,
        byte_size=1024,
    )
    fragment = SourceFragment(
        id=FRAGMENT_ID,
        document_id=DOCUMENT_ID,
        page=1,
        section="Criteria",
        verbatim_text=VERBATIM_TEXT,
    )
    variable = Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)
    action = Action(id="act_decide", type=ActionType.DECISION)
    rule = Rule(
        id="rule_x",
        condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
        action_refs=("act_decide",),
        provenance=Provenance(
            derivation=DerivationState.SOURCE_STATED,
            fragment_refs=(FRAGMENT_ID,),
        ),
    )
    return ProtocolVersion(
        protocol=protocol,
        version="v01",
        documents={DOCUMENT_ID: document},
        fragments={FRAGMENT_ID: fragment},
        variables={"flag_y": variable},
        actions={"act_decide": action},
        rules={"rule_x": rule},
    )


def make_fragment(
    fragment_id: str = FRAGMENT_ID,
    document_id: str | None = DOCUMENT_ID,
    page: int = 1,
    verbatim_text: str | None = VERBATIM_TEXT,
) -> SourceFragment:
    return SourceFragment(
        id=fragment_id,
        document_id=document_id,
        page=page,
        verbatim_text=verbatim_text,
    )


def make_rule(
    rule_id: str = "rule_x",
    derivation: DerivationState = DerivationState.SOURCE_STATED,
    fragment_refs: tuple[str, ...] = (FRAGMENT_ID,),
    notes: str | None = None,
    validation_status: ValidationStatus = ValidationStatus.DRAFT,
) -> Rule:
    return Rule(
        id=rule_id,
        condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
        action_refs=("act_decide",),
        provenance=Provenance(
            derivation=derivation,
            fragment_refs=fragment_refs,
            notes=notes,
        ),
        validation_status=validation_status,
    )


def make_validation_item(
    item_id: str = "vi_1",
    related_ids: tuple[str, ...] = (),
) -> ValidationItem:
    return ValidationItem(
        id=item_id,
        category="ambiguity",
        description="synthetic validation item",
        related_ids=related_ids,
    )
