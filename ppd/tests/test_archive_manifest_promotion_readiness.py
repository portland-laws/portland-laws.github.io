from __future__ import annotations

import pytest

from ppd.archive_manifest_promotion_readiness import (
    assert_promotion_readiness_packet,
    validate_promotion_readiness_packet,
)


def valid_packet() -> dict[str, object]:
    return {
        "manifest_id": "manifest-2026-05-29",
        "source_id": "portland-code-source",
        "known_manifest_ids": ["manifest-2026-05-29"],
        "known_source_ids": ["portland-code-source"],
        "evidence": {
            "checksum": {"algorithm": "sha256", "value": "0" * 64},
            "freshness": {"observed_at": "2026-05-29T00:00:00Z"},
        },
        "attestations": {"no_raw_body": True},
        "manifest_promotion_active": False,
        "promotion_enabled": False,
        "notes": "fixture-only readiness packet; no live processor execution requested",
    }


def issue_codes(packet: dict[str, object]) -> set[str]:
    return {issue.code for issue in validate_promotion_readiness_packet(packet)}


def test_accepts_minimal_safe_readiness_packet() -> None:
    packet = valid_packet()

    assert validate_promotion_readiness_packet(packet) == []
    assert_promotion_readiness_packet(packet)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda packet: packet["evidence"].pop("checksum"), "missing_checksum_evidence"),
        (lambda packet: packet["evidence"].pop("freshness"), "missing_freshness_evidence"),
        (lambda packet: packet.update({"raw_body_path": "ppd/tests/fixtures/raw/body.html"}), "raw_output_path_present"),
        (lambda packet: packet.update({"download_path": "ppd/tests/fixtures/downloads/code.pdf"}), "raw_output_path_present"),
        (lambda packet: packet.update({"archive_output_path": "ppd/tests/fixtures/archive-output/out.json"}), "raw_output_path_present"),
        (lambda packet: packet.update({"evidence_path": "/home/example/private/evidence.json"}), "private_local_path_present"),
        (lambda packet: packet.update({"claim": "processor executed live against production"}), "live_processor_execution_claim"),
        (lambda packet: packet.update({"manifest_id": "unknown-manifest"}), "unknown_manifest_id"),
        (lambda packet: packet.update({"source_id": "unknown-source"}), "unknown_source_id"),
        (lambda packet: packet.update({"attestations": {}}), "missing_no_raw_body_attestation"),
        (lambda packet: packet.update({"aborted": True}), "missing_abort_notes"),
        (lambda packet: packet.update({"manifest_promotion_active": True}), "active_manifest_promotion_flag"),
    ],
)
def test_rejects_unsafe_or_incomplete_readiness_packets(mutation, expected_code: str) -> None:
    packet = valid_packet()
    mutation(packet)

    assert expected_code in issue_codes(packet)


def test_abort_note_satisfies_aborted_packet_requirement() -> None:
    packet = valid_packet()
    packet.update({"aborted": True, "abort_note": "Fixture aborted before promotion; no live processor was run."})

    assert "missing_abort_notes" not in issue_codes(packet)


def test_assert_raises_with_issue_codes() -> None:
    packet = valid_packet()
    packet["promotion_enabled"] = True

    with pytest.raises(ValueError, match="active_manifest_promotion_flag"):
        assert_promotion_readiness_packet(packet)
