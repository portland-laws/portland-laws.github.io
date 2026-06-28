from __future__ import annotations

import pytest

from ppd.human_review_queue_validation import (
    assert_valid_human_review_queue_packet,
    validate_human_review_queue_packet,
)


def valid_packet() -> dict[str, object]:
    return {
        "packet_id": "fixture-001",
        "status": "needs_review",
        "packet_links": [{"label": "PP&D public permit search", "url": "https://www.portland.gov/ppd"}],
        "reviewer_prompts": ["Confirm whether the public source supports this packet summary."],
        "summary": "Public-source packet prepared for human review.",
    }


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ({"auth_token": "abc123"}, "private_value"),
        ({"notes": "Authorization: Bearer abc.def"}, "private_value"),
        ({"raw_html": "raw crawl output"}, "raw_or_authenticated_artifact"),
        ({"trace_path": "ppd/private/traces/run.zip"}, "raw_or_authenticated_artifact"),
        ({"downloaded_document_path": "ppd/downloads/permit.pdf"}, "downloaded_document_path"),
        ({"packet_links": []}, "missing_packet_links"),
        ({"reviewer_prompts": []}, "missing_reviewer_prompts"),
        ({"status": "production_ready"}, "unreviewed_production_ready_status"),
        ({"recommendation": "Submit the application in DevHub."}, "live_or_consequential_action_recommendation"),
    ],
)
def test_rejects_disallowed_human_review_packet_content(mutation: dict[str, object], code: str) -> None:
    packet = valid_packet()
    packet.update(mutation)

    issues = validate_human_review_queue_packet(packet)

    assert code in {issue.code for issue in issues}


def test_accepts_reviewed_production_ready_packet_without_private_or_live_action_content() -> None:
    packet = valid_packet()
    packet.update(
        {
            "status": "production_ready",
            "human_review": {"reviewed": True, "reviewed_by": "reviewer-fixture"},
            "recommendation": "Keep this packet in the reviewed archive.",
        }
    )

    assert validate_human_review_queue_packet(packet) == []
    assert_valid_human_review_queue_packet(packet)


def test_assert_valid_raises_with_issue_details() -> None:
    packet = valid_packet()
    packet["recommended_action"] = "Pay the permit fee."

    with pytest.raises(ValueError, match="live_or_consequential_action_recommendation"):
        assert_valid_human_review_queue_packet(packet)
