"""Tests for generic artifact discovery and loading."""

from __future__ import annotations

from dataclasses import replace

import pytest

from cpg_tree.knowledge import ProtocolVersion, dump_package
from cpg_tree.views.discovery import DiscoveryError, discover_protocols, load_protocol


def _write_artifact(
    root,
    protocol_id: str,
    version: str,
    package: ProtocolVersion,
) -> None:
    target = root / protocol_id / version
    target.mkdir(parents=True)
    versioned = replace(package, version=version)
    (target / "package.yaml").write_text(dump_package(versioned), encoding="utf-8")


def test_discovers_protocols_sorted(tmp_path, synthetic_package: ProtocolVersion) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "TEST-PL-999", "v01", synthetic_package)
    _write_artifact(root, "OTHER-PL-111", "v02", synthetic_package)
    index = discover_protocols(root)
    assert list(index) == ["OTHER-PL-111", "TEST-PL-999"]
    assert list(index["TEST-PL-999"]) == ["v01"]


def test_discovers_multiple_versions_sorted(
    tmp_path, synthetic_package: ProtocolVersion
) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "TEST-PL-999", "v02", synthetic_package)
    _write_artifact(root, "TEST-PL-999", "v01", synthetic_package)
    index = discover_protocols(root)
    assert list(index["TEST-PL-999"]) == ["v01", "v02"]


def test_ignores_directories_without_package_artifact(tmp_path) -> None:
    root = tmp_path / "protocols"
    (root / "TEST-PL-999" / "v01").mkdir(parents=True)
    (root / "TEST-PL-999" / "notes.txt").write_text("not an artifact", encoding="utf-8")
    assert discover_protocols(root) == {}


def test_loads_single_version_without_selector(
    tmp_path, synthetic_package: ProtocolVersion
) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "TEST-PL-999", "v01", synthetic_package)
    package, path = load_protocol(discover_protocols(root), "TEST-PL-999")
    assert package.protocol.id == "TEST-PL-999"
    assert package.version == "v01"
    assert path.name == "package.yaml"


def test_unknown_protocol_fails_deterministically(
    tmp_path, synthetic_package: ProtocolVersion
) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "TEST-PL-999", "v01", synthetic_package)
    with pytest.raises(DiscoveryError, match="unknown protocol 'TEST-PL-000'"):
        load_protocol(discover_protocols(root), "TEST-PL-000")


def test_unknown_version_fails_deterministically(
    tmp_path, synthetic_package: ProtocolVersion
) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "TEST-PL-999", "v01", synthetic_package)
    with pytest.raises(DiscoveryError, match="unknown version 'v09'"):
        load_protocol(discover_protocols(root), "TEST-PL-999", "v09")


def test_multiple_versions_require_explicit_selector(
    tmp_path, synthetic_package: ProtocolVersion
) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "TEST-PL-999", "v01", synthetic_package)
    _write_artifact(root, "TEST-PL-999", "v02", synthetic_package)
    with pytest.raises(DiscoveryError, match="multiple versions"):
        load_protocol(discover_protocols(root), "TEST-PL-999")
    package, _ = load_protocol(discover_protocols(root), "TEST-PL-999", "v02")
    assert package.version == "v02"


def test_malformed_yaml_raises_value_error(tmp_path) -> None:
    root = tmp_path / "protocols"
    target = root / "TEST-PL-999" / "v01"
    target.mkdir(parents=True)
    (target / "package.yaml").write_text("protocol: [unclosed", encoding="utf-8")
    with pytest.raises(DiscoveryError, match="malformed package YAML"):
        load_protocol(discover_protocols(root), "TEST-PL-999")


def test_directory_identity_must_match_package(
    tmp_path, synthetic_package: ProtocolVersion
) -> None:
    root = tmp_path / "protocols"
    _write_artifact(root, "OTHER-PL-111", "v01", synthetic_package)
    with pytest.raises(DiscoveryError, match="declares protocol id 'TEST-PL-999'"):
        load_protocol(discover_protocols(root), "OTHER-PL-111")
    target = root / "TEST-PL-999" / "v02"
    target.mkdir(parents=True)
    (target / "package.yaml").write_text(dump_package(synthetic_package), encoding="utf-8")
    with pytest.raises(DiscoveryError, match="declares version 'v01'"):
        load_protocol(discover_protocols(root), "TEST-PL-999", "v02")
