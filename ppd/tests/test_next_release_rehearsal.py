from pathlib import Path

from ppd.next_release_rehearsal import build_rehearsal_packet, load_fixture_packet, packet_to_json


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "next_release_rehearsal" / "packet_v1.json"


def test_next_release_rehearsal_packet_categories_and_counts() -> None:
    fixture = load_fixture_packet(FIXTURE_PATH)
    packet = build_rehearsal_packet(fixture)

    recommendations = {item["candidate_id"]: item for item in packet["recommendations"]}

    assert packet["mode"] == "fixture-first-offline-rehearsal"
    assert packet["recommendation_counts"] == {
        "release-held": 1,
        "release-ready": 1,
        "release-rejected": 1,
    }
    assert recommendations["synthetic-freshness-requirements-ready"]["recommendation"] == "release-ready"
    assert recommendations["correction-upload-review-held"]["recommendation"] == "release-held"
    assert recommendations["payment-execution-rejected"]["recommendation"] == "release-rejected"


def test_rehearsal_packet_contains_required_review_material() -> None:
    packet = build_rehearsal_packet(load_fixture_packet(FIXTURE_PATH))

    for recommendation in packet["recommendations"]:
        assert recommendation["rollback_notes"]
        assert recommendation["reviewer_disposition"] in {
            "approve-for-next-release-review",
            "hold-for-review",
            "reject",
        }
        assert recommendation["dependency_order"]
        assert recommendation["offline_validation_commands"] == packet["offline_validation_commands"]

    assert packet["mutation_policy"] == {
        "release_promotion": "forbidden",
        "live_crawling": "forbidden",
        "devhub_access": "forbidden",
        "private_files": "forbidden",
        "uploads_submissions_certifications_payments_scheduling": "forbidden",
        "state_mutation": "forbidden",
    }


def test_rehearsal_packet_serializes_deterministically() -> None:
    packet = build_rehearsal_packet(load_fixture_packet(FIXTURE_PATH))
    rendered = packet_to_json(packet)

    assert rendered.endswith("\n")
    assert "next-release-integration-rehearsal-v1" in rendered
    assert "payment-execution-rejected" in rendered
    assert "release promotion was performed" in rendered
