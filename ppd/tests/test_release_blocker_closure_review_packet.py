import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_blocker_closure" / "review_packet.json"


def load_packet():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_release_blocker_closure_packet_has_ordered_decisions():
    packet = load_packet()

    decisions = packet["blocker_decisions"]
    assert [decision["blocker_id"] for decision in decisions] == packet["decision_order"]
    assert [decision["status"] for decision in decisions] == ["closed", "closed", "unresolved"]


def test_release_blocker_closure_packet_consumes_required_inputs():
    packet = load_packet()

    consumed_roles = {source["role"] for source in packet["generated_from"]}
    assert consumed_roles == {
        "source_refresh_input",
        "requirement_regeneration_input",
        "safe_action_freshness_input",
    }
    for source in packet["generated_from"]:
        assert source["evidence_ref"].startswith("ppd/tests/fixtures/")
        assert source["packet_id"]


def test_release_blocker_closure_packet_has_review_evidence_and_validation():
    packet = load_packet()

    expected_command = ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]
    for decision in packet["blocker_decisions"]:
        assert decision["reviewer_owner"].startswith("ppd-")
        assert decision["evidence_refs"]
        assert all(ref.startswith("ppd/tests/fixtures/") for ref in decision["evidence_refs"])
        assert expected_command in decision["required_follow_up_validation_commands"]


def test_release_blocker_closure_packet_attests_no_mutating_actions():
    packet = load_packet()

    assert packet["attestations"] == {
        "no_crawl": True,
        "no_devhub": True,
        "no_prompt_mutation": True,
        "no_guardrail_mutation": True,
        "no_release_mutation": True,
        "fixture_first": True,
    }
