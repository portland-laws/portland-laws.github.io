from __future__ import annotations

from ppd.logic.guardrail_regeneration_readiness import (
    GuardrailRegenerationReadinessError,
    assert_guardrail_regeneration_readiness,
    validate_guardrail_regeneration_readiness,
)


def valid_packet() -> dict[str, object]:
    return {
        "affected_requirement_ids": ["REQ-001"],
        "affected_predicate_ids": ["PRED-001"],
        "human_review_status": "reviewed",
        "source_evidence": [
            {
                "source_evidence_id": "EVID-001",
                "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
                "freshness_status": "fresh",
            }
        ],
        "refreshed_predicates": [
            {
                "predicate_id": "PRED-001",
                "source_evidence_ids": ["EVID-001"],
                "text": "Permit requests requiring plan review use an attended DevHub path.",
            }
        ],
        "cache_status": "current",
        "promotion_mode": "manual_review",
    }


def issue_codes(packet: dict[str, object]) -> set[str]:
    return {issue.code for issue in validate_guardrail_regeneration_readiness(packet).issues}


def test_accepts_reviewed_public_cited_packet() -> None:
    result = validate_guardrail_regeneration_readiness(valid_packet())

    assert result.ready is True
    assert result.issues == ()


def test_rejects_stale_source_evidence() -> None:
    packet = valid_packet()
    packet["source_evidence"] = [
        {
            "source_evidence_id": "EVID-001",
            "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
            "freshness_status": "stale",
        }
    ]

    assert "stale_source_evidence" in issue_codes(packet)


def test_rejects_missing_affected_ids() -> None:
    packet = valid_packet()
    packet["affected_requirement_ids"] = []
    packet["affected_predicate_ids"] = []

    codes = issue_codes(packet)

    assert "missing_affected_requirement_ids" in codes
    assert "missing_affected_predicate_ids" in codes


def test_rejects_uncited_refreshed_predicates() -> None:
    packet = valid_packet()
    packet["refreshed_predicates"] = [{"predicate_id": "PRED-001", "text": "No citations."}]

    assert "uncited_refreshed_predicate" in issue_codes(packet)


def test_rejects_private_or_authenticated_urls() -> None:
    packet = valid_packet()
    packet["source_evidence"] = [
        {
            "source_evidence_id": "EVID-001",
            "canonical_url": "https://devhub.portlandoregon.gov/account/my-permits?token=secret",
            "freshness_status": "fresh",
        }
    ]

    assert "private_or_authenticated_url" in issue_codes(packet)


def test_rejects_raw_body_fields() -> None:
    packet = valid_packet()
    packet["capture"] = {"raw_html": "raw body"}

    assert "raw_body_field" in issue_codes(packet)


def test_rejects_downloaded_document_paths() -> None:
    packet = valid_packet()
    packet["document"] = {"downloaded_document_path": "/tmp/downloads/fee-guide.pdf"}

    assert "downloaded_document_path" in issue_codes(packet)


def test_rejects_current_cache_status_before_review() -> None:
    packet = valid_packet()
    packet["human_review_status"] = "pending"
    packet["cache_status"] = "current"

    assert "current_cache_status_before_review" in issue_codes(packet)


def test_rejects_automatic_guardrail_promotion() -> None:
    packet = valid_packet()
    packet["automatic_guardrail_promotion"] = True

    assert "automatic_guardrail_promotion" in issue_codes(packet)


def test_assertion_helper_raises_with_issues() -> None:
    packet = valid_packet()
    packet["source_evidence"] = []
    packet["refreshed_predicates"] = [{"predicate_id": "PRED-001"}]

    try:
        assert_guardrail_regeneration_readiness(packet)
    except GuardrailRegenerationReadinessError as exc:
        assert exc.issues
    else:
        raise AssertionError("expected readiness assertion to fail")
