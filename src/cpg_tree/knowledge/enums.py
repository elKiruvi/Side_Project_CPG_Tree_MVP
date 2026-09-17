"""Enumerations of the canonical knowledge model."""

from enum import StrEnum


class VariableType(StrEnum):
    """Generic type of a clinical variable."""

    NUMERIC = "NUMERIC"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"
    DURATION = "DURATION"


class ConditionKind(StrEnum):
    """Discriminates the atomic predicate represented by a Condition."""

    COMPARISON = "COMPARISON"
    MEMBERSHIP = "MEMBERSHIP"
    FLAG = "FLAG"
    TEMPORAL = "TEMPORAL"


class ComparisonOperator(StrEnum):
    """Operators for numeric comparison predicates."""

    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"


class TemporalOperator(StrEnum):
    """Temporal predicates supported by the MVP model."""

    AT_LEAST_FOR_LAST = "AT_LEAST_FOR_LAST"
    WITHIN_LAST = "WITHIN_LAST"


class LogicalOperator(StrEnum):
    """Operators for composite logical expressions."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    AT_LEAST_N = "AT_LEAST_N"


class ActionType(StrEnum):
    """Generic consequence kinds a rule may recommend."""

    DECISION = "DECISION"
    REQUEST_TEST = "REQUEST_TEST"
    ADMIT = "ADMIT"
    DISCHARGE = "DISCHARGE"
    PRESCRIBE = "PRESCRIBE"
    FOLLOW_UP = "FOLLOW_UP"
    CLASSIFY = "CLASSIFY"
    EDUCATE = "EDUCATE"
    RESTRICTION = "RESTRICTION"


class DerivationState(StrEnum):
    """How a knowledge element was derived from its source."""

    SOURCE_STATED = "SOURCE_STATED"
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    INFERRED = "INFERRED"
    VALIDATED = "VALIDATED"
    UNRESOLVED = "UNRESOLVED"


class ValidationStatus(StrEnum):
    """Review state of a knowledge element."""

    DRAFT = "DRAFT"
    EXTRACTED = "EXTRACTED"
    REVIEWED = "REVIEWED"
    VALIDATED = "VALIDATED"
    UNRESOLVED = "UNRESOLVED"


class ValidationItemStatus(StrEnum):
    """Lifecycle state of a validation item."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class TruthValue(StrEnum):
    """Three-valued logic state used by test expectations and the future engine."""

    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
