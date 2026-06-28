from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "archive_retention"

_ALLOWED_PUBLIC_FIELDS = {
    "archive_artifact_ref",
    "capture_finished_at",
    "capture_started_at",
    "canonical_url",
    "citation_spans",
    "content_hash",
    "content_type",
    "http_status",
    "manifest_id",
    "metadata",
    "no_raw_body_persisted",
    "normalized_document_id",
    "processor_name",
    "processor_version",
    "redirect_chain",
    "requested_url",
    "source_id",
}

_FORBIDDEN_KEY_PATTERNS = {
    "auth_state": re.compile(r"(^|_)(auth|storage)_?state($|_)", re.IGNORECASE),
    "credentials": re.compile(r"(credential|password|secret|token|cookie|session)", re.IGNORECASE),
    "har_data": re.compile(r"(^|_)(har|network_har)($|_)", re.IGNORECASE),
    "local_private_path": re.compile(r"(local_private_path|private_path|absolute_path|filesystem_path)", re.IGNORECASE),
    "private_devhub_value": re.compile(r"(private_devhub_value|account_value|private_field_value)", re.IGNORECASE),
    "raw_crawl_body": re.compile(r"(raw_body|raw_html|raw_text|response_body|body_bytes|crawl_body)", re.IGNORECASE),
    "screenshots": re.compile(r"(screenshot|screen_capture)", re.IGNORECASE),
    "traces": re.compile(r"(^|_)(trace|playwright_trace)($|_)", re.IGNORECASE),
}

_FORBIDDEN_VALUE_PATTERNS = {
    "auth_state": re.compile(r"\b(storageState|auth state|bearer [a-z0-9._-]+)\b", re.IGNORECASE),
    "har_data": re.compile(r"\.har\b|\bHAR archive\b", re.IGNORECASE),
    "local_private_path": re.compile(r"\b(/home/|/Users/|C:\\\\Users\\\\|file://)", re.IGNORECASE),
    "screenshots": re.compile(r"\.(png|jpg|jpeg|webp)\b.*\bscreenshot\b", re.IGNORECASE),
    "traces": re.compile(r"\btrace\.zip\b|\bplaywright trace\b", re.IGNORECASE),
}


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _walk_json(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    visited = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            visited.extend(_walk_json(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            visited.extend(_walk_json(child, (*path, str(index))))
    return visited


def _classify_manifest_retention_violations(manifest: dict[str, Any]) -> dict[str, list[str]]:
    violations: dict[str, list[str]] = {}
    for path, value in _walk_json(manifest):
        if path:
            key = path[-1]
            for label, pattern in _FORBIDDEN_KEY_PATTERNS.items():
                if pattern.search(key):
                    violations.setdefault(label, []).append(".".join(path))
        if isinstance(value, str):
            for label, pattern in _FORBIDDEN_VALUE_PATTERNS.items():
                if pattern.search(value):
                    violations.setdefault(label, []).append(".".join(path) or "$")
    return violations


def _assert_manifest_is_commit_safe(manifest: dict[str, Any]) -> None:
    violations = _classify_manifest_retention_violations(manifest)
    if violations:
        details = ", ".join(
            f"{label}: {sorted(paths)}" for label, paths in sorted(violations.items())
        )
        raise AssertionError(f"manifest includes non-committable archive artifacts: {details}")


@pytest.mark.parametrize(
    "field",
    sorted(_ALLOWED_PUBLIC_FIELDS),
)
def test_public_processor_manifest_fixture_exposes_commit_safe_fields(field: str) -> None:
    manifest = _load_fixture("public_processor_manifest_allowed.json")

    _assert_manifest_is_commit_safe(manifest)

    assert field in manifest


def test_public_processor_manifest_fixture_keeps_expected_public_archive_values() -> None:
    manifest = _load_fixture("public_processor_manifest_allowed.json")

    _assert_manifest_is_commit_safe(manifest)

    assert manifest["no_raw_body_persisted"] is True
    assert manifest["content_hash"].startswith("sha256:")
    assert manifest["normalized_document_id"] == "ppd-doc-devhub-faqs-2026-05-08"
    assert manifest["citation_spans"] == [
        {
            "source_id": "ppd-devhub-faqs",
            "normalized_document_id": "ppd-doc-devhub-faqs-2026-05-08",
            "section": "Services available in DevHub",
            "start_char": 128,
            "end_char": 214,
            "content_hash": "sha256:2a3f7f9d2bc9d8e482a28dc0e38b7d69e75c403ab9b52dbef6fdf12ad3b42e0d",
        }
    ]


def test_committed_manifest_policy_rejects_private_archive_artifacts() -> None:
    manifest = _load_fixture("public_processor_manifest_rejected_leaky.json")

    violations = _classify_manifest_retention_violations(manifest)

    assert set(violations) == {
        "auth_state",
        "credentials",
        "har_data",
        "local_private_path",
        "private_devhub_value",
        "raw_crawl_body",
        "screenshots",
        "traces",
    }
    with pytest.raises(AssertionError, match="non-committable archive artifacts"):
        _assert_manifest_is_commit_safe(manifest)
