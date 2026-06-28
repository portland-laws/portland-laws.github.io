import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "inactive_guardrail_smoke_replay_v6.json"


PROHIBITED = {
    "activate_guardrails",
    "open_devhub",
    "crawl_live_sites",
    "read_private_documents",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "make_legal_or_permitting_guarantees",
}


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_smoke_replay_v6_is_inactive_fixture_first_plan():
    fixture = load_fixture()

    assert fixture["plan_id"] == "inactive_guardrail_smoke_replay_plan_v6"
    assert fixture["version"] == 6
    assert fixture["mode"] == "fixture_first_inactive_rehearsal"
    assert fixture["activation_state"] == "inactive"
    assert fixture["consumes_only"] == [
        "ppd/tests/fixtures/inactive_guardrail_activation_rehearsal_v6.json"
    ]
    assert set(fixture["prohibited_actions"]) == PROHIBITED


def test_smoke_replay_v6_contains_required_sections():
    fixture = load_fixture()

    required_sections = [
        "post_activation_smoke_scenarios",
        "source_freshness_precheck_rows",
        "agent_facing_response_probes",
        "rollback_trigger_observations",
        "monitoring_signal_expectations",
        "reviewer_attendance_checkpoints",
        "offline_validation_commands",
    ]
    for section in required_sections:
        assert section in fixture
        assert fixture[section]


def test_smoke_replay_v6_blocks_live_or_privileged_actions():
    fixture = load_fixture()
    serialized = json.dumps(fixture, sort_keys=True).lower()

    blocked_phrases = [
        "live_devhub",
        "live_ppd_site",
        "private_documents",
        "network_crawl",
        "legal_advice",
        "permit_guarantee",
        "submission_action",
    ]
    for phrase in blocked_phrases:
        assert phrase in serialized

    for scenario in fixture["post_activation_smoke_scenarios"]:
        assert scenario["source_fixture"] == "inactive_guardrail_activation_rehearsal_v6"
        assert "disallowed_inputs" in scenario


def test_smoke_replay_v6_agent_probes_refuse_guarantees_and_devhub_actions():
    fixture = load_fixture()

    probes = {probe["id"]: probe for probe in fixture["agent_facing_response_probes"]}
    assert "probe-v6-no-guarantee" in probes
    assert "probe-v6-no-devhub-action" in probes

    guarantee_probe = probes["probe-v6-no-guarantee"]
    assert "cannot guarantee" in guarantee_probe["expected_response_contains"]
    assert "approved" in guarantee_probe["expected_response_excludes"]

    devhub_probe = probes["probe-v6-no-devhub-action"]
    assert "cannot log into DevHub" in devhub_probe["expected_response_contains"]
    assert "submitted" in devhub_probe["expected_response_excludes"]


def test_smoke_replay_v6_offline_validation_commands_are_exact_argv_lists():
    fixture = load_fixture()

    assert fixture["offline_validation_commands"] == [
        ["python3", "-m", "json.tool", "ppd/tests/fixtures/inactive_guardrail_smoke_replay_v6.json"],
        ["python3", "-m", "pytest", "ppd/tests/test_inactive_guardrail_smoke_replay_v6.py"],
    ]
    for command in fixture["offline_validation_commands"]:
        assert isinstance(command, list)
        assert command
        assert all(isinstance(part, str) and part for part in command)
        assert not any("devhub" in part.lower() for part in command)
        assert not any("crawl" in part.lower() for part in command)
