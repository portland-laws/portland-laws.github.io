from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ppd.crawler.fake_public_capture import (
    FakeCaptureError,
    FakePublicCaptureTransport,
    load_fixture_intentions,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_capture" / "approved_intentions.json"


def test_fake_public_capture_transport_builds_archive_manifest_metadata() -> None:
    intentions = load_fixture_intentions(FIXTURE_PATH)
    transport = FakePublicCaptureTransport(
        capture_started_at="2026-05-15T06:03:00Z",
        capture_finished_at="2026-05-15T06:03:01Z",
    )

    manifests = transport.capture_many(intentions)

    assert len(manifests) == 2
    first = manifests[0]
    expected_hash = "sha256:%s" % hashlib.sha256(
        intentions[0]["synthetic_body"].encode("utf-8")
    ).hexdigest()

    assert first["manifest_id"].startswith("archive-manifest:fake:")
    assert first["source_id"] == "ppd-devhub-faqs"
    assert first["requested_url"] == "http://www.portland.gov/ppd/devhub-faqs"
    assert first["canonical_url"] == "https://www.portland.gov/ppd/devhub-faqs"
    assert first["redirect_chain"] == [
        {
            "url": "http://www.portland.gov/ppd/devhub-faqs",
            "status": 301,
            "location": "https://www.portland.gov/ppd/devhub-faqs",
        },
        {"url": "https://www.portland.gov/ppd/devhub-faqs", "status": 200},
    ]
    assert first["http_status"] == 200
    assert first["content_type"] == "text/html; charset=utf-8"
    assert first["mime_type"] == "text/html; charset=utf-8"
    assert first["content_hash"] == expected_hash
    assert first["capture_started_at"] == "2026-05-15T06:03:00Z"
    assert first["capture_finished_at"] == "2026-05-15T06:03:01Z"
    assert first["processor_name"] == "ppd.fake_public_capture"
    assert first["processor_version"] == "0.1"
    assert first["processor_metadata"] == {
        "transport": "fake_public_capture",
        "network_requests_made": 0,
        "raw_body_persisted": False,
    }
    assert first["archive_artifact_ref"] == "metadata-only:fixture:ppd-devhub-faqs"
    assert first["normalized_document_id"] == "document:fixture:ppd-devhub-faqs"
    assert first["skipped_reason"] is None
    assert first["no_raw_body_persisted"] is True
    assert "synthetic_body" not in first


def test_fake_public_capture_respects_explicit_content_hash_without_raw_body() -> None:
    intentions = load_fixture_intentions(FIXTURE_PATH)
    manifest = FakePublicCaptureTransport().capture(intentions[1])

    assert manifest["source_id"] == "ppd-spp-file-naming-standards"
    assert manifest["content_type"] == "application/pdf"
    assert manifest["content_hash"] == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert manifest["redirect_chain"] == [
        {
            "url": "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
            "status": 200,
        }
    ]
    assert manifest["processor_metadata"]["network_requests_made"] == 0
    assert manifest["no_raw_body_persisted"] is True
    assert "synthetic_body" not in manifest


def test_fake_public_capture_rejects_unapproved_or_live_intentions() -> None:
    base_intention = {
        "source_id": "ppd-unapproved",
        "requested_url": "https://www.portland.gov/ppd/unapproved",
        "synthetic": True,
        "approval": {"status": "denied"},
        "http_status": 200,
        "mime_type": "text/html",
        "synthetic_body": "fixture",
    }

    transport = FakePublicCaptureTransport()

    with pytest.raises(FakeCaptureError, match="approved synthetic"):
        transport.capture(base_intention)

    live_intention = dict(base_intention)
    live_intention["synthetic"] = False
    live_intention["approval"] = {"status": "approved"}

    with pytest.raises(FakeCaptureError, match="synthetic crawl"):
        transport.capture(live_intention)
