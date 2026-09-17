"""Protocol-specific knowledge packages.

Modules in this package are protocol knowledge, not generic infrastructure.
The generic layers (engine, validation, extraction, knowledge model) must
never import from here. Each module builds one versioned protocol package
from its source evidence; the serialized artifact lives under
``protocols/<id>/<version>/package.yaml``.

Current builders:

- ``nac_v09`` — NAC CT-PL-193 v09 (neumonía adquirida en comunidad).
- ``itu_v06`` — ITU CT-PL-197 v06 (infección del tracto urinario y
  bacteriuria asintomática en población adulta).
"""
