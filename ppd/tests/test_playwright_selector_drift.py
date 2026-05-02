"""Fixture-only validation for DevHub Playwright selector drift handling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_selector_drift.json"
MIN_SELECTOR_CONFIDENCE = 0.85
FORBIDDEN_ACTION_FRAGMENTS = (
    "upload",
    "submit",
    "certify",
    "payment",
    "pay",
    "cancel",
    "schedule_inspection",
    "mfa",
    "captcha",
    "account_creation",
    "password_recovery",
)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def _validate_selector_drift_fixture(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    baseline = data.get("baselineSelector", {})
    observed = data.get("observedSelectorCandidate", {})
    decision = data.get("automationDecision", {})
    action = data.get("draftPreviewAction", {})
    page_state = data.get("pageState", {})

    if page_state.get("fixtureOnly") is not True:
        errors.append("selector drift validation must use fixtureOnly page state")
    if page_state.get("authenticated") is not False:
        errors.append("selector drift fixture must not represent an authenticated session")

    baseline_name = str(baseline.get("accessibleName", ""))
    observed_name = str(observed.get("accessibleName", ""))
    if not baseline_name or not observed_name:
        errors.append("baseline and observed accessible names are required")
    if baseline_name == observed_name:
        errors.append("fixture must model a changed accessible name")

    drift_signals = set(observed.get("driftSignals", []))
    if "accessible_name_changed" not in drift_signals:
        errors.append("changed accessible name must be recorded as a drift signal")

    confidence = observed.get("matchConfidence")
    if not isinstance(confidence, (int, float)):
        errors.append("observed selector matchConfidence must be numeric")
        confidence = 0.0
    if confidence >= MIN_SELECTOR_CONFIDENCE:
        errors.append("selector drift scenario must remain below the confidence threshold")

    threshold = baseline.get("confidenceThreshold")
    if threshold != MIN_SELECTOR_CONFIDENCE:
        errors.append("baseline selector confidenceThreshold must be 0.85")

    if decision.get("continueDraftPreview") is not False:
        errors.append("draft-preview automation must stop when selector drift is low confidence")
    if decision.get("refuseSelector") is not True:
        errors.append("low-confidence changed selector must be refused")
    if decision.get("requiresHumanReview") is not True:
        errors.append("selector drift must require human review before automation continues")

    reason_codes = set(decision.get("reasonCodes", []))
    expected_reason_codes = {
        "accessible_name_drift",
        "low_selector_confidence",
        "human_review_required_before_draft_preview",
    }
    missing_reason_codes = expected_reason_codes.difference(reason_codes)
    if missing_reason_codes:
        errors.append(f"automation decision missing reason codes: {sorted(missing_reason_codes)}")

    if action.get("classification") != "reversible_draft_edit":
        errors.append("selector drift fixture should gate only a reversible draft edit preview")
    if action.get("exactUserConfirmation") is not False:
        errors.append("draft preview fixtures must keep exactUserConfirmation false by default")

    operation_text = " ".join(str(action.get(key, "")).lower() for key in ("actionId", "classification", "operation"))
    forbidden_hits = [fragment for fragment in FORBIDDEN_ACTION_FRAGMENTS if fragment in operation_text]
    if forbidden_hits:
        errors.append(f"selector drift fixture includes forbidden action fragments: {forbidden_hits}")

    absent = data.get("forbiddenArtifactsAbsent", {})
    for key in ("authState", "cookies", "trace", "screenshot", "rawBrowserStorage", "liveDevhubUrl"):
        if absent.get(key) is not True:
            errors.append(f"forbidden artifact marker must be absent: {key}")

    return errors


def test_playwright_selector_drift_fixture_stops_draft_preview_for_human_review() -> None:
    data = _load_fixture()
    assert _validate_selector_drift_fixture(data) == []


def test_playwright_selector_drift_validation_rejects_continuing_automation() -> None:
    data = _load_fixture()
    data["automationDecision"] = dict(data["automationDecision"])
    data["automationDecision"]["continueDraftPreview"] = True

    errors = _validate_selector_drift_fixture(data)

    assert "draft-preview automation must stop when selector drift is low confidence" in errors


def test_playwright_selector_drift_validation_rejects_missing_human_review() -> None:
    data = _load_fixture()
    data["automationDecision"] = dict(data["automationDecision"])
    data["automationDecision"]["requiresHumanReview"] = False

    errors = _validate_selector_drift_fixture(data)

    assert "selector drift must require human review before automation continues" in errors


def test_playwright_selector_drift_validation_rejects_high_confidence_drift_fixture() -> None:
    data = _load_fixture()
    data["observedSelectorCandidate"] = dict(data["observedSelectorCandidate"])
    data["observedSelectorCandidate"]["matchConfidence"] = 0.91

    errors = _validate_selector_drift_fixture(data)

    assert "selector drift scenario must remain below the confidence threshold" in errors
