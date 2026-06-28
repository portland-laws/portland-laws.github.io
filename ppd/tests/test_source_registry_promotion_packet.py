from pathlib import Path

import pytest

from ppd.source_registry_promotion_packet import PromotionPacketError, build_promotion_decision_packet


FIXTURES = Path(__file__).parent / "fixtures" / "source_registry_promotion"


def test_builds_fixture_first_promotion_decision_packet() -> None:
    packet = build_promotion_decision_packet(
        FIXTURES / "promotion_rehearsal_completed.json",
        FIXTURES / "release_gate_status_passed.json",
        FIXTURES / "reviewer_decisions.json",
    )

    assert packet["packet_type"] == "public_source_registry_promotion_decision"
    assert packet["fixture_first"] is True
    assert packet["crawl_ran"] is False
    assert packet["live_registry_mutated"] is False
    assert packet["summary"] == {"promote": 1, "defer": 1}
    assert [item["source_id"] for item in packet["decisions"]] == [
        "portland-devhub-permits",
        "portland-zoning-code",
    ]

    deferred = packet["decisions"][1]
    assert deferred["decision"] == "defer"
    assert deferred["blocker_refs"] == ["PPD-GATE-coverage-drift"]
    assert deferred["metadata_only_artifact_ids"] == ["artifact:ppd:registry:zoning-code:metadata-review"]


def test_defer_requires_explicit_blocker_refs(tmp_path: Path) -> None:
    bad_decisions = tmp_path / "bad_decisions.json"
    bad_decisions.write_text(
        '{"reviewer":"fixture-reviewer","decisions":[{"source_id":"portland-zoning-code","decision":"defer","blocker_refs":[],"rollback_owner_notes":"Planning policy owner will hold rollback notes.","downstream_invalidation_targets":[],"metadata_only_artifact_ids":["artifact:ppd:registry:zoning-code:metadata-review"]}]}',
        encoding="utf-8",
    )

    with pytest.raises(PromotionPacketError, match="requires explicit blocker_refs"):
        build_promotion_decision_packet(
            FIXTURES / "promotion_rehearsal_completed.json",
            FIXTURES / "release_gate_status_passed.json",
            bad_decisions,
        )
