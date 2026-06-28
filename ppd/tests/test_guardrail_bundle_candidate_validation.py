from ppd.logic.guardrail_bundle_candidate_validation import validate_guardrail_bundle_update_candidate


def finding_codes(packet):
    findings = validate_guardrail_bundle_update_candidate(
        packet,
        known_requirement_ids={"REQ-1"},
        known_process_ids={"PROC-1"},
        known_guardrail_ids={"GB-1", "GR-1"},
    )
    return {finding["code"] for finding in findings}


def base_packet():
    return {
        "process_id": "PROC-1",
        "guardrail_bundle_id": "GB-1",
        "known_requirement_ids": ["REQ-1"],
        "known_process_ids": ["PROC-1"],
        "known_guardrail_ids": ["GB-1", "GR-1"],
        "rollback_notes": "Restore GB-1 from the last accepted bundle artifact.",
        "reviewer_owners": ["ppd-guardrail-review"],
        "changes": [
            {
                "type": "predicate_update",
                "requirement_id": "REQ-1",
                "guardrail_id": "GR-1",
                "source_evidence_ids": ["SRC-1#p1"],
            }
        ],
        "evidence": [
            {
                "source_evidence_id": "SRC-1#p1",
                "current": True,
                "freshness_status": "current",
                "privacy_classification": "public",
            }
        ],
        "enabled_actions": [{"name": "save draft", "classification": "reversible", "enabled": True}],
        "guardrail_mutation_active": False,
    }


def test_accepts_minimal_cited_reviewed_candidate_packet():
    assert validate_guardrail_bundle_update_candidate(
        base_packet(),
        known_requirement_ids={"REQ-1"},
        known_process_ids={"PROC-1"},
        known_guardrail_ids={"GB-1", "GR-1"},
    ) == []


def test_rejects_uncited_predicate_and_explanation_changes():
    packet = base_packet()
    packet["changes"] = [
        {"type": "predicate_update", "requirement_id": "REQ-1"},
        {"type": "explanation_template_update", "explanation": "Updated text."},
    ]

    assert "uncited_guardrail_change" in finding_codes(packet)


def test_rejects_unknown_requirement_process_and_guardrail_ids():
    packet = base_packet()
    packet["process_id"] = "PROC-404"
    packet["guardrail_bundle_id"] = "GB-404"
    packet["changes"][0]["requirement_id"] = "REQ-404"

    codes = finding_codes(packet)

    assert "unknown_requirement_id" in codes
    assert "unknown_process_id" in codes
    assert "unknown_guardrail_id" in codes


def test_rejects_stale_current_evidence_without_acknowledgement():
    packet = base_packet()
    packet["evidence"][0]["freshness_status"] = "stale"

    assert "stale_current_evidence_unacknowledged" in finding_codes(packet)


def test_allows_stale_current_evidence_with_acknowledgement():
    packet = base_packet()
    packet["evidence"][0]["freshness_status"] = "stale"
    packet["evidence"][0]["stale_current_acknowledged"] = True

    assert "stale_current_evidence_unacknowledged" not in finding_codes(packet)


def test_rejects_private_case_facts_and_private_classifications():
    packet = base_packet()
    packet["private_case_facts"] = {"permit_number": "private value"}
    packet["evidence"][0]["privacy_classification"] = "case_private"

    assert "private_case_facts" in finding_codes(packet)


def test_rejects_live_compiler_or_consumer_execution_claims():
    packet = base_packet()
    packet["validation_notes"] = "This was accepted because the live compiler executed successfully."

    assert "live_execution_claim" in finding_codes(packet)


def test_rejects_legal_or_permitting_outcome_guarantees():
    packet = base_packet()
    packet["explanation"] = "Using this guardrail guarantees the permit will be approved."

    assert "outcome_guarantee" in finding_codes(packet)


def test_rejects_enabled_consequential_actions():
    packet = base_packet()
    packet["enabled_actions"] = [{"name": "submit permit request", "classification": "consequential", "enabled": True}]

    assert "enabled_consequential_action" in finding_codes(packet)


def test_rejects_missing_rollback_notes_and_reviewer_owners():
    packet = base_packet()
    packet["rollback_notes"] = ""
    packet["reviewer_owners"] = []

    codes = finding_codes(packet)

    assert "missing_rollback_notes" in codes
    assert "missing_reviewer_owners" in codes


def test_rejects_active_guardrail_mutation_flags():
    packet = base_packet()
    packet["mutation_flags"] = {"guardrail_mutation_active": True}

    assert "active_guardrail_mutation_flag" in finding_codes(packet)
