"""Source-reconciliation model for clinical relationship candidates (Phase 10 D2.5).

This package is a controlled reconciliation layer over the human-review
relationship inventories under ``evaluation/pathway/``. It classifies every
candidate relationship against the source evidence and records source
conflicts explicitly. It is deliberately NOT part of the canonical knowledge
model and NOT part of the presentation/views layer:

- it never modifies ``package.yaml``, rules, conditions, actions, or engine
  semantics;
- it never evaluates conditions;
- it contains no protocol-specific clinical knowledge (protocol-agnostic);
- its statuses are reconciliation evidence for a future pathway phase, not
  approvals: nothing here is clinically validated.

Terminology is deliberate: outputs are "source-reconciled" and
"structurally/source reviewed", never "clinically validated".
"""

from cpg_tree.reconciliation.model import (
    ConflictRepresentation,
    ConflictResolution,
    ConflictStatus,
    EvidenceClass,
    PresentationRole,
    ReconciledCandidate,
    ReconciliationInventory,
    ReconciliationStatus,
    ReviewStatus,
    SourceConflict,
    SourceEvidenceStatus,
    SourceRepresentation,
)

__all__ = [
    "ConflictRepresentation",
    "ConflictResolution",
    "ConflictStatus",
    "EvidenceClass",
    "PresentationRole",
    "ReconciledCandidate",
    "ReconciliationInventory",
    "ReconciliationStatus",
    "ReviewStatus",
    "SourceConflict",
    "SourceEvidenceStatus",
    "SourceRepresentation",
]
