from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = "processor_handoff_dry_run_manifest_v7"
QUEUE_SCHEMA_VERSION = "public_source_recrawl_preflight_queue_v7"

FORBIDDEN_OPERATIONS = [
    "invoke_live_processors",
    "network_fetch",
    "download_raw_artifacts",
    "persist_raw_body",
    "open_devhub",
    "read_private_documents",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "make_legal_or_permitting_guarantees",
]

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/crawler/processor_handoff_manifest_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_processor_handoff_manifest_v7.py"],
]

RAW_BODY_KEYS = {
    "raw_body",
    "body",
    "html",
    "raw_html",
    "text",
    "raw_text",
    "pdf_bytes",
    "content",
    "document_bytes",
    "downloaded_path",
}


def load_public_source_recrawl_preflight_queue_v7(path: str | Path) -> dict[str, Any]:
    queue_path = Path(path)
    with queue_path.open("r", encoding="utf-8") as handle:
        queue = json.load(handle)

    if queue.get("schema_version") != QUEUE_SCHEMA_VERSION:
        raise ValueError(f"expected {QUEUE_SCHEMA_VERSION} queue fixture")

    entries = queue.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("queue fixture must include at least one entry")

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"queue entry {index} must be an object")
        _assert_no_raw_body_fields(entry, f"entries[{index}]")
        for required_key in ("source_id", "canonical_url", "source_type", "preflight_decision"):
            if not entry.get(required_key):
                raise ValueError(f"queue entry {index} missing {required_key}")
        if entry["preflight_decision"] not in {"handoff_ready", "skipped"}:
            raise ValueError(f"unsupported preflight decision for {entry['source_id']}")

    return queue


