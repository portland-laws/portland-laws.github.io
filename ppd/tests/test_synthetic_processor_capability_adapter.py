"""Tests for the synthetic PP&D processor-capability adapter."""

from __future__ import annotations

import json
from pathlib import Path

from ppd.processor_suite.synthetic_processor_capability_adapter import (
    build_synthetic_processor_capability_fixture,
    validate_synthetic_processor_capability_fixture,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "processor_capabilities"
    / "synthetic_ppd_processor_capabilities.json"
)


def _load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_committed_fixture_matches_adapter_output():
    assert _load_fixture() == build_synthetic_processor_capability_fixture()


def test_fixture_covers_expected_capture_types_in_order():
    fixture = _load_fixture()

    assert fixture["capture_types"] == ["html", "pdf", "warc", "metadata"]
    assert [entry["capture_type"] for entry in fixture["capabilities"]] == [
        "html",
        "pdf",
        "warc",
        "metadata",
    ]


def test_fixture_is_commit_safe_and_does_not_import_live_processors():
    fixture = _load_fixture()

    assert fixture["constraints"] == {
        "imports_network_processors": False,
        "writes_raw_archives": False,
        "deterministic": True,
    }

    for entry in fixture["capabilities"]:
        assert entry["raw_archive_written"] is False
        assert entry["imports_network_processor"] is False
        assert entry["processor_family"].startswith("ipfs_datasets_py.")
        assert entry["capabilities"]
        assert entry["ppd_records"]


def test_fixture_validation_accepts_committed_fixture():
    assert validate_synthetic_processor_capability_fixture(_load_fixture()) == []


def test_fixture_records_ppd_handoff_records_for_each_capture_type():
    fixture = _load_fixture()
    by_capture_type = {
        entry["capture_type"]: set(entry["ppd_records"])
        for entry in fixture["capabilities"]
    }

    assert by_capture_type["html"] == {
        "SourceRegistry",
        "ArchiveManifest",
        "DocumentRecord",
    }
    assert by_capture_type["pdf"] == {
        "ArchiveManifest",
        "DocumentRecord",
        "RequirementNode",
    }
    assert by_capture_type["warc"] == {"ArchiveManifest"}
    assert by_capture_type["metadata"] == {"SourceRegistry", "ArchiveManifest"}
