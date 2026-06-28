from pathlib import Path

from ppd.replay.post_decision_smoke_replay_v3 import (
    EXPECTED_OFFLINE_VALIDATION_COMMANDS,
    classify_action,
    replay_from_fixture_paths,
)

FIXTURES = Path(__file__).parent / "fixtures" / "post_decision_smoke_replay_v3"


def test_fixture_first_post_decision_smoke_replay_v3_passes() -> None:
    report = replay_from_fixture_paths(
        FIXTURES / "devhub_read_only_release_decision_packet_v3.json",
        FIXTURES / "synthetic_surface_map_placeholders_v3.json",
    )

    assert report["schema"] == "ppd_post_decision_smoke_replay_v3_report"
    assert report["ok"] is True
    assert {finding["check"] for finding in report["findings"]} == {
        "decision_packet_v3",
        "fixture_first_mode",
        "no_private_or_session_artifacts",
        "read_only_route_lookup",
        "action_classification",
        "exact_confirmation_gates",
        "manual_handoff_gates",
        "reviewer_holds",
        "rollback_readiness",
        "exact_offline_validation_commands",
    }


def test_action_classifier_rejects_forbidden_official_actions() -> None:
    assert classify_action({"type": "submission"}) == "forbidden_mutating_or_official_action"
    assert classify_action({"type": "payment"}) == "forbidden_mutating_or_official_action"
    assert classify_action({"type": "upload"}) == "forbidden_mutating_or_official_action"


def test_exact_offline_validation_commands_are_stable() -> None:
    assert EXPECTED_OFFLINE_VALIDATION_COMMANDS == [
        ["python3", "-m", "py_compile", "ppd/replay/post_decision_smoke_replay_v3.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_post_decision_smoke_replay_v3.py"],
    ]
