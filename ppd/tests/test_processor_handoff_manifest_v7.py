from __future__ import annotations

from pathlib import Path

import pytest

from ppd.crawler.processor_handoff_manifest_v7 import (
    FORBIDDEN_OPERATIONS,
    MANIFEST_SCHEMA_VERSION,
    build_processor_handoff_dry_run_manifest_v7,
    load_public_source_recrawl_preflight_queue_v7,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_recrawl_preflight_queue_v7.json"


def test_loads_public_source_recrawl_preflight_queue_v7_fixture() -> None:
    queue = load_public_source_recrawl_preflight_queue_v7(FIXTURE_PATH)

    assert queue["schema_version"] == "public_source_recrawl_preflight_queue_v7"
    assert [entry["source_id"] for entry in queue["entries"]] == [
        "ppd-online-tools-overview",
        "ppd-fee-payment-guide-download",
        "devhub-private-application-placeholder",
        "external-example-skip",
    ]


def test_builds_fixture_first_processor_handoff_dry_run_manifest_v7() -> None:
    manifest = build_processor_handoff_dry_run_manifest_v7(FIXTURE_PATH)

    assert manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["generated_from_fixture_only"] is True
    assert manifest["network_invocation_permitted"] is False
    assert manifest["devhub_invocation_permitted"] is False
    assert manifest["raw_artifact_download_permitted"] is False
    assert manifest["legal_or_permitting_guarantees_made"] is False
    assert manifest["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/crawler/processor_handoff_manifest_v7.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_processor_handoff_manifest_v7.py"],
    ]

    assert len(manifest["invocation_plans"]) == 2
    assert len(manifest["archive_manifest_placeholders"]) == 2
    assert len(manifest["normalized_document_reference_placeholders"]) == 2
    assert len(manifest["no_raw_body_persistence_assertions"]) == 4
    assert len(manifest["skipped_source_evidence_rows"]) == 2
    assert len(manifest["validation_handoff_rows"]) == 4


def test_invocation_plans_are_offline_and_forbid_consequential_actions() -> None:
    manifest = build_processor_handoff_dry_run_manifest_v7(FIXTURE_PATH)

    for plan in manifest["invocation_plans"]:
        assert plan["mode"] == "dry_run_fixture_only"
        assert plan["input_ref"].startswith("fixture:")
        assert plan["arguments"]["no_network"] is True
        assert plan["arguments"]["no_raw_download"] is True
        assert plan["arguments"]["no_devhub"] is True
        assert plan["forbidden_operations"] == FORBIDDEN_OPERATIONS
        assert "invoke_live_processors" in plan["forbidden_operations"]
        assert "pay" in plan["forbidden_operations"]
        assert "submit" in plan["forbidden_operations"]
        assert "make_legal_or_permitting_guarantees" in plan["forbidden_operations"]


def test_placeholders_assert_no_raw_body_persistence() -> None:
    manifest = build_processor_handoff_dry_run_manifest_v7(FIXTURE_PATH)

    for placeholder in manifest["archive_manifest_placeholders"]:
        assert placeholder["archive_artifact_ref"] == "placeholder:no-raw-artifact-persisted"
        assert placeholder["no_raw_body_persisted"] is True
        assert placeholder["http_status"] is None
        assert placeholder["capture_started_at"] is None
        assert placeholder["capture_finished_at"] is None
        assert placeholder["content_hash"].startswith("placeholder:fixture-preflight-v7:")

    for assertion in manifest["no_raw_body_persistence_assertions"]:
        assert assertion["passed"] is True
        assert assertion["raw_body_persisted"] is False


def test_skipped_sources_have_policy_evidence_rows() -> None:
    manifest = build_processor_handoff_dry_run_manifest_v7(FIXTURE_PATH)
    rows = {row["source_id"]: row for row in manifest["skipped_source_evidence_rows"]}

    assert rows["devhub-private-application-placeholder"]["skipped_reason"] == "private_authenticated_devhub_path"
    assert rows["external-example-skip"]["skipped_reason"] == "outside_allowlist"
    assert rows["devhub-private-application-placeholder"]["policy_evidence"]["allowlist_policy"] == "blocked_authenticated_surface"


def test_rejects_raw_body_fields_in_queue_fixture(tmp_path: Path) -> None:
    bad_fixture = tmp_path / "bad_queue.json"
    bad_fixture.write_text(
        """
        {
          "schema_version": "public_source_recrawl_preflight_queue_v7",
          "entries": [
            {
              "source_id": "bad-source",
              "canonical_url": "https://www.portland.gov/ppd",
              "source_type": "public_html",
              "preflight_decision": "handoff_ready",
              "raw_body": "not allowed"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="raw body field"):
        load_public_source_recrawl_preflight_queue_v7(bad_fixture)
