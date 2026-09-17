"""Protocol-specific knowledge packages.

Modules in this package are protocol knowledge, not generic infrastructure.
The generic layers (engine, validation, extraction, knowledge model) must
never import from here. Each module builds one versioned protocol package
from its source evidence; the serialized artifact lives under
``protocols/<id>/<version>/package.yaml``.
"""
