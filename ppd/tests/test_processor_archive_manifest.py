from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.processor_archive_manifest import (
    ManifestValidationError,
    deterministic_handoff_id,
    validate_manifest,
    validate_manifest_file,
)


FIXTURES = Path(__file__).parent / "fixtures" / "processor_archive_manifest"


def test_valid_manifest_has_citation_backed_public_sources_and_deterministic_handoff() -> None:
    manifest_path = FIXTURES / "valid_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    result = validate_manifest_file(manifest_path)

    assert result == {
        "handoff_id": deterministic_handoff_id(manifest["public_sources"]),
        "public_source_count": 2,
    }


def test_rejects_private_devhub_material() -> None:
    manifest = json.loads((FIXTURES / "valid_manifest.json").read_text(encoding="utf-8"))
    manifest["prohibited_paths"] = ["devhub_session/auth_state.json"]
    manifest["handoff_id"] = deterministic_handoff_id(manifest["public_sources"])

    with pytest.raises(ManifestValidationError, match="private DevHub"):
        validate_manifest(manifest)


def test_rejects_raw_crawl_output() -> None:
    manifest = json.loads((FIXTURES / "valid_manifest.json").read_text(encoding="utf-8"))
    manifest["public_sources"][0]["archive_path"] = "archive/raw_crawl/source.html"
    manifest["handoff_id"] = deterministic_handoff_id(manifest["public_sources"])

    with pytest.raises(ManifestValidationError, match="raw crawl"):
        validate_manifest(manifest)


def test_rejects_missing_citations() -> None:
    manifest = json.loads((FIXTURES / "valid_manifest.json").read_text(encoding="utf-8"))
    manifest["public_sources"][0]["citations"] = []
    manifest["handoff_id"] = deterministic_handoff_id(manifest["public_sources"])

    with pytest.raises(ManifestValidationError, match="citation"):
        validate_manifest(manifest)


def test_rejects_non_deterministic_handoff_id() -> None:
    manifest = json.loads((FIXTURES / "valid_manifest.json").read_text(encoding="utf-8"))
    changed = copy.deepcopy(manifest)
    changed["handoff_id"] = "ppd-logic-not-derived-from-sources"

    with pytest.raises(ManifestValidationError, match="handoff_id"):
        validate_manifest(changed)
