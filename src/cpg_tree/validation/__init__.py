"""Package-level validation for computable protocol knowledge packages.

The validator audits ``ProtocolVersion`` packages without mutating them and
never evaluates conditions. Reports describe provenance traceability and
referential integrity only; they never claim clinical validity.
"""

from cpg_tree.validation.model import (
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
    dump_report,
    load_report,
)
from cpg_tree.validation.package_checks import validate_package

__all__ = [
    "FindingSeverity",
    "ValidationFinding",
    "ValidationReport",
    "dump_report",
    "load_report",
    "validate_package",
]
