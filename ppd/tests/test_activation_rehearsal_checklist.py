from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ppd.devhub.activation_rehearsal_checklist import (
    REQUIRED_LIST_FIELDS,
    validate_inactive_activation_rehearsal_checklist_v1,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "activation_rehearsal_checklists"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def finding_codes(checklist: dict[str, Any]) -> set[str]:
    report = validate_inactive_activation_rehearsal_checklist_v1(checklist)
    return {finding.code for finding in report.findings}


def test_inactive_activation_rehearsal_checklist_accepts_valid_placeholder_fixture() -> None:
    report = validate_inactive_activation_rehearsal_checklist_v1(load_fixture("inactive_valid.json"))

    assert report.ok
    assert report.findings == ()


def test_inactive_activation_rehearsal_checklist_rejects_each_missing_required_placeholder() -> None:
    base = load_fixture("inactive_valid.json")

    for field in REQUIRED_LIST_FIELDS:
        checklist = dict(base)
        checklist.pop(field)

        report = validate_inactive_activation_rehearsal_checklist_v1(checklist)

        assert not report.ok
        assert f"missing_{field}" in {finding.code for finding in report.findings}


def test_inactive_activation_rehearsal_checklist_rejects_blank_required_placeholders() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["release_decision_references"] = ["", "   "]

    assert "missing_release_decision_references" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_rejects_private_raw_or_downloaded_artifacts() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["artifacts"] = {
        "auth_state_path": "private/devhub/storage_state.json",
        "raw_download_note": "raw downloaded document was kept locally",
        "trace_file": "devhub.trace.zip",
    }

    assert "private_or_raw_artifact" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_rejects_live_crawl_or_devhub_claims() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["claims"] = {
        "live_crawl_completed": True,
        "summary": "DevHub live run completed for the rehearsal.",
    }

    assert "live_crawl_or_devhub_claim" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_rejects_activation_or_promotion_claims() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["claims"] = ["Promotion completed after smoke replay."]

    assert "activation_or_promotion_claim" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_rejects_official_action_completion_claims() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["claims"] = ["Permit submitted through DevHub."]

    assert "official_action_completion_claim" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_rejects_legal_or_permitting_guarantees() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["claims"] = ["The permit approval is guaranteed once the checklist passes."]

    assert "legal_or_permitting_guarantee" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_rejects_active_mutation_flags() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["mutation_controls"] = {
        "activation_enabled": True,
        "devhub_write_enabled": True,
        "official_action_enabled": True,
    }

    assert "active_mutation_flag" in finding_codes(checklist)


def test_inactive_activation_rehearsal_checklist_requires_inactive_status_and_version() -> None:
    checklist = load_fixture("inactive_valid.json")
    checklist["version"] = "activation_rehearsal_checklist_v2"
    checklist["status"] = "active"

    codes = finding_codes(checklist)

    assert "invalid_version" in codes
    assert "not_inactive" in codes
