import json
from pathlib import Path

from ppd.devhub_attended_readonly_operator_transcript import (
    REQUIRED_ATTESTATIONS,
    build_operator_transcript_packet,
    validate_operator_transcript_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_attended_readonly_pilot"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_build_operator_transcript_packet_matches_committed_fixture() -> None:
    launch_readiness = _load_fixture("launch_readiness_packet.json")
    expected = _load_fixture("operator_transcript_packet.json")

    actual = build_operator_transcript_packet(launch_readiness)

    assert actual == expected


def test_operator_transcript_packet_has_ordered_simulated_observations_and_attestations() -> None:
    transcript = _load_fixture("operator_transcript_packet.json")

    validate_operator_transcript_packet(transcript)

    observations = transcript["ordered_operator_observations"]
    assert [observation["sequence"] for observation in observations] == list(
        range(1, len(observations) + 1)
    )
    assert {observation["kind"] for observation in observations} == {
        "manual_user_attendance_checkpoint",
        "redacted_page_state_summary",
        "selector_confidence_confirmation",
    }
    assert all(observation["simulated_only"] is True for observation in observations)
    assert transcript["prohibited_artifacts"] == {
        "browser_sessions": [],
        "auth_state_files": [],
        "screenshots": [],
        "traces": [],
        "raw_crawl_outputs": [],
        "downloaded_documents": [],
    }
    assert all(
        transcript["guardrail_attestations"][attestation] is True
        for attestation in REQUIRED_ATTESTATIONS
    )
