from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from ppd.crawler.processor_handoff_dry_run_manifest_v7 import (
    ProcessorHandoffDryRunManifestV7Error,
    require_processor_handoff_dry_run_manifest_v7,
    validate_processor_handoff_dry_run_manifest_v7,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "processor_handoff_dry_run_manifest_v7"


def load_valid_manifest() -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / "valid_manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ("recrawl_preflight_refs", "missing recrawl preflight references"),
        ("processor_invocation_plans", "missing processor invocation plans"),
        ("archive_manifest_placeholders", "missing archive manifest placeholders"),
        ("normalized_document_reference_placeholders", "missing normalized document reference placeholders"),
        ("no_raw_body_persistence_assertions", "missing no-raw-body persistence assertions"),
        ("skipped_source_evidence_rows", "missing skipped-source evidence rows"),
        ("validation_handoff_rows", "missing validation handoff rows"),
        ("validation_commands", "missing validation commands"),
    ],
)
def test_manifest_v7_rejects_missing_required_sections(key: str, message: str) -> None:
    manifest = load_valid_manifest()
    manifest.pop(key)

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert message in result.errors


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"live_processor_execution_claims": ["completed"]}, "rejects live processor or crawl execution claims"),
        ({"claims": ["A live processor was executed for this manifest."]}, "rejects live processor or crawl execution claims"),
        ({"claims": ["A live crawl was completed for this manifest."]}, "rejects live processor or crawl execution claims"),
        ({"downloaded_artifacts": ["crawl-output.html"]}, "rejects downloaded or raw crawl artifacts"),
        ({"raw_crawl_artifacts": ["body.html"]}, "rejects downloaded or raw crawl artifacts"),
        ({"session_state": "state.json"}, "rejects private/session/auth artifacts"),
        ({"auth_artifacts": ["cookies.json"]}, "rejects private/session/auth artifacts"),
        ({"claims": ["Official action was completed in DevHub."]}, "rejects official-action completion claims"),
        ({"claims": ["This includes a permitting guarantee."]}, "rejects legal or permitting guarantees"),
        ({"active_mutation_flags": {"enabled": True}}, "rejects active mutation flags"),
        ({"mutation_enabled": True}, "rejects active mutation flags"),
    ],
)
def test_manifest_v7_rejects_forbidden_claims_and_artifacts(patch: dict[str, object], message: str) -> None:
    manifest = load_valid_manifest()
    manifest.update(patch)

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert message in result.errors


def test_manifest_v7_rejects_processor_plan_that_allows_invocation() -> None:
    manifest = load_valid_manifest()
    manifest["processor_invocation_plans"][0]["processor_invocation_allowed"] = True

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert "processor_invocation_plans[0].processor_invocation_allowed must be false" in result.errors


def test_manifest_v7_rejects_archive_placeholder_that_persists_artifact() -> None:
    manifest = load_valid_manifest()
    manifest["archive_manifest_placeholders"][0]["artifact_persisted"] = True

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert "archive_manifest_placeholders[0].artifact_persisted must be false" in result.errors


def test_manifest_v7_rejects_normalized_placeholder_that_persists_content() -> None:
    manifest = load_valid_manifest()
    manifest["normalized_document_reference_placeholders"][0]["document_content_persisted"] = True

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert "normalized_document_reference_placeholders[0].document_content_persisted must be false" in result.errors


def test_manifest_v7_rejects_missing_no_raw_body_assertion() -> None:
    manifest = load_valid_manifest()
    manifest["no_raw_body_persistence_assertions"][0] = copy.deepcopy(manifest["no_raw_body_persistence_assertions"][0])
    manifest["no_raw_body_persistence_assertions"][0]["no_raw_body_persisted"] = False

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert "no_raw_body_persistence_assertions[0].no_raw_body_persisted must be true" in result.errors


def test_manifest_v7_rejects_malformed_validation_command() -> None:
    manifest = load_valid_manifest()
    manifest["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]

    result = validate_processor_handoff_dry_run_manifest_v7(manifest)

    assert not result.valid
    assert "validation_commands[0] must be an argv list" in result.errors


def test_manifest_v7_accepts_complete_fixture_only_manifest() -> None:
    result = validate_processor_handoff_dry_run_manifest_v7(load_valid_manifest())

    assert result.valid
    assert result.errors == ()


def test_manifest_v7_require_raises_with_actionable_errors() -> None:
    manifest = load_valid_manifest()
    manifest["live_crawl_execution_claims"] = ["completed"]

    with pytest.raises(ProcessorHandoffDryRunManifestV7Error) as exc_info:
        require_processor_handoff_dry_run_manifest_v7(manifest)

    assert "rejects live processor or crawl execution claims" in str(exc_info.value)
