from __future__ import annotations

from datetime import date

import pytest

from ppd.guardrails.candidate_packet_validator import reject_candidate_packet, validate_candidate_packet


def _valid_packet() -> dict:
    return {
        "predicates": [
            {
                "id": "predicate-1",
                "text": "Permit status must come from the archived PP&D source.",
                "citations": [{"url": "https://www.portland.gov/ppd", "captured_at": "2026-05-20"}],
            }
        ],
        "input_models": [{"id": "model-1", "last_verified_at": "2026-05-20"}],
        "actions": [
            {
                "id": "submit-appeal",
                "type": "submission",
                "consequential": True,
                "refusal_rules": ["no-submission-without-human-review"],
                "exact_confirmation_required": True,
            }
        ],
        "promotion": {"target": "candidate"},
    }


def _valid_regenerated_requirement_packet() -> dict:
    packet = _valid_packet()
    packet.update(
        {
            "packet_type": "regenerated_requirement_candidate",
            "does_not_replace_active_bundle": True,
            "affected_process_ids": ["process-single-pdf-submission"],
            "affected_guardrail_bundle_ids": ["guardrail-bundle-single-pdf-active"],
            "reviewer_review": {"approved": True, "reviewer": "ppd-reviewer"},
            "requirement_diffs": [
                {
                    "old_requirement_id": "req-single-pdf-001",
                    "new_requirement_id": "req-single-pdf-001-r1",
                    "summary": "Regenerated requirement keeps supporting documents separate from drawings.",
                    "citations": [
                        {
                            "url": "https://www.portland.gov/ppd/get-permit/submit-plans-online",
                            "source_type": "public_html",
                            "privacy_classification": "public",
                            "captured_at": "2026-05-20",
                        }
                    ],
                }
            ],
        }
    )
    return packet


def _codes(packet: dict) -> set[str]:
    return {finding.code for finding in validate_candidate_packet(packet, today=date(2026, 5, 28))}


def test_valid_candidate_packet_has_no_findings() -> None:
    assert validate_candidate_packet(_valid_packet(), today=date(2026, 5, 28)) == []


def test_rejects_uncited_predicates() -> None:
    packet = _valid_packet()
    packet["predicates"] = [{"id": "predicate-1", "text": "A source-grounded claim without a source."}]

    assert "uncited_predicate" in _codes(packet)


def test_rejects_consequential_action_without_refusal_rules() -> None:
    packet = _valid_packet()
    packet["actions"][0].pop("refusal_rules")

    assert "missing_refusal_rule" in _codes(packet)


def test_rejects_consequential_action_without_exact_confirmation_gate() -> None:
    packet = _valid_packet()
    packet["actions"][0].pop("exact_confirmation_required")

    assert "missing_exact_confirmation_gate" in _codes(packet)


def test_rejects_private_values() -> None:
    packet = _valid_packet()
    packet["devhub_session_token"] = "Bearer abcdefghijklmnopqrstuvwxyz"

    assert "private_value" in _codes(packet)


def test_rejects_stale_input_models() -> None:
    packet = _valid_packet()
    packet["input_models"] = [{"id": "model-1", "last_verified_at": "2026-03-01"}]

    assert "stale_input_model" in _codes(packet)


def test_rejects_active_bundle_promotion_before_human_review() -> None:
    packet = _valid_packet()
    packet["promotion"] = {"target": "active_bundle"}

    assert "active_bundle_promotion_requires_review" in _codes(packet)


def test_allows_active_bundle_promotion_after_human_review() -> None:
    packet = _valid_packet()
    packet["promotion"] = {
        "target": "active_bundle",
        "human_review": {"approved": True, "reviewer": "ppd-reviewer"},
    }

    assert "active_bundle_promotion_requires_review" not in _codes(packet)


def test_reject_helper_raises_with_codes() -> None:
    packet = _valid_packet()
    packet["predicates"] = [{"id": "predicate-1"}]

    with pytest.raises(ValueError, match="uncited_predicate"):
        reject_candidate_packet(packet, today=date(2026, 5, 28))


def test_valid_regenerated_requirement_packet_has_no_findings() -> None:
    assert validate_candidate_packet(_valid_regenerated_requirement_packet(), today=date(2026, 5, 28)) == []


def test_regenerated_requirement_packet_rejects_uncited_diffs() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet["requirement_diffs"][0]["citations"] = []

    assert "uncited_requirement_diff" in _codes(packet)


def test_regenerated_requirement_packet_rejects_missing_old_and_new_ids() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet["requirement_diffs"][0].pop("old_requirement_id")
    packet["requirement_diffs"][0].pop("new_requirement_id")

    codes = _codes(packet)
    assert "missing_old_requirement_id" in codes
    assert "missing_new_requirement_id" in codes


def test_regenerated_requirement_packet_rejects_private_or_authenticated_evidence() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet["requirement_diffs"][0]["citations"] = [
        {
            "url": "https://devhub.portlandoregon.gov/account/permits/123",
            "source_type": "devhub_authenticated",
            "auth_scope": "authenticated",
            "privacy_classification": "private",
        }
    ]

    assert "private_or_authenticated_evidence" in _codes(packet)


def test_regenerated_requirement_packet_rejects_raw_body_download_and_archive_paths() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet["requirement_diffs"][0]["raw_body_path"] = "/tmp/ppd/raw/devhub-page.html"
    packet["requirement_diffs"][0]["download_path"] = "/home/user/downloads/source.pdf"
    packet["requirement_diffs"][0]["archive_path"] = "archive://public-crawl/source.warc.gz"

    assert "raw_artifact_reference" in _codes(packet)


def test_regenerated_requirement_packet_rejects_current_status_claims_without_reviewer_review() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet.pop("reviewer_review")
    packet["requirement_diffs"][0]["summary"] = "This is the current PP&D upload status."

    assert "current_status_claim_requires_reviewer_review" in _codes(packet)


def test_regenerated_requirement_packet_rejects_missing_affected_process_and_guardrail_links() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet["affected_process_ids"] = []
    packet["affected_guardrail_bundle_ids"] = []

    codes = _codes(packet)
    assert "missing_affected_process_links" in codes
    assert "missing_affected_guardrail_links" in codes


def test_regenerated_requirement_packet_rejects_active_bundle_mutation() -> None:
    packet = _valid_regenerated_requirement_packet()
    packet["does_not_replace_active_bundle"] = False
    packet["bundle_mutation"] = {"mutates_active_bundle": True, "target_bundle_status": "active"}

    assert "active_bundle_mutation" in _codes(packet)
