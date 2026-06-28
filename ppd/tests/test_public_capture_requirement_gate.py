from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ppd.validation.public_capture_requirement_gate import (
    RequirementGateError,
    require_public_capture_requirement_readiness,
    validate_public_capture_requirement_readiness,
)

NOW = datetime(2026, 5, 17, tzinfo=timezone.utc)


def ready_assembly() -> dict[str, object]:
    return {
        "citation_spans": [{"start": 12, "end": 34, "citation": "33.510.100"}],
        "section_order": ["33.510.100", "33.510.110"],
        "extraction_confidence": 0.91,
        "content_hash": "sha256:0123456789abcdef",
        "source_captured_at": "2026-05-01T00:00:00Z",
        "owning_surface": {"id": "portland-zoning-code", "kind": "code"},
    }


def issue_codes(assembly: dict[str, object]) -> list[str]:
    return [issue.code for issue in validate_public_capture_requirement_readiness(assembly, now=NOW)]


def test_ready_public_capture_assembly_passes_requirement_gate() -> None:
    require_public_capture_requirement_readiness(ready_assembly(), now=NOW)


def test_missing_required_provenance_blocks_requirement_extraction() -> None:
    assembly: dict[str, object] = {}

    assert issue_codes(assembly) == [
        "missing_citation_spans",
        "missing_or_invalid_section_order",
        "missing_extraction_confidence",
        "missing_content_hash",
        "missing_source_freshness",
        "missing_owning_surface",
    ]

    with pytest.raises(RequirementGateError) as excinfo:
        require_public_capture_requirement_readiness(assembly, now=NOW)

    assert "missing_citation_spans" in str(excinfo.value)


def test_stale_source_low_confidence_and_bad_surface_block_extraction() -> None:
    assembly = ready_assembly()
    assembly["source_captured_at"] = "2026-02-01T00:00:00Z"
    assembly["extraction_confidence"] = 0.5
    assembly["owning_surface"] = {"id": "portland-zoning-code"}

    assert issue_codes(assembly) == [
        "low_extraction_confidence",
        "stale_source_freshness",
        "missing_owning_surface",
    ]


def test_nested_normalized_metadata_paths_are_supported() -> None:
    assembly = {
        "citations": {"spans": [{"start": 0, "end": 5}]},
        "sections": {"order": [1, 2]},
        "requirements": {"extraction_confidence": "0.82"},
        "normalized": {"content_hash": "sha256:nested"},
        "source": {"captured_at": "2026-05-16T00:00:00+00:00"},
        "metadata": {"owning_surface": {"name": "Public Notices", "type": "capture"}},
    }

    assert issue_codes(assembly) == []