def build_processor_handoff_dry_run_manifest_v7(path: str | Path) -> dict[str, Any]:
    queue = load_public_source_recrawl_preflight_queue_v7(path)
    queue_path = Path(path)
    entries = queue["entries"]

    invocation_plans = []
    archive_manifest_placeholders = []
    normalized_document_reference_placeholders = []
    no_raw_body_persistence_assertions = []
    skipped_source_evidence_rows = []
    validation_handoff_rows = []

    for entry in entries:
        source_id = entry["source_id"]
        canonical_url = entry["canonical_url"]
        decision = entry["preflight_decision"]
        processor_name = entry.get("expected_processor") or _default_processor_name(entry)

        no_raw_body_persistence_assertions.append(
            {
                "assertion_id": f"no-raw-body-v7-{source_id}",
                "source_id": source_id,
                "passed": True,
                "evidence": "Queue fixture and dry-run manifest contain metadata and placeholders only.",
                "forbidden_fields_absent": sorted(RAW_BODY_KEYS),
                "raw_body_persisted": False,
            }
        )

        if decision == "skipped":
            skipped_source_evidence_rows.append(
                {
                    "source_id": source_id,
                    "canonical_url": canonical_url,
                    "skipped_reason": entry.get("skip_reason", "policy_preflight_skip"),
                    "policy_evidence": {
                        "allowlist_policy": entry.get("allowlist_policy"),
                        "robots_policy": entry.get("robots_policy"),
                        "processor_policy": entry.get("processor_policy"),
                    },
                }
            )
            validation_handoff_rows.append(
                {
                    "source_id": source_id,
                    "handoff_status": "skipped_with_evidence",
                    "validation_scope": "offline_fixture_review_only",
                }
            )
            continue

        invocation_plans.append(
            {
                "plan_id": f"processor-plan-v7-{source_id}",
                "source_id": source_id,
                "canonical_url": canonical_url,
                "mode": "dry_run_fixture_only",
                "processor_name": processor_name,
                "processor_version": "placeholder:offline-dry-run",
                "input_ref": f"fixture:{queue_path.as_posix()}#{source_id}",
                "arguments": {
                    "source_id": source_id,
                    "canonical_url": canonical_url,
                    "source_type": entry["source_type"],
                    "content_type": entry.get("content_type"),
                    "preflight_decision": decision,
                    "no_network": True,
                    "no_raw_download": True,
                    "no_devhub": True,
                },
                "forbidden_operations": list(FORBIDDEN_OPERATIONS),
            }
        )

        archive_manifest_placeholders.append(
            {
                "manifest_id": f"archive-placeholder-v7-{source_id}",
                "source_id": source_id,
                "canonical_url": canonical_url,
                "requested_url": canonical_url,
                "redirect_chain": [],
                "http_status": None,
                "content_type": entry.get("content_type"),
                "content_hash": f"placeholder:fixture-preflight-v7:{source_id}",
                "capture_started_at": None,
                "capture_finished_at": None,
                "processor_name": processor_name,
                "processor_version": "placeholder:offline-dry-run",
                "archive_artifact_ref": "placeholder:no-raw-artifact-persisted",
                "normalized_document_id": f"normalized-document-placeholder-v7-{source_id}",
                "skipped_reason": None,
                "no_raw_body_persisted": True,
            }
        )

        normalized_document_reference_placeholders.append(
            {
                "document_id": f"normalized-document-placeholder-v7-{source_id}",
                "source_id": source_id,
                "title": entry.get("title", "placeholder:title-from-processor"),
                "document_type": entry.get("document_type", _default_document_type(entry)),
                "language": "en",
                "sections": [],
                "tables": [],
                "links": [],
                "pdf_pages": [],
                "form_fields": [],
                "citation_spans": [],
                "content_hash": f"placeholder:fixture-preflight-v7:{source_id}",
                "extraction_confidence": "placeholder:not_extracted_in_dry_run",
            }
        )

        validation_handoff_rows.append(
            {
                "source_id": source_id,
                "handoff_status": "ready_for_offline_validation",
                "validation_scope": "fixture_processor_plan_contract_only",
                "required_command_ids": ["py_compile", "pytest_processor_handoff_manifest_v7"],
            }
        )

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "source_queue_schema_version": queue["schema_version"],
        "source_queue_fixture": queue_path.as_posix(),
        "generated_from_fixture_only": True,
        "network_invocation_permitted": False,
        "devhub_invocation_permitted": False,
        "raw_artifact_download_permitted": False,
        "legal_or_permitting_guarantees_made": False,
        "invocation_plans": invocation_plans,
        "archive_manifest_placeholders": archive_manifest_placeholders,
        "normalized_document_reference_placeholders": normalized_document_reference_placeholders,
        "no_raw_body_persistence_assertions": no_raw_body_persistence_assertions,
        "skipped_source_evidence_rows": skipped_source_evidence_rows,
        "validation_handoff_rows": validation_handoff_rows,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }
    _assert_no_raw_body_fields(manifest, "manifest")
    return manifest


def _default_processor_name(entry: dict[str, Any]) -> str:
    content_type = (entry.get("content_type") or "").lower()
    if "pdf" in content_type:
        return "ipfs_datasets_py.public_pdf_archive_processor"
    return "ipfs_datasets_py.public_html_archive_processor"


def _default_document_type(entry: dict[str, Any]) -> str:
    content_type = (entry.get("content_type") or "").lower()
    if "pdf" in content_type:
        return "public_pdf"
    return "public_html"


def _assert_no_raw_body_fields(value: Any, location: str) -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if key in RAW_BODY_KEYS:
                raise ValueError(f"raw body field {key!r} is not permitted at {location}")
            _assert_no_raw_body_fields(nested_value, f"{location}.{key}")
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            _assert_no_raw_body_fields(nested_value, f"{location}[{index}]")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build PP&D processor handoff dry-run manifest v7 from fixtures.")
    parser.add_argument("queue_fixture", type=Path)
    args = parser.parse_args()
    manifest = build_processor_handoff_dry_run_manifest_v7(args.queue_fixture)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
