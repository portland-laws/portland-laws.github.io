from __future__ import annotations

import pytest

from ppd.validation.inactive_public_refresh_promotion_candidate_v1 import validate_candidate


def valid_candidate() -> dict:
    return {
        "candidate_version": "v1",
        "promotion_state": "inactive",
        "active": False,
        "reviewer_bundle_references": ["reviewer-bundle:v1:fixture"],
        "inactive_promotion_manifests": ["inactive-manifest:v1:fixture"],
        "reference_coverage": {
            "SourceRegistry": ["source-registry:v1:fixture"],
            "ArchiveManifest": ["archive-manifest:v1:fixture"],
            "DocumentRecord": ["document-record:v1:fixture"],
            "RequirementNode": ["requirement-node:v1:fixture"],
            "ProcessModel": ["process-model:v1:fixture"],
            "GuardrailBundle": ["guardrail-bundle:v1:fixture"],
            "agent-readiness": ["agent-readiness:v1:fixture"],
        },
        "promotion_preconditions": ["candidate remains inactive"],
        "reviewer_approvals": ["reviewer-a"],
        "rollback_checkpoints": ["checkpoint-a"],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
        "artifacts": [{"visibility": "public", "kind": "curated", "path": "ppd/tests/fixtures/public.json"}],
        "claims": ["deterministic fixture validation only"],
        "flags": {"writes_enabled": False, "live_crawl_enabled": False},
    }


def test_valid_candidate_has_no_errors() -> None:
    assert validate_candidate(valid_candidate()) == []


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("reviewer_bundle_references", "missing reviewer_bundle_references"),
        ("inactive_promotion_manifests", "missing inactive_promotion_manifests"),
        ("promotion_preconditions", "missing promotion_preconditions"),
        ("reviewer_approvals", "missing reviewer_approvals"),
        ("rollback_checkpoints", "missing rollback_checkpoints"),
        ("validation_commands", "missing validation_commands"),
    ],
)
def test_rejects_missing_required_lists(field: str, expected: str) -> None:
    candidate = valid_candidate()
    candidate[field] = []

    assert expected in validate_candidate(candidate)


@pytest.mark.parametrize(
    "reference_type",
    [
        "SourceRegistry",
        "ArchiveManifest",
        "DocumentRecord",
        "RequirementNode",
        "ProcessModel",
        "GuardrailBundle",
        "agent-readiness",
    ],
)
def test_rejects_missing_reference_coverage(reference_type: str) -> None:
    candidate = valid_candidate()
    candidate["reference_coverage"][reference_type] = []

    assert f"missing reference coverage for {reference_type}" in validate_candidate(candidate)


@pytest.mark.parametrize("artifact_value", ["private", "raw", "downloaded"])
def test_rejects_private_raw_or_downloaded_artifacts(artifact_value: str) -> None:
    candidate = valid_candidate()
    candidate["artifacts"] = [{"visibility": artifact_value, "path": "fixture"}]

    assert "artifact must not be private, raw, or downloaded" in validate_candidate(candidate)


@pytest.mark.parametrize(
    "claim",
    [
        "live crawl completed",
        "live extraction completed",
        "DevHub evidence captured",
        "active promotion is ready",
        "release activation is queued",
        "official action completed",
        "legal guarantee supplied",
        "permitting guarantee supplied",
    ],
)
def test_rejects_forbidden_claims(claim: str) -> None:
    candidate = valid_candidate()
    candidate["claims"] = [claim]

    assert any(error.startswith("forbidden claim:") for error in validate_candidate(candidate))


@pytest.mark.parametrize("flag", ["active_mutation", "writes_enabled", "live_crawl_enabled", "release_activation"])
def test_rejects_active_mutation_flags(flag: str) -> None:
    candidate = valid_candidate()
    candidate["flags"][flag] = True

    assert f"active mutation flag set: flags.{flag}" in validate_candidate(candidate)


def test_rejects_active_state() -> None:
    candidate = valid_candidate()
    candidate["promotion_state"] = "active"
    candidate["active"] = True

    errors = validate_candidate(candidate)

    assert "promotion state must be inactive" in errors
    assert "candidate must not be active" in errors
