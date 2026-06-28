import json
from pathlib import Path

from ppd.devhub_surface_delta_v1 import build_devhub_surface_delta_packet


def test_builds_devhub_surface_delta_packet_from_fixture_rows() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "devhub_surface_delta_v1" / "observation_rows.json"
    rows = json.loads(fixture_path.read_text(encoding="utf-8"))

    packet = build_devhub_surface_delta_packet(rows)

    assert packet["packet_version"] == "devhub_surface_delta_packet_v1"
    assert packet["source_policy"] == "synthetic_fixture_read_only_no_live_devhub_access"
    assert len(packet["candidate_surface_changes"]) == 3
    assert all(change["promotion_allowed"] is False for change in packet["candidate_surface_changes"])
    assert packet["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/devhub_surface_delta_v1.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_devhub_surface_delta_v1.py"],
    ]


def test_classifies_blocked_actions_and_manual_handoff_paths() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "devhub_surface_delta_v1" / "observation_rows.json"
    rows = json.loads(fixture_path.read_text(encoding="utf-8"))

    packet = build_devhub_surface_delta_packet(rows)
    action_checks = {item["row_id"]: item for item in packet["action_classification_checks"]}

    assert action_checks["obs-001"]["classification"] == "read_only_navigation_or_information"
    assert action_checks["obs-001"]["automation_allowed"] is True
    assert action_checks["obs-002"]["classification"] == "unsupported_action_requires_manual_handoff"
    assert action_checks["obs-002"]["automation_allowed"] is False
    assert "schedule" in action_checks["obs-002"]["matched_blocked_terms"]
    assert packet["attendance_requirements"] == [
        {
            "row_id": "obs-002",
            "surface_key": "devhub.inspection.schedule",
            "requirement": "manual_attendance_required",
            "automation_allowed": False,
        }
    ]
    assert packet["exact_confirmation_requirements"][0]["must_match_before_any_future_action"] is True
    assert packet["unsupported_manual_handoff_paths"][0]["manual_handoff_required"] is True
    assert packet["reviewer_holds"][0]["release_requires_human_review"] is True


def test_records_selector_confidence_and_redaction_impacts() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "devhub_surface_delta_v1" / "observation_rows.json"
    rows = json.loads(fixture_path.read_text(encoding="utf-8"))

    packet = build_devhub_surface_delta_packet(rows)
    selector_notes = {item["row_id"]: item for item in packet["selector_confidence_notes"]}

    assert selector_notes["obs-001"]["confidence"] == "high"
    assert selector_notes["obs-003"]["confidence"] == "low"
    assert packet["redaction_policy_impacts"] == [
        {
            "row_id": "obs-003",
            "surface_key": "devhub.account.profile",
            "impact": "redact_private_values_before_review",
            "private_field_names": ["email"],
            "raw_values_stored": False,
        }
    ]
