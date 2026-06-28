from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ppd.requirement_candidate_set_v6 import (
    build_candidate_set_from_fixture,
    expected_offline_validation_commands,
    validate_candidate_set,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_candidate_set_v6"
WORK_PACKET_FIXTURE = FIXTURE_DIR / "requirement_reextraction_work_packet_v6.json"


def _packet() -> dict:
    return build_candidate_set_from_fixture(WORK_PACKET_FIXTURE)


def _payload() -> dict:
    return json.loads(WORK_PACKET_FIXTURE.read_text(encoding="utf-8"))


def test_builds_fixture_first_reextracted_requirement_candidate_set_v6() -> None:
    packet = _packet()

    assert packet["packet_type"] == "fixture_first_reextracted_requirement_candidate_set_v6"
    assert packet["version"] == 6
    assert packet["fixture_only"] is True
    assert packet["consumes_only"] == {"requirement_reextraction_work_packet_v6_fixtures": True}
    assert packet["work_packet_refs"][0]["fixture_role"] == "requirement_reextraction_work_packet_v6"
    assert packet["work_packet_refs"][0]["packet_id"] == "requirement-reextraction-work-packet-v6"
    assert packet["source_fixture_refs"][0] == packet["work_packet_refs"][0]
    assert all(value is False for value in packet["live_access"].values())


def test_enumerates_candidate_deltas_unchanged_rows_evidence_and_hints() -> None:
    packet = _packet()

    assert [row["requirement_id"] for row in packet["candidate_requirement_node_deltas"]] == [
        "req-plan-review-upload-separate-pdfs"
    ]
    assert {row["requirement_id"] for row in packet["unchanged_requirement_rows"]} == {
        "req-plan-review-devhub-before-submit",
        "req-trade-license-profile-check",
    }
    assert {row["source_id"] for row in packet["source_evidence_refs"]} == {
        "src-ppd-apply-permits-fixture",
        "src-ppd-single-pdf-fixture",
        "src-ppd-online-tools-fixture",
    }
    for row in packet["candidate_requirement_node_deltas"] + packet["unchanged_requirement_rows"]:
        assert row["source_evidence_ids"]
        assert row["confidence"] == "pending_reviewer_assignment"
        assert row["human_review_status"] in {"held_for_human_review", "pending_human_review"}
        assert row["formalization_deferred"] is True
        assert row["formalization_status"] == "deferred_until_human_review"
        assert row["superseded_citation_note"].startswith("Potentially supersedes prior citation")
    delta = packet["candidate_requirement_node_deltas"][0]
    assert delta["source_evidence_ids"] == ["evidence-single-pdf-separate-documents"]
    assert delta["human_review_status"] == "held_for_human_review"
    assert packet["downstream_process_model_impact_hints"][0]["activation_allowed"] is False


def test_keeps_exact_offline_validation_commands_only() -> None:
    packet = _packet()

    assert packet["offline_validation_commands"] == expected_offline_validation_commands()
    assert packet["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/requirement_candidate_set_v6.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_requirement_candidate_set_v6.py"],
        ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ]
    validate_candidate_set(packet)


def test_rejects_wrong_source_packet_and_non_fixture_mode(tmp_path: Path) -> None:
    payload = _payload()
    payload["packet_id"] = "other-packet"
    fixture = tmp_path / "bad.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="requirement re-extraction work packet v6"):
        build_candidate_set_from_fixture(fixture)

    payload = _payload()
    payload["fixture_only"] = False
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="fixture-only"):
        build_candidate_set_from_fixture(fixture)


def test_rejects_live_fetch_raw_body_and_guardrail_activation(tmp_path: Path) -> None:
    cases = []

    raw_body = _payload()
    raw_body["process_packets"][0]["extraction_inputs"][0]["raw_body_ref"] = "raw/page.html"
    cases.append((raw_body, "raw bodies"))

    live_fetch = _payload()
    live_fetch["process_packets"][0]["source_span_refresh_targets"][0]["requires_live_fetch"] = True
    cases.append((live_fetch, "live fetch"))

    activated = _payload()
    activated["process_packets"][0]["inactive_guardrail_status"] = "activated"
    cases.append((activated, "inactive guardrails unchanged"))

    live_access = _payload()
    live_access["live_access"]["open_devhub"] = True
    cases.append((live_access, "live or consequential access"))

    missing_evidence = _payload()
    missing_evidence["process_packets"][0]["source_span_refresh_targets"] = []
    cases.append((missing_evidence, "source_span_refresh_targets"))

    for index, (payload, match) in enumerate(cases):
        fixture = tmp_path / f"bad-{index}.json"
        fixture.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match=match):
            build_candidate_set_from_fixture(fixture)


