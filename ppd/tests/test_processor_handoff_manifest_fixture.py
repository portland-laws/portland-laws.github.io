import json
import re
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "processor_handoff"
    / "synthetic_public_capture_manifest.json"
)

FORBIDDEN_RAW_KEYS = {
    "raw_body",
    "body",
    "html",
    "pdf_bytes",
    "downloaded_document",
    "screenshot",
    "trace",
    "har",
    "cookies",
    "auth_state",
    "credentials",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_processor_handoff_fixture_records_required_public_metadata():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["fixture_scope"] == "synthetic_public_captures_only"
    assert fixture["captures"]

    for capture in fixture["captures"]:
        assert capture["capture_kind"] == "synthetic_public_capture"
        assert capture["no_raw_body_persisted"] is True

        preflight = capture["policy_preflight"]
        assert preflight["policy_name"] == "ppd_public_source_preflight"
        assert preflight["allowed"] is True
        assert preflight["auth_scope"] == "public"
        assert preflight["raw_body_policy"] == "do_not_persist_raw_body"

        processor = capture["processor"]
        assert processor["name"]
        assert processor["version"]

        redirect_metadata = capture["redirect_metadata"]
        assert redirect_metadata["final_url"].startswith("https://www.portland.gov/ppd/")
        assert isinstance(redirect_metadata["redirect_chain"], list)
        assert redirect_metadata["redirect_count"] == len(redirect_metadata["redirect_chain"])

        response_metadata = capture["response_metadata"]
        assert response_metadata["mime_type"] in {
            "text/html; charset=utf-8",
            "application/pdf",
        }

        content_hash = capture["content_hash"]
        assert content_hash["algorithm"] == "sha256"
        assert SHA256_RE.match(content_hash["value"])

        normalized = capture["normalized_document_reference"]
        assert normalized["document_id"].startswith("doc-synthetic-ppd-public-")
        assert normalized["source_id"] == capture["source_id"]
        assert normalized["normalized_ref"].startswith("ppd://documents/synthetic/")
        assert normalized["content_hash"] == f"sha256:{content_hash['value']}"


def test_processor_handoff_fixture_does_not_persist_raw_or_private_artifacts():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for item in _walk(fixture):
        assert FORBIDDEN_RAW_KEYS.isdisjoint(item.keys())
