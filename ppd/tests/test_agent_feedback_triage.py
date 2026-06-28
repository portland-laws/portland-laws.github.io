from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.agent_feedback_triage import (
    FeedbackTriageError,
    build_agent_consumer_feedback_triage,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_feedback_triage"


def _load_fixture(name: str) -> dict[str, object]:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def _load_packets() -> dict[str, dict[str, object]]:
    return {
        "release_consumer_handoff": _load_fixture("release_consumer_handoff.json"),
        "safe_action_regression": _load_fixture("safe_action_regression.json"),
        "post_promotion_smoke_test_plan": _load_fixture("post_promotion_smoke_test_plan.json"),
    }


def test_builds_cited_fixture_first_feedback_triage_packet() -> None:
    triage = build_agent_consumer_feedback_triage(_load_packets())

    assert triage["packet_id"] == "fixture-agent-consumer-feedback-triage-v1"
    assert triage["mode"] == "fixture_first"
    assert triage["attestations"] == {
        "no_live_agent_consumers_invoked": True,
        "no_private_case_files_read": True,
        "no_prompt_mutations_performed": True,
        "no_release_state_mutations_performed": True,
        "fixtures_only": True,
    }

    categories = triage["feedback_categories"]
    assert isinstance(categories, list)
    assert [category["category_id"] for category in categories] == [
        "release-consumer-readiness",
        "safe-action-boundary",
        "post-promotion-smoke-coverage",
        "cross-packet-consumer-feedback",
    ]

    for category in categories:
        assert category["citations"]
        assert category["expected_prompt_or_refusal_updates"]
        assert category["reviewer_owner"]
        assert category["reviewer_owner_field"]
        assert category["regression_rerun_triggers"]


def test_exposes_reviewer_owner_fields_and_rerun_triggers() -> None:
    triage = build_agent_consumer_feedback_triage(_load_packets())

    assert triage["reviewer_owner_fields"] == {
        "release_consumer_reviewer_owner": "ppd-release-reviewer",
        "safe_action_regression_reviewer_owner": "ppd-guardrail-reviewer",
        "post_promotion_smoke_reviewer_owner": "ppd-smoke-reviewer",
        "cross_packet_reviewer_owner": "ppd-release-reviewer",
    }

    trigger_rows = triage["regression_rerun_triggers"]
    assert len(trigger_rows) == 4
    assert any(
        row["category_id"] == "safe-action-boundary"
        and "new consequential action category appears" in row["triggers"]
        for row in trigger_rows
    )


def test_requires_all_three_input_packets() -> None:
    packets = _load_packets()
    packets.pop("safe_action_regression")

    with pytest.raises(FeedbackTriageError, match="safe_action_regression"):
        build_agent_consumer_feedback_triage(packets)


def test_requires_citations_for_each_packet() -> None:
    packets = _load_packets()
    packets["release_consumer_handoff"] = {
        "packet_id": "broken",
        "citations": [],
    }

    with pytest.raises(FeedbackTriageError, match="at least one citation"):
        build_agent_consumer_feedback_triage(packets)
