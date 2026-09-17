"""Derived views over the canonical knowledge model and the rule engine.

Views are pure, deterministic projections: rendering, artifact discovery,
inspection, provenance chains, the decision-tree projection, evaluation
result rendering, and runtime case loading. They contain no clinical
knowledge and never evaluate conditions themselves; the Phase 4 engine is
the only evaluator.

The package initializer is intentionally minimal; import view functions from
their modules (for example ``cpg_tree.views.discovery``).
"""