def test_candidate_set_validator_rejects_missing_sections_and_commands() -> None:
    for key, match in (
        ("work_packet_refs", "work_packet_refs"),
        ("source_fixture_refs", "source_fixture_refs"),
        ("candidate_requirement_node_deltas", "candidate_requirement_node_deltas"),
        ("unchanged_requirement_rows", "unchanged_requirement_rows"),
        ("source_evidence_refs", "source_evidence_refs"),
        ("confidence_placeholder", "confidence placeholder"),
        ("human_review_status_placeholder", "human review status placeholder"),
        ("formalization_deferred", "formalization"),
        ("superseded_citation_notes", "superseded_citation_notes"),
        ("downstream_process_model_impact_hints", "downstream_process_model_impact_hints"),
        ("offline_validation_commands", "offline validation commands"),
    ):
        packet = _packet()
        del packet[key]
        with pytest.raises(ValueError, match=match):
            validate_candidate_set(packet)


def test_candidate_set_validator_rejects_missing_row_review_evidence_and_deferred_fields() -> None:
    row_cases = (
        ("candidate_requirement_node_deltas", "source_evidence_ids", "source_evidence_ids"),
        ("candidate_requirement_node_deltas", "confidence", "confidence"),
        ("candidate_requirement_node_deltas", "human_review_status", "human_review_status"),
        ("candidate_requirement_node_deltas", "formalization_deferred", "formalization"),
        ("candidate_requirement_node_deltas", "superseded_citation_note", "superseded_citation_note"),
        ("unchanged_requirement_rows", "source_evidence_ids", "source_evidence_ids"),
        ("unchanged_requirement_rows", "confidence", "confidence"),
        ("unchanged_requirement_rows", "human_review_status", "human_review_status"),
        ("unchanged_requirement_rows", "formalization_deferred", "formalization"),
        ("unchanged_requirement_rows", "superseded_citation_note", "superseded_citation_note"),
    )
    for section, key, match in row_cases:
        packet = _packet()
        del packet[section][0][key]
        with pytest.raises(ValueError, match=match):
            validate_candidate_set(packet)

    packet = _packet()
    packet["source_evidence_refs"][0]["requires_live_fetch"] = True
    with pytest.raises(ValueError, match="live fetch"):
        validate_candidate_set(packet)

    packet = _packet()
    packet["downstream_process_model_impact_hints"][0]["activation_allowed"] = True
    with pytest.raises(ValueError, match="must not activate"):
        validate_candidate_set(packet)


def test_candidate_set_validator_rejects_prohibited_claims_artifacts_guarantees_and_mutation_flags() -> None:
    unsafe_cases = (
        ({"active_mutation": True}, "prohibited"),
        ({"active_process_model_mutation": True}, "prohibited"),
        ({"auth_state": "storage-state.json"}, "prohibited"),
        ({"session_artifact": "private-session.json"}, "prohibited"),
        ({"downloaded_document": "permit.pdf"}, "prohibited"),
        ({"raw_body": ""}, "prohibited"),
        ({"raw_crawl_artifact": "crawl.warc"}, "prohibited"),
        ({"official_action_completed": True}, "prohibited"),
        ({"notes": "live crawl execution completed"}, "prohibited"),
        ({"notes": "permit approval guaranteed"}, "prohibited"),
        ({"notes": "submitted the application"}, "prohibited"),
    )
    for unsafe_payload, match in unsafe_cases:
        packet = _packet()
        packet["candidate_requirement_node_deltas"][0].update(deepcopy(unsafe_payload))
        with pytest.raises(ValueError, match=match):
            validate_candidate_set(packet)
