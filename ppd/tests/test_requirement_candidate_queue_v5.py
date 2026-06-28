from pathlib import Path
import copy
import json

import pytest

from ppd.requirement_candidate_queue_v5 import build_candidate_queue_from_fixture

FIXTURE = Path(__file__).parent / "fixtures" / "requirement_candidate_queue_v5" / "public_citation_span_inventory_v5.json"


def test_candidate_queue_uses_fixture_inventory_only():
    rows = build_candidate_queue_from_fixture(FIXTURE)

    assert len(rows) == 10
    assert {row["requirement_type"] for row in rows} == {
        "obligation",
        "prohibition",
        "permission",
        "precondition",
        "exception",
        "deadline",
        "fee_trigger",
        "license_requirement",
        "document_requirement",
        "action_gate",
    }
    assert all(row["queue_version"] == "requirement_candidate_queue_v5" for row in rows)
    assert all(row["requirement_node_candidate"] is True for row in rows)
    assert all(row["active"] is False for row in rows)
    assert all(row["active_mutation"] is False for row in rows)
    assert all(row["citation_span_inventory_ref"] == "fixture:public-citation-span-inventory-v5" for row in rows)
    assert all(row["source_evidence_id"].startswith("pub-span-v5-") for row in rows)
    assert all(row["human_review_status"] == "pending_human_review" for row in rows)
    assert all(row["formalization_status"] == "not_formalized" for row in rows)
    assert all(row["reviewer_holds"] == ["hold_for_human_review"] for row in rows)
    assert all("fixture-first candidate" in row["rollback_notes"] for row in rows)
    assert rows == build_candidate_queue_from_fixture(FIXTURE)


def test_candidate_queue_embeds_exact_offline_validation_commands():
    row = build_candidate_queue_from_fixture(FIXTURE)[0]

    assert row["validation_commands_exact"] == [
        ["python3", "-m", "py_compile", "ppd/requirement_candidate_queue_v5.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_requirement_candidate_queue_v5.py"],
    ]


@pytest.mark.parametrize(
    "field,match",
    [
        ("citation_span_inventory_ref", "citation span inventory"),
        ("requirement_node_candidate", "RequirementNode candidate"),
        ("requirement_type", "requirement_type"),
        ("source_evidence_id", "source_evidence_id"),
        ("confidence_label", "confidence_label"),
        ("human_review_status", "human_review_status"),
        ("formalization_status", "formalization_status"),
        ("reviewer_holds", "reviewer_holds"),
        ("rollback_notes", "rollback_notes"),
        ("validation_commands_exact", "validation commands"),
    ],
)
def test_candidate_queue_rejects_missing_candidate_fields(tmp_path, field, match):
    payload = _fixture_payload()
    del payload["citation_spans"][0][field]
    fixture = tmp_path / "bad_inventory.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=match):
        build_candidate_queue_from_fixture(fixture)


def test_candidate_queue_rejects_missing_top_level_inventory_reference(tmp_path):
    payload = _fixture_payload()
    del payload["inventory_reference"]
    fixture = tmp_path / "bad_inventory.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="inventory_reference"):
        build_candidate_queue_from_fixture(fixture)


def test_candidate_queue_rejects_missing_requirement_node_candidate_rows(tmp_path):
    payload = _fixture_payload()
    payload["citation_spans"] = []
    fixture = tmp_path / "bad_inventory.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="RequirementNode candidate rows"):
        build_candidate_queue_from_fixture(fixture)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("raw_body", "forbidden", "prohibited artifact key"),
        ("downloaded_document", "fixture.pdf", "prohibited artifact key"),
        ("auth_state", "state.json", "prohibited artifact key"),
        ("active_mutation", True, "active mutation"),
        ("notes", "live extraction completed", "prohibited claim phrase"),
        ("claim", "permit guaranteed", "prohibited claim phrase"),
    ],
)
def test_candidate_queue_rejects_unsafe_artifacts_and_claims(tmp_path, field, value, match):
    payload = _fixture_payload()
    payload["citation_spans"][0][field] = value
    fixture = tmp_path / "bad_inventory.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=match):
        build_candidate_queue_from_fixture(fixture)


def _fixture_payload():
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))
