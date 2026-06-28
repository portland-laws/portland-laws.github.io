from __future__ import annotations

import pytest

from ppd.validators.processor_handoff_manifest import (
    assert_valid_processor_handoff_manifest,
    validate_processor_handoff_manifest,
)


def valid_manifest() -> dict[str, object]:
    return {
        "processor_policy": "rehearsal-only deterministic processor handoff",
        "version_notes": "fixture schema v1; no live execution",
        "source_ids": ["ppd_rehearsal_fixture"],
        "output_paths": ["ppd/tests/fixtures/processor_handoff/rehearsal_manifest.json"],
        "attestations": {"no_raw_body": True},
        "abort_conditions": ["stop if a live processor would be required"],
        "artifact_policy": {"writes_artifacts": False},
    }


def test_accepts_valid_rehearsal_manifest() -> None:
    assert validate_processor_handoff_manifest(valid_manifest()) == []
    assert_valid_processor_handoff_manifest(valid_manifest())


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("processor_policy", "", "missing processor_policy"),
        ("version_notes", "", "missing version_notes"),
        ("source_ids", ["unreviewed_source"], "non-allowlisted source_id"),
        ("output_paths", ["ppd/tests/fixtures/raw_body.json"], "raw/download/archive output path"),
        ("output_paths", ["/home/alex/private/out.json"], "private local path"),
        ("live_processor_execution", True, "live processor execution claim"),
        ("attestations", {}, "missing no-raw-body attestation"),
        ("abort_conditions", [], "missing abort_conditions"),
        ("active_artifact_mutation", True, "active artifact mutation flag"),
    ],
)
def test_rejects_unsafe_manifest_shapes(field: str, value: object, expected: str) -> None:
    manifest = valid_manifest()
    manifest[field] = value
    errors = validate_processor_handoff_manifest(manifest)
    assert any(expected in error for error in errors)


def test_rejects_nested_active_artifact_mutation_flag() -> None:
    manifest = valid_manifest()
    manifest["artifact_policy"] = {"mutate_artifacts": True}
    errors = validate_processor_handoff_manifest(manifest)
    assert any("artifact_policy.mutate_artifacts" in error for error in errors)


def test_assert_valid_raises_with_compact_error_message() -> None:
    manifest = valid_manifest()
    manifest["source_ids"] = ["not_allowlisted"]
    with pytest.raises(ValueError, match="non-allowlisted source_id"):
        assert_valid_processor_handoff_manifest(manifest)
