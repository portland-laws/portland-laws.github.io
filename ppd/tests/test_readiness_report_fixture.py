import copy
import json
from pathlib import Path

from ppd.readiness.report import validate_readiness_bundle


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "readiness_report" / "complete_offline_case_bundle.json"


def load_bundle():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def diagnostic_codes(report):
    return {diagnostic["code"] for diagnostic in report["diagnostics"]}


def test_complete_offline_case_bundle_is_ready():
    report = validate_readiness_bundle(load_bundle())

    assert report["case_id"] == "case-offline-single-pdf-demo"
    assert report["ready"] is True
    assert report["diagnostics"] == []
    assert report["checked_sections"] == [
        "source_freshness",
        "citation_integrity",
        "process_dependency_ordering",
        "user_gap_analysis",
        "next_safe_actions",
        "evidence_packs",
        "question_planning",
        "handoff_packets",
    ]


def test_missing_requirement_citation_fails_closed():
    bundle = load_bundle()
    broken = copy.deepcopy(bundle)
    broken["requirements"][0]["source_evidence_ids"] = []

    report = validate_readiness_bundle(broken)

    assert report["ready"] is False
    assert "missing_citation" in diagnostic_codes(report)


def test_unknown_evidence_reference_fails_closed():
    bundle = load_bundle()
    broken = copy.deepcopy(bundle)
    broken["evidence_packs"][0]["evidence_ids"] = ["ev-not-in-fixture"]

    report = validate_readiness_bundle(broken)

    assert report["ready"] is False
    assert "unknown_citation" in diagnostic_codes(report)


def test_consequential_next_safe_action_fails_closed():
    bundle = load_bundle()
    broken = copy.deepcopy(bundle)
    broken["user_gap_analysis"]["next_safe_actions"].append(
        {
            "action_id": "unsafe-submit",
            "action_type": "submit",
            "label": "Submit the application",
            "source_evidence_ids": ["ev-devhub-application-save"],
        }
    )

    report = validate_readiness_bundle(broken)

    assert report["ready"] is False
    assert "consequential_action_not_safe" in diagnostic_codes(report)


def test_handoff_consequential_action_requires_attendance_and_exact_confirmation():
    bundle = load_bundle()
    broken = copy.deepcopy(bundle)
    broken["handoff_packets"][0]["requires_exact_confirmation"] = False
    broken["handoff_packets"][0]["requires_attendance"] = False

    report = validate_readiness_bundle(broken)

    assert report["ready"] is False
    codes = diagnostic_codes(report)
    assert "missing_attendance_gate" in codes
    assert "missing_exact_confirmation" in codes


def test_process_dependency_ordering_fails_closed():
    bundle = load_bundle()
    broken = copy.deepcopy(bundle)
    stages = broken["process_model"]["stages"]
    stages[1], stages[2] = stages[2], stages[1]

    report = validate_readiness_bundle(broken)

    assert report["ready"] is False
    assert "dependency_order_violation" in diagnostic_codes(report)
