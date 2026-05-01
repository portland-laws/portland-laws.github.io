#!/usr/bin/env python3
"""Deterministic PP&D workspace validation.

This command is intentionally fixture-only. It does not crawl public sites, open
DevHub, authenticate, submit, upload, pay, or read private session artifacts.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urlparse

ROOT = Path(__file__).resolve().parents[2]
PPD_ROOT = ROOT / "ppd"

PRIVATE_PATH_MARKERS = (
    "/data/private/",
    "/devhub/.auth/",
    "/devhub/traces/",
    "/devhub/screenshots/",
    "/devhub/downloads/",
    "auth-state",
    "storage-state",
    "session",
    "trace.zip",
    ".har",
)

REQUIRED_GITIGNORE_PATTERNS = (
    "/data/private/",
    "/data/raw/",
    "/devhub/.auth/",
    "/devhub/auth-state*.json",
    "/devhub/storage-state*.json",
    "/devhub/traces/",
    "/devhub/screenshots/",
    "/devhub/downloads/",
    "/daemon/status.json",
    "/daemon/progress.json",
    "/daemon/supervisor-status.json",
    "/daemon/supervisor-actions.jsonl",
    "/daemon/failed-patches/",
)

SOURCE_INDEX_STATUSES = {"fetched", "not_modified", "skipped", "failed"}
SOURCE_INDEX_PAGE_TYPES = {
    "guidance",
    "form_index",
    "faq",
    "portal_reference",
    "public_search_reference",
    "pdf",
    "other",
}
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def parse_utc_timestamp(value: Any, field: str, path: Path) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        fail(f"{path.relative_to(ROOT)} field {field} must be an ISO UTC timestamp ending in Z")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"{path.relative_to(ROOT)} field {field} is not a valid ISO timestamp: {exc}")


def require_https_url(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.startswith("https://"):
        fail(f"{path.relative_to(ROOT)} field {field} must be an HTTPS URL")
    parsed = urlparse(value)
    if not parsed.netloc:
        fail(f"{path.relative_to(ROOT)} field {field} must include a hostname")
    if urldefrag(value).fragment:
        fail(f"{path.relative_to(ROOT)} field {field} must not include a fragment")
    return value


def validate_fixture_files() -> None:
    fixture_root = PPD_ROOT / "tests"
    if not fixture_root.exists():
        fail("ppd/tests is required for curated PP&D fixtures")

    json_files = sorted(fixture_root.rglob("*.json")) + sorted((PPD_ROOT / "data" / "manifests").glob("*.json"))
    if not json_files:
        fail("expected at least one committed PP&D JSON fixture or manifest")

    for path in json_files:
        rel = f"/{path.relative_to(PPD_ROOT).as_posix()}"
        if any(marker in rel for marker in PRIVATE_PATH_MARKERS):
            fail(f"private or runtime artifact is inside fixture validation set: {path.relative_to(ROOT)}")
        data = load_json(path)
        if isinstance(data, dict):
            if "sourceUrl" in data and str(data["sourceUrl"]).startswith("http://"):
                fail(f"{path.relative_to(ROOT)} uses non-HTTPS sourceUrl")
            if "source_url" in data and str(data["source_url"]).startswith("http://"):
                fail(f"{path.relative_to(ROOT)} uses non-HTTPS source_url")


def validate_source_index_fixtures() -> None:
    fixture_path = PPD_ROOT / "tests" / "fixtures" / "source-index" / "source_index_records.json"
    if not fixture_path.exists():
        fail("source-index fixture is required at ppd/tests/fixtures/source-index/source_index_records.json")

    fixture = load_json(fixture_path)
    if fixture.get("fixtureKind") != "source_index_records":
        fail(f"{fixture_path.relative_to(ROOT)} fixtureKind must be source_index_records")
    if fixture.get("schemaVersion") != 1:
        fail(f"{fixture_path.relative_to(ROOT)} schemaVersion must be 1")
    parse_utc_timestamp(fixture.get("generatedAt"), "generatedAt", fixture_path)

    records = fixture.get("records")
    if not isinstance(records, list) or not records:
        fail(f"{fixture_path.relative_to(ROOT)} records must be a non-empty array")

    ids: set[str] = set()
    saw_redirect = False
    saw_hash = False
    saw_skipped = False
    saw_not_modified = False

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            fail(f"{fixture_path.relative_to(ROOT)} records[{index}] must be an object")
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            fail(f"{fixture_path.relative_to(ROOT)} records[{index}].id is required")
        if record_id in ids:
            fail(f"{fixture_path.relative_to(ROOT)} duplicate source-index id {record_id}")
        ids.add(record_id)

        source_url = require_https_url(record.get("sourceUrl"), f"records[{index}].sourceUrl", fixture_path)
        canonical_url = require_https_url(record.get("canonicalUrl"), f"records[{index}].canonicalUrl", fixture_path)
        if not isinstance(record.get("title"), str) or not record["title"].strip():
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} title is required")
        if not isinstance(record.get("bureau"), str) or not record["bureau"].strip():
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} bureau is required")
        if record.get("pageType") not in SOURCE_INDEX_PAGE_TYPES:
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} has invalid pageType")
        if not isinstance(record.get("contentType"), str) or "/" not in record["contentType"]:
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} contentType must be a MIME-like value")

        first_seen = parse_utc_timestamp(record.get("firstSeenAt"), f"record {record_id} firstSeenAt", fixture_path)
        last_seen = parse_utc_timestamp(record.get("lastSeenAt"), f"record {record_id} lastSeenAt", fixture_path)
        if last_seen < first_seen:
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} lastSeenAt must be after firstSeenAt")

        redirects = record.get("redirects")
        if not isinstance(redirects, list):
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} redirects must be an array")
        if redirects:
            saw_redirect = True
            expected_from = source_url
            for hop_index, hop in enumerate(redirects):
                if not isinstance(hop, dict):
                    fail(f"{fixture_path.relative_to(ROOT)} record {record_id} redirect {hop_index} must be an object")
                from_url = require_https_url(hop.get("fromUrl"), f"record {record_id} redirect {hop_index} fromUrl", fixture_path)
                to_url = require_https_url(hop.get("toUrl"), f"record {record_id} redirect {hop_index} toUrl", fixture_path)
                if from_url != expected_from:
                    fail(f"{fixture_path.relative_to(ROOT)} record {record_id} redirect chain is discontinuous")
                expected_from = to_url
                if hop.get("statusCode") not in REDIRECT_STATUS_CODES:
                    fail(f"{fixture_path.relative_to(ROOT)} record {record_id} redirect {hop_index} has invalid statusCode")
                observed_at = parse_utc_timestamp(hop.get("observedAt"), f"record {record_id} redirect {hop_index} observedAt", fixture_path)
                if observed_at < first_seen or observed_at > last_seen:
                    fail(f"{fixture_path.relative_to(ROOT)} record {record_id} redirect observedAt must be within first/last seen window")
            if expected_from != canonical_url:
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} redirect chain must end at canonicalUrl")
        elif source_url != canonical_url:
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} needs redirects when sourceUrl differs from canonicalUrl")

        crawl_status = record.get("crawlStatus")
        if crawl_status not in SOURCE_INDEX_STATUSES:
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} has invalid crawlStatus")

        fetched_at = record.get("fetchedAt")
        if fetched_at is not None:
            fetched_dt = parse_utc_timestamp(fetched_at, f"record {record_id} fetchedAt", fixture_path)
            if fetched_dt < first_seen or fetched_dt > last_seen:
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} fetchedAt must be within first/last seen window")

        content_hash = record.get("contentHash")
        if crawl_status in {"fetched", "not_modified"}:
            if fetched_at is None:
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} requires fetchedAt for crawlStatus {crawl_status}")
            if record.get("httpStatus") not in {200, 304}:
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} requires httpStatus 200 or 304")
            if not isinstance(content_hash, str) or not SHA256_RE.match(content_hash):
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} requires sha256 contentHash")
            saw_hash = True
        if crawl_status == "not_modified":
            saw_not_modified = True
            if record.get("httpStatus") != 304:
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} not_modified requires httpStatus 304")
        if crawl_status == "skipped":
            saw_skipped = True
            if not isinstance(record.get("skipReason"), str) or not record["skipReason"].strip():
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} skipped status requires skipReason")
            if content_hash is not None:
                fail(f"{fixture_path.relative_to(ROOT)} record {record_id} skipped status must not invent a contentHash")
        if crawl_status == "failed" and not isinstance(record.get("failureReason"), str):
            fail(f"{fixture_path.relative_to(ROOT)} record {record_id} failed status requires failureReason")

    if not saw_redirect:
        fail(f"{fixture_path.relative_to(ROOT)} must include at least one redirect-chain record")
    if not saw_hash:
        fail(f"{fixture_path.relative_to(ROOT)} must include at least one content-hash record")
    if not saw_not_modified:
        fail(f"{fixture_path.relative_to(ROOT)} must include at least one not_modified crawl status record")
    if not saw_skipped:
        fail(f"{fixture_path.relative_to(ROOT)} must include at least one skipped crawl status record")


def validate_contract_schemas() -> None:
    sys.path.insert(0, str(ROOT))

    from ppd.contracts.documents import NormalizedDocument, PpdContentType, PpdDocumentRole
    from ppd.contracts.processes import (
        ActionGate,
        ActionGateClassification,
        ActionGateKind,
        PermitProcess,
        ProcessStage,
        ProcessStageKind,
        RequiredDocument,
        RequiredDocumentKind,
        RequiredFact,
        RequiredFactKind,
    )
    from ppd.contracts.source_index import CrawlStatus, RedirectHop, SourceIndexRecord, SourcePageType

    document = NormalizedDocument(
        id="fixture-doc",
        source_url="https://www.portland.gov/ppd/example",
        canonical_url="https://www.portland.gov/ppd/example",
        content_type=PpdContentType.HTML,
        title="Fixture Document",
        fetched_at="2026-05-01T00:00:00Z",
        content_hash="sha256:fixture",
        text="Public PP&D fixture text.",
        document_role=PpdDocumentRole.GUIDANCE,
        normalized_at="2026-05-01T00:00:00Z",
        source_family="portland_gov_ppd",
    )
    document_errors = document.validate()
    if document_errors:
        fail(f"document contract fixture failed validation: {document_errors}")

    process = PermitProcess(
        id="fixture-process",
        name="Fixture Permit Process",
        permit_types=("fixture",),
        source_ids=("fixture-doc",),
        stages=(
            ProcessStage(
                id="prepare",
                name="Prepare documents",
                kind=ProcessStageKind.DOCUMENT_PREPARATION,
                sequence=0,
                next_stage_ids=("submit",),
            ),
            ProcessStage(
                id="submit",
                name="Submit request",
                kind=ProcessStageKind.SUBMISSION,
                sequence=1,
            ),
        ),
        required_facts=(
            RequiredFact(
                id="property-address",
                label="Property address",
                kind=RequiredFactKind.PROPERTY,
                required=True,
                source_stage_ids=("prepare",),
            ),
        ),
        required_documents=(
            RequiredDocument(
                id="application-pdf",
                name="Application PDF",
                kind=RequiredDocumentKind.APPLICATION_FORM,
                required=True,
                accepted_file_types=("application/pdf",),
                source_stage_ids=("prepare",),
            ),
        ),
        action_gates=(
            ActionGate(
                id="submit-application",
                name="Submit application",
                kind=ActionGateKind.SUBMISSION,
                classification=ActionGateClassification.POTENTIALLY_CONSEQUENTIAL,
                required_confirmation="User explicitly confirms this exact submission.",
                source_stage_ids=("submit",),
            ),
        ),
    )
    process_errors = process.validate()
    if process_errors:
        fail(f"process contract fixture failed validation: {process_errors}")

    source_index_record = SourceIndexRecord(
        id="fixture-source-index-record",
        source_url="https://www.portland.gov/bds/example",
        canonical_url="https://www.portland.gov/ppd/example",
        redirects=(
            RedirectHop(
                from_url="https://www.portland.gov/bds/example",
                to_url="https://www.portland.gov/ppd/example",
                status_code=301,
                observed_at="2026-05-01T00:00:00Z",
            ),
        ),
        title="Fixture Source Index Record",
        bureau="Portland Permitting & Development",
        page_type=SourcePageType.GUIDANCE,
        content_type="text/html",
        first_seen_at="2026-05-01T00:00:00Z",
        last_seen_at="2026-05-01T00:05:00Z",
        fetched_at="2026-05-01T00:05:00Z",
        http_status=200,
        content_hash="sha256:4444444444444444444444444444444444444444444444444444444444444444",
        crawl_status=CrawlStatus.FETCHED,
    )
    source_index_errors = source_index_record.validate()
    if source_index_errors:
        fail(f"source-index contract fixture failed validation: {source_index_errors}")


def validate_private_data_ignore_coverage() -> None:
    gitignore = PPD_ROOT / ".gitignore"
    if not gitignore.exists():
        fail("ppd/.gitignore is required")

    content = gitignore.read_text(encoding="utf-8")
    missing = [pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in content]
    if missing:
        fail(f"ppd/.gitignore is missing private/runtime patterns: {missing}")

    forbidden_committed_paths = [
        PPD_ROOT / "data" / "private",
        PPD_ROOT / "devhub" / ".auth",
        PPD_ROOT / "devhub" / "traces",
        PPD_ROOT / "devhub" / "screenshots",
        PPD_ROOT / "devhub" / "downloads",
    ]
    present = [path.relative_to(ROOT).as_posix() for path in forbidden_committed_paths if path.exists()]
    if present:
        fail(f"private/runtime artifact directories must not be present in the fixture workspace: {present}")


def validate_daemon_self_test() -> None:
    daemon = PPD_ROOT / "daemon" / "ppd_daemon.py"
    if not daemon.exists():
        fail("ppd/daemon/ppd_daemon.py is required")

    result = subprocess.run(
        [sys.executable, str(daemon), "--self-test"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail(
            "daemon self-test failed with exit code "
            f"{result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    supervisor = PPD_ROOT / "daemon" / "ppd_supervisor.py"
    if not supervisor.exists():
        fail("ppd/daemon/ppd_supervisor.py is required")

    supervisor_result = subprocess.run(
        [sys.executable, str(supervisor), "--self-test"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if supervisor_result.returncode != 0:
        fail(
            "supervisor self-test failed with exit code "
            f"{supervisor_result.returncode}\nSTDOUT:\n{supervisor_result.stdout}\nSTDERR:\n{supervisor_result.stderr}"
        )


def main() -> int:
    checks = (
        validate_fixture_files,
        validate_source_index_fixtures,
        validate_contract_schemas,
        validate_daemon_self_test,
        validate_private_data_ignore_coverage,
    )
    for check in checks:
        check()
    print("PP&D validation passed: fixtures, source index, schemas, daemon self-test, and ignore coverage are valid.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PP&D validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
