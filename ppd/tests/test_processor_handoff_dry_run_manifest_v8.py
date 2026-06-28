from __future__ import annotations

import copy

import pytest

from ppd.crawler.processor_handoff_dry_run_manifest_v8 import (
    ProcessorHandoffDryRunManifestV8Error,
    require_processor_handoff_dry_run_manifest_v8,
    validate_processor_handoff_dry_run_manifest_v8,
)


def valid_manifest() -> dict[str, object]:
    return {
        "manifest_version": "v8",
        "manifest_type": "ppd_processor_handoff_dry_run_manifest",
        "preflight_queue_references": [
            {
                "queue_ref": "fixture:ppd/tests/fixtures/processor_handoff/preflight_queue_v8.json",
                "queue_schema_version": "public_recrawl_preflight_queue_v8",
                "fixture_only": True,
            }
        ],
        "planned_processor_invocation_rows": [
            {
                "source_id": "ppd-public-guide",
                "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
                "processor_name": "ipfs_datasets_py.public_html_archive_processor",
                "processor_version": "placeholder:offline-dry-run",
                "dry_run": True,
                "processor_invocation_allowed": False,
                "network_allowed": False,
                "metadata_only": True,
            }
        ],
        "response_metadata_placeholders": [
            {
                "source_id": "ppd-public-guide",
                "placeholder_only": True,
                "http_status": None,
                "content_type": "text/html",
                "redirect_chain": [],
            }
        ],
        "content_hash_placeholders": [
            {
                "source_id": "ppd-public-guide",
                "placeholder_only": True,
                "content_hash": "placeholder:dry-run-v8:ppd-public-guide",
            }
        ],
        "normalized_document_reference_placeholders": [
            {
                "source_id": "ppd-public-guide",
                "normalized_document_id": "normalized-document-placeholder-v8-ppd-public-guide",
                "placeholder_only": True,
                "document_content_persisted": False,
            }
        ],
        "no_raw_body_persistence_assertions": [
            {
                "source_id": "ppd-public-guide",
                "no_raw_body_persisted": True,
                "persist_raw_body": False,
                "download_documents": False,
            }
        ],
        "skipped_source_rows": [
            {
                "source_id": "outside-allowlist-example",
                "skipped_reason": "outside_allowlist",
                "processor_invocation_allowed": False,
            }
        ],
        "validation_commands": [
            ["python3", "-m", "py_compile", "ppd/crawler/processor_handoff_dry_run_manifest_v8.py"],
            ["python3", "-m", "pytest", "ppd/tests/test_processor_handoff_dry_run_manifest_v8.py"],
        ],
        "live_processor_execution_allowed": False,
        "live_crawl_execution_allowed": False,
        "raw_artifact_download_allowed": False,
        "official_action_allowed": False,
        "legal_or_permitting_guarantees_made": False,
        "mutation_enabled": False,
    }


def test_valid_manifest_passes() -> None:
    manifest = valid_manifest()

    result = validate_processor_handoff_dry_run_manifest_v8(manifest)

    assert result.valid is True
    assert result.errors == ()
    assert require_processor_handoff_dry_run_manifest_v8(manifest) is manifest


@pytest.mark.parametrize(
    ("section", "message"),
    [
        ("preflight_queue_references", "missing preflight queue references"),
        ("planned_processor_invocation_rows", "missing planned processor invocation rows"),
        ("response_metadata_placeholders", "missing response metadata placeholders"),
        ("content_hash_placeholders", "missing content hash placeholders"),
        ("normalized_document_reference_placeholders", "missing normalized document reference placeholders"),
        ("no_raw_body_persistence_assertions", "missing no-raw-body persistence assertions"),
        ("skipped_source_rows", "missing skipped source rows"),
        ("validation_commands", "missing validation commands"),
    ],
)
def test_manifest_v8_rejects_missing_required_sections(section: str, message: str) -> None:
    manifest = valid_manifest()
    manifest.pop(section)

    result = validate_processor_handoff_dry_run_manifest_v8(manifest)

    assert result.valid is False
    assert message in result.errors


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("live_processor_execution", True, "rejects live processor execution claims"),
        ("processor_executed", True, "rejects live processor execution claims"),
        ("live_crawl_execution", True, "rejects live crawl execution claims"),
        ("crawl_executed", True, "rejects live crawl execution claims"),
        ("downloaded_artifact", "ppd/tests/fixtures/downloaded/artifact.html", "rejects downloaded or raw crawl artifacts"),
        ("raw_body", "raw page", "rejects downloaded or raw crawl artifacts"),
        ("session_state", "state.json", "rejects private/session/auth artifacts"),
        ("auth_artifact", "auth.json", "rejects private/session/auth artifacts"),
        ("official_action_completion", True, "rejects official-action completion claims"),
        ("legal_guarantee", "approval is guaranteed", "rejects legal or permitting guarantees"),
        ("permit_guarantee", True, "rejects legal or permitting guarantees"),
        ("active_mutation", True, "rejects active mutation flags"),
    ],
)
def test_manifest_v8_rejects_forbidden_claim_keys(field: str, value: object, message: str) -> None:
    manifest = valid_manifest()
    manifest[field] = value

    result = validate_processor_handoff_dry_run_manifest_v8(manifest)

    assert result.valid is False
    assert message in result.errors


def test_manifest_v8_rejects_nested_forbidden_claims() -> None:
    manifest = valid_manifest()
    manifest["operator_notes"] = {
        "processor": "processor was executed",
        "crawl": "live crawl was run",
        "official": "official action was completed",
        "mutation": "mutation is active",
    }

    result = validate_processor_handoff_dry_run_manifest_v8(manifest)

    assert result.valid is False
    assert "rejects live processor execution claims" in result.errors
    assert "rejects live crawl execution claims" in result.errors
    assert "rejects official-action completion claims" in result.errors
    assert "rejects active mutation flags" in result.errors


def test_manifest_v8_rejects_private_and_raw_paths() -> None:
    manifest = valid_manifest()
    manifest["artifact"] = {
        "path": "/home/alex/private/session.json",
        "artifact_path": "ppd/tests/fixtures/raw_crawl/page.html",
    }

    result = validate_processor_handoff_dry_run_manifest_v8(manifest)

    assert result.valid is False
    assert "rejects private/session/auth artifacts" in result.errors
    assert "rejects downloaded or raw crawl artifacts" in result.errors


def test_manifest_v8_rejects_bad_row_contracts() -> None:
    manifest = valid_manifest()
    broken = copy.deepcopy(manifest)
    assert isinstance(broken["planned_processor_invocation_rows"], list)
    assert isinstance(broken["content_hash_placeholders"], list)
    broken["planned_processor_invocation_rows"][0]["network_allowed"] = True
    broken["content_hash_placeholders"][0]["content_hash"] = "sha256:real-capture"

    result = validate_processor_handoff_dry_run_manifest_v8(broken)

    assert result.valid is False
    assert "planned_processor_invocation_rows[0].network_allowed must be false" in result.errors
    assert "content_hash_placeholders[0].content_hash must be a placeholder" in result.errors


def test_manifest_v8_require_raises_with_errors() -> None:
    manifest = valid_manifest()
    manifest["live_processor_execution"] = True

    with pytest.raises(ProcessorHandoffDryRunManifestV8Error, match="live processor"):
        require_processor_handoff_dry_run_manifest_v8(manifest)
