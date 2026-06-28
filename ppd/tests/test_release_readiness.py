from __future__ import annotations

import json
from pathlib import Path

from ppd.release_readiness import (
    assert_release_readiness_snapshot,
    load_release_readiness_snapshot,
    validate_release_readiness_snapshot,
)


FIXTURES = Path(__file__).parent / "fixtures" / "release_readiness"


def test_valid_release_readiness_snapshot_passes() -> None:
    snapshot = load_release_readiness_snapshot(FIXTURES / "valid_snapshot.json")

    result = validate_release_readiness_snapshot(snapshot)

    assert result.ok, result.messages()
    assert_release_readiness_snapshot(snapshot)


def test_rejects_missing_prerequisite_packet_links() -> None:
    snapshot = {
        "prerequisite_packets": [
            {"name": "source registry without a link"},
        ],
        "readiness_claims": [
            {"claim": "safe claim", "citations": ["source-1"]},
        ],
    }

    result = validate_release_readiness_snapshot(snapshot)

    assert "missing_prerequisite_packet_link" in _codes(result)


def test_rejects_uncited_readiness_claims() -> None:
    snapshot = {
        "prerequisite_packets": [
            {"name": "packet", "link": "ppd/tests/fixtures/release_readiness/packet.json"},
        ],
        "readiness_claims": [
            {"claim": "The release is ready without evidence."},
            "Plain text claims cannot carry citations.",
        ],
    }

    result = validate_release_readiness_snapshot(snapshot)

    assert _codes(result).count("uncited_readiness_claim") == 2


def test_rejects_private_session_artifacts_and_raw_crawl_references() -> None:
    snapshot = {
        "prerequisite_packets": [
            {"name": "packet", "link": "ppd/tests/fixtures/release_readiness/packet.json"},
        ],
        "readiness_claims": [
            {"claim": "safe claim", "citations": ["source-1"]},
        ],
        "artifacts": [
            "ppd/local/devhub/auth_state.json",
            "ppd/local/crawl_output/raw_html/page.html",
        ],
    }

    result = validate_release_readiness_snapshot(snapshot)

    assert "private_or_session_artifact" in _codes(result)
    assert "raw_crawl_output_reference" in _codes(result)


def test_rejects_production_ready_label_with_unresolved_blockers() -> None:
    snapshot = {
        "release_status": "production-ready",
        "prerequisite_packets": [
            {"name": "packet", "link": "ppd/tests/fixtures/release_readiness/packet.json"},
        ],
        "readiness_claims": [
            {"claim": "safe claim", "citations": ["source-1"]},
        ],
        "unresolved_blockers": ["DevHub attended handoff review is incomplete"],
    }

    result = validate_release_readiness_snapshot(snapshot)

    assert "production_ready_with_unresolved_blockers" in _codes(result)


def test_rejects_enabled_consequential_paths() -> None:
    snapshot = {
        "prerequisite_packets": [
            {"name": "packet", "link": "ppd/tests/fixtures/release_readiness/packet.json"},
        ],
        "readiness_claims": [
            {"claim": "safe claim", "citations": ["source-1"]},
        ],
        "paths": {
            "live_crawl": {"enabled": True},
            "devhub": {"status": "enabled"},
            "payment": {"enabled": True},
            "upload": {"enabled": True},
            "submission": {"enabled": True},
            "scheduling": {"enabled": True},
            "cancellation": {"enabled": True},
            "certification": {"enabled": True},
        },
    }

    result = validate_release_readiness_snapshot(snapshot)

    codes = _codes(result)
    assert codes.count("enabled_consequential_path") == 8


def test_fixture_is_valid_json() -> None:
    with (FIXTURES / "valid_snapshot.json").open("r", encoding="utf-8") as handle:
        assert isinstance(json.load(handle), dict)


def _codes(result) -> list[str]:
    return [error.code for error in result.errors]
