from __future__ import annotations

from copy import deepcopy

from ppd.processor_handoff_validation import validate_processor_handoff_packet


def valid_packet() -> dict[str, object]:
    return {
        "dry_run": True,
        "policy_preflight_evidence": {
            "policy_id": "ppd-preflight-v1",
            "checked_at": "2026-05-28T00:00:00Z",
        },
        "processor_contract_id": "processor-contract-v1",
        "processor_contract_version": "2026.05-fixture",
        "rate_limit": {"max_requests": 3, "per_seconds": 60},
        "artifacts": [
            {
                "id": "ordinance-index",
                "kind": "metadata",
                "metadata_only": True,
                "source_url": "https://www.portland.gov/code/1",
                "normalized_document_ref": "normalized_documents/ordinance-index.json",
                "source_registry_id": "ppd-code-title-1",
            }
        ],
    }


def assert_rejected(packet: dict[str, object], expected: str) -> None:
    errors = validate_processor_handoff_packet(packet)
    assert any(expected in error for error in errors), errors


def test_accepts_metadata_only_bounded_dry_run_handoff_packet() -> None:
    assert validate_processor_handoff_packet(valid_packet()) == []


def test_rejects_missing_policy_preflight_evidence() -> None:
    packet = valid_packet()
    packet.pop("policy_preflight_evidence")
    assert_rejected(packet, "missing policy preflight evidence")


def test_rejects_missing_processor_contract_identifier() -> None:
    packet = valid_packet()
    packet["processor_contract_id"] = ""
    assert_rejected(packet, "missing processor contract identifier")


def test_rejects_missing_processor_contract_version() -> None:
    packet = valid_packet()
    packet["processor_contract_version"] = ""
    assert_rejected(packet, "missing processor contract version")


def test_rejects_live_network_flags() -> None:
    packet = valid_packet()
    packet["allow_live_network"] = True
    assert_rejected(packet, "live execution flag")


def test_rejects_live_execution_flags() -> None:
    packet = valid_packet()
    packet["execute_live"] = True
    assert_rejected(packet, "live execution flag")


def test_rejects_dry_run_disabled() -> None:
    packet = valid_packet()
    packet["dry_run"] = False
    assert_rejected(packet, "cannot disable dry-run mode")


def test_rejects_raw_archive_or_body_fields() -> None:
    packet = valid_packet()
    packet["raw_body"] = "raw response"
    assert_rejected(packet, "raw archive/body field")


def test_rejects_raw_archive_persistence() -> None:
    packet = valid_packet()
    packet["persistRawBody"] = True
    assert_rejected(packet, "raw archive persistence")


def test_rejects_local_downloaded_paths() -> None:
    packet = valid_packet()
    packet["downloaded_document_path"] = "/tmp/ppd/raw.pdf"
    assert_rejected(packet, "local downloaded document path")


def test_rejects_private_or_authenticated_urls() -> None:
    packet = valid_packet()
    packet["source_url"] = "https://user:secret@example.test/archive"
    assert_rejected(packet, "private or authenticated URL")


def test_rejects_private_network_urls() -> None:
    packet = valid_packet()
    packet["source_url"] = "http://127.0.0.1:8080/archive"
    assert_rejected(packet, "private or authenticated URL")


def test_rejects_unbounded_rate_limits() -> None:
    packet = valid_packet()
    packet["rate_limit"] = "unlimited"
    assert_rejected(packet, "missing bounded rate limit")


def test_rejects_artifacts_that_are_not_metadata_only() -> None:
    packet = valid_packet()
    packet["artifacts"] = [{"id": "raw-doc", "metadata_only": False}]
    assert_rejected(packet, "metadata-only")


def test_rejects_artifact_raw_payloads_even_when_marked_metadata_only() -> None:
    packet = valid_packet()
    packet["artifacts"] = [{"id": "raw-doc", "metadata_only": True, "body": "raw"}]
    assert_rejected(packet, "non-metadata field")


def test_rejects_unactionable_skip_reasons() -> None:
    packet = valid_packet()
    artifacts = deepcopy(packet["artifacts"])
    assert isinstance(artifacts, list)
    assert isinstance(artifacts[0], dict)
    artifacts[0]["status"] = "skipped"
    artifacts[0]["skip_reason"] = "unknown"
    packet["artifacts"] = artifacts
    assert_rejected(packet, "unactionable skip reason")


def test_accepts_actionable_skip_reasons() -> None:
    packet = valid_packet()
    artifacts = deepcopy(packet["artifacts"])
    assert isinstance(artifacts, list)
    assert isinstance(artifacts[0], dict)
    artifacts[0]["status"] = "skipped"
    artifacts[0]["skip_reason"] = "disallowed_by_robots"
    packet["artifacts"] = artifacts
    assert validate_processor_handoff_packet(packet) == []


def test_rejects_normalized_document_refs_without_source_registry_ids() -> None:
    packet = valid_packet()
    artifacts = deepcopy(packet["artifacts"])
    assert isinstance(artifacts, list)
    assert isinstance(artifacts[0], dict)
    artifacts[0].pop("source_registry_id")
    packet["artifacts"] = artifacts
    assert_rejected(packet, "normalized document reference requires source registry id")
