from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ppd.extraction.requirement_node_candidate_set_v8 import (
    assert_valid_requirement_node_candidate_set_v8,
    validate_requirement_node_candidate_set_v8,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_node_candidate_set_v8"


def _valid_candidate_set() -> dict:
    with (_FIXTURE_DIR / "valid_candidate_set.json").open(encoding="utf-8") as fixture:
        return json.load(fixture)


def _messages(candidate_set: dict) -> tuple[str, ...]:
    return validate_requirement_node_candidate_set_v8(candidate_set).messages()


def test_valid_candidate_set_fixture_passes() -> None:
    candidate_set = _valid_candidate_set()

    result = validate_requirement_node_candidate_set_v8(candidate_set)

    assert result.valid is True
    assert result.findings == ()
    assert_valid_requirement_node_candidate_set_v8(candidate_set)


def test_rejects_missing_work_packet_references() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set.pop("work_packet_ref")
    candidate_set["rows"][0].pop("work_packet_ref")

    messages = _messages(candidate_set)

    assert any("work_packet_ref" in message for message in messages)
    assert any("rows[0].work_packet_ref" in message for message in messages)


def test_rejects_missing_source_evidence_ids() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["source_evidence_catalog"][0].pop("evidence_id")
    candidate_set["rows"][0]["source_evidence_ids"] = []
    candidate_set["rows"][1]["source_evidence_ids"] = ["evidence:missing"]

    messages = _messages(candidate_set)

    assert any("source_evidence_catalog[0].evidence_id" in message for message in messages)
    assert any("rows[0].source_evidence_ids" in message for message in messages)
    assert any("must reference source_evidence_catalog" in message for message in messages)


def test_rejects_missing_required_requirement_type_coverage() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["required_requirement_type_coverage"].append("fee_trigger")

    messages = _messages(candidate_set)

    assert any("required_requirement_type_coverage" in message and "fee_trigger" in message for message in messages)


def test_rejects_missing_confidence_values() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["rows"][0].pop("confidence")

    messages = _messages(candidate_set)

    assert any("rows[0].confidence" in message for message in messages)


def test_rejects_missing_formalization_placeholders() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["rows"][0].pop("formalization_status")

    messages = _messages(candidate_set)

    assert any("rows[0].formalization_status" in message for message in messages)


def test_rejects_missing_reviewer_status_placeholders() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["rows"][0]["human_review_status"] = "approved"

    messages = _messages(candidate_set)

    assert any("rows[0].human_review_status" in message for message in messages)


def test_rejects_missing_superseded_requirement_references() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["rows"][3].pop("superseded_requirement_refs")

    messages = _messages(candidate_set)

    assert any("rows[3].superseded_requirement_refs" in message for message in messages)


def test_rejects_missing_validation_commands() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["validation_commands"] = []

    messages = _messages(candidate_set)

    assert any("validation_commands" in message for message in messages)


def test_rejects_live_crawl_execution_claims() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["notes"] = "Live crawl executed for this candidate set."

    messages = _messages(candidate_set)

    assert any("live crawl execution" in message for message in messages)


def test_rejects_downloaded_or_raw_crawl_artifacts() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["raw_html"] = "raw crawl artifact"

    messages = _messages(candidate_set)

    assert any("raw crawl" in message or "artifact" in message for message in messages)


def test_rejects_private_session_or_auth_artifacts() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["storage_state"] = {"cookies": [{"name": "session", "value": "secret"}]}

    messages = _messages(candidate_set)

    assert any("private, session, or auth" in message for message in messages)


def test_rejects_official_action_completion_claims() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["completion_claim"] = "Permit submitted through DevHub."

    messages = _messages(candidate_set)

    assert any("official-action completion" in message for message in messages)


def test_rejects_legal_or_permitting_guarantees() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["guarantee"] = "Approval guaranteed after this extraction."

    messages = _messages(candidate_set)

    assert any("legal or permitting guarantees" in message for message in messages)


def test_rejects_active_mutation_flags() -> None:
    candidate_set = _valid_candidate_set()
    candidate_set["mutation_enabled"] = True

    messages = _messages(candidate_set)

    assert any("active mutation flags" in message for message in messages)


def test_allows_explicitly_inactive_mutation_flags() -> None:
    candidate_set = _valid_candidate_set()
    for inactive_value in (False, None, "disabled", "inactive", "no"):
        candidate = deepcopy(candidate_set)
        candidate["active_mutation_flags"] = inactive_value
        assert validate_requirement_node_candidate_set_v8(candidate).valid is True
