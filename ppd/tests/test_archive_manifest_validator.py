from __future__ import annotations

import json
from pathlib import Path

from ppd.archive.manifest_validator import validate_archive_manifest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "archive_manifests"


def _valid_manifest() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "valid_public_manifest.json").read_text(encoding="utf-8"))


def _codes(manifest: dict[str, object]) -> set[str]:
    return {issue.code for issue in validate_archive_manifest(manifest)}


def test_valid_public_manifest_passes_policy_checks() -> None:
    assert validate_archive_manifest(_valid_manifest()) == []


def test_rejects_raw_body_persistence_and_raw_body_fields() -> None:
    manifest = _valid_manifest()
    manifest["no_raw_body_persisted"] = False
    manifest["raw_body"] = "raw response body"

    assert {"raw_body_persistence_not_denied", "raw_body_persisted"}.issubset(_codes(manifest))


def test_rejects_private_or_authenticated_devhub_urls() -> None:
    manifest = _valid_manifest()
    manifest["canonical_url"] = "https://devhub.portlandoregon.gov/permits/12345?sessionid=secret"
    manifest["requested_url"] = "https://devhub.portlandoregon.gov/"
    manifest["redirect_chain"] = [
        "https://devhub.portlandoregon.gov/signin",
        {"url": "https://www.portland.gov/ppd/devhub-faqs"},
    ]

    assert "private_devhub_url" in _codes(manifest)


def test_public_devhub_root_url_is_allowed() -> None:
    manifest = _valid_manifest()
    manifest["canonical_url"] = "https://devhub.portlandoregon.gov/"
    manifest["requested_url"] = "https://devhub.portlandoregon.gov/"

    assert validate_archive_manifest(manifest) == []


def test_rejects_missing_processor_metadata() -> None:
    manifest = _valid_manifest()
    manifest["processor_name"] = ""
    manifest.pop("processor_version")

    assert "missing_processor_metadata" in _codes(manifest)


def test_rejects_missing_source_id() -> None:
    manifest = _valid_manifest()
    manifest["source_id"] = " "

    assert "missing_source_id" in _codes(manifest)


def test_rejects_invented_hashes_for_skipped_captures() -> None:
    manifest = _valid_manifest()
    manifest["http_status"] = None
    manifest["skipped_reason"] = "disallowed by robots or policy"
    manifest["content_hash"] = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

    assert "invented_hash_for_skipped_capture" in _codes(manifest)


def test_skipped_capture_without_hash_is_allowed_when_metadata_is_present() -> None:
    manifest = _valid_manifest()
    manifest["http_status"] = None
    manifest["skipped_reason"] = "private/authenticated"
    manifest["content_hash"] = None
    manifest["archive_artifact_ref"] = None
    manifest["normalized_document_id"] = None

    assert validate_archive_manifest(manifest) == []
