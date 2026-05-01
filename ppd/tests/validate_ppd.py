#!/usr/bin/env python3
"""Deterministic PP&D workspace validation.

This command is intentionally fixture-only. It does not crawl public sites, open
DevHub, authenticate, submit, upload, pay, or read private session artifacts.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


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
        validate_contract_schemas,
        validate_daemon_self_test,
        validate_private_data_ignore_coverage,
    )
    for check in checks:
        check()
    print("PP&D validation passed: fixtures, schemas, daemon self-test, and ignore coverage are valid.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PP&D validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
