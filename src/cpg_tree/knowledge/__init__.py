"""Canonical knowledge model for computable clinical protocols.

The model is protocol-agnostic: it knows about variables, conditions, logical
expressions, rules, actions, provenance, and test cases, but nothing about any
specific clinical protocol. Clinical knowledge lives in protocol packages.
"""

from cpg_tree.knowledge.conditions import Condition, LogicalExpression
from cpg_tree.knowledge.enums import (
    ActionType,
    ComparisonOperator,
    ConditionKind,
    DerivationState,
    LogicalOperator,
    TemporalOperator,
    TruthValue,
    ValidationItemStatus,
    ValidationStatus,
    VariableType,
)
from cpg_tree.knowledge.protocol import Protocol, ProtocolVersion
from cpg_tree.knowledge.provenance import Provenance, SourceFragment, ValidationItem
from cpg_tree.knowledge.rules import Action, Rule
from cpg_tree.knowledge.serialization import dump_package, from_dict, load_package, to_dict
from cpg_tree.knowledge.test_case import TestCase
from cpg_tree.knowledge.types import Scalar, ScalarOperand
from cpg_tree.knowledge.variables import Variable

__all__ = [
    "Action",
    "ActionType",
    "ComparisonOperator",
    "Condition",
    "ConditionKind",
    "DerivationState",
    "LogicalExpression",
    "LogicalOperator",
    "Protocol",
    "ProtocolVersion",
    "Provenance",
    "Rule",
    "Scalar",
    "ScalarOperand",
    "SourceFragment",
    "TemporalOperator",
    "TestCase",
    "TruthValue",
    "ValidationItem",
    "ValidationItemStatus",
    "ValidationStatus",
    "Variable",
    "VariableType",
    "dump_package",
    "from_dict",
    "load_package",
    "to_dict",
]
