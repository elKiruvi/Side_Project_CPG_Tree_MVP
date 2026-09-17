"""Generic protocol artifact discovery and loading.

Protocols are discovered from the committed artifact tree:

    protocols/<protocol_id>/<version>/package.yaml

Discovery is purely directory-driven: no registry, no builder imports, and no
protocol-specific knowledge. The same mechanism serves every protocol, and a
new protocol becomes visible by adding its versioned artifact directory.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.serialization import load_package

type DiscoveryIndex = dict[str, dict[str, Path]]

_PACKAGE_FILENAME = "package.yaml"


class DiscoveryError(ValueError):
    """Deterministic discovery failure: unknown protocol/version or an
    artifact whose directory identity does not match the package identity."""


def discover_protocols(root: Path) -> DiscoveryIndex:
    """Scan the artifact tree and return an index keyed by id then version.

    Protocol and version directories are returned in sorted order. Version
    directories without a ``package.yaml`` are ignored, so unrelated content
    under the root does not break discovery.
    """
    index: DiscoveryIndex = {}
    for protocol_dir in sorted(root.iterdir()) if root.is_dir() else []:
        if not protocol_dir.is_dir():
            continue
        versions: dict[str, Path] = {}
        for version_dir in sorted(protocol_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            package_path = version_dir / _PACKAGE_FILENAME
            if package_path.is_file():
                versions[version_dir.name] = package_path
        if versions:
            index[protocol_dir.name] = versions
    return index


def load_protocol(
    index: DiscoveryIndex,
    protocol_id: str,
    version: str | None = None,
) -> tuple[ProtocolVersion, Path]:
    """Load one package from the index, verifying its directory identity.

    When ``version`` is omitted the protocol must have exactly one version;
    never a guessed "latest". The loaded package must agree with its directory
    location (protocol id and version), otherwise ``DiscoveryError`` is raised
    so a mis-placed artifact can never be evaluated silently.
    """
    versions = index.get(protocol_id)
    if not versions:
        raise DiscoveryError(f"unknown protocol {protocol_id!r}")
    if version is None:
        if len(versions) != 1:
            available = ", ".join(sorted(versions))
            raise DiscoveryError(
                f"protocol {protocol_id!r} has multiple versions; specify one of: {available}"
            )
        version = next(iter(versions))
    package_path = versions.get(version)
    if package_path is None:
        available = ", ".join(sorted(versions))
        raise DiscoveryError(
            f"unknown version {version!r} for protocol {protocol_id!r}; available: {available}"
        )
    try:
        package = load_package(package_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise DiscoveryError(f"malformed package YAML at {package_path}: {error}") from error
    if package.protocol.id != protocol_id:
        raise DiscoveryError(
            f"artifact at {package_path} declares protocol id {package.protocol.id!r}; "
            f"expected {protocol_id!r}"
        )
    if package.version != version:
        raise DiscoveryError(
            f"artifact at {package_path} declares version {package.version!r}; "
            f"expected {version!r}"
        )
    return package, package_path
