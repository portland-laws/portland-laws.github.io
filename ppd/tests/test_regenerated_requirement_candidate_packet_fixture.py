import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "regenerated_requirement_candidates"
    / "submit_plans_online_changed_source_packet.json"
)


def load_packet():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_regenerated_requirement_candidate_packet_is_fixture_first():
    packet = load_packet()

    assert packet["packet_kind"] == "regenerated_requirement_candidate_packet"
    assert packet["fixture_mode"] == "synthetic_normalized_excerpts_only"
    assert packet["activation"]["status"] == "disabled"
    assert packet["changed_public_source"]["source_type"] == "public_html"
    assert packet["changed_public_source"]["raw_body_persisted"] is False

    excerpts = packet["synthetic_normalized_document_excerpts"]
    assert excerpts
    for excerpt in excerpts:
        assert excerpt["synthetic"] is True
        assert excerpt["raw_source_text"] is False
        assert excerpt["source_evidence_id"].startswith("src-ev-")
        assert "Synthetic" in excerpt["text"]


def test_regenerated_candidates_preserve_evidence_and_remain_disabled():
    packet = load_packet()

    for candidate in packet["regenerated_requirement_candidates"]:
        assert candidate["activation_status"] == "disabled"
        assert candidate["human_review_status"] == "needs_human_review"
        assert 0.0 <= candidate["confidence"] <= 1.0
        assert candidate["affected_process_ids"]
        assert candidate["source_evidence_ids"]

        diff = candidate["old_to_new_requirement_diff"]
        assert diff["preserved_source_evidence_ids"] == candidate["source_evidence_ids"]
        assert diff["changed_fields"]

        new_requirement = candidate["new_requirement"]
        assert new_requirement is not None
        assert new_requirement["source_evidence_ids"] == candidate["source_evidence_ids"]
        assert new_requirement["human_review_status"] == "needs_human_review"
        assert 0.0 <= new_requirement["confidence"] <= 1.0

        old_requirement = candidate["old_requirement"]
        if old_requirement is not None:
            assert old_requirement["requirement_id"] == new_requirement["requirement_id"]
            assert old_requirement["source_evidence_ids"] == candidate["source_evidence_ids"]
            assert diff["preserved_requirement_id"] == old_requirement["requirement_id"]


def test_regenerated_candidates_reference_synthetic_excerpt_evidence_only():
    packet = load_packet()
    excerpt_evidence_ids = {
        excerpt["source_evidence_id"]
        for excerpt in packet["synthetic_normalized_document_excerpts"]
    }

    for candidate in packet["regenerated_requirement_candidates"]:
        assert set(candidate["source_evidence_ids"]).issubset(excerpt_evidence_ids)
