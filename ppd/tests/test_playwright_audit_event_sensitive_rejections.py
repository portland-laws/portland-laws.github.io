from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "audit_event_sensitive_rejection_cases.json"

REQUIRED_REJECTION_CATEGORIES = {
    "private_auth_state",
    "cookies",
    "traces",
    "screenshots",
    "raw_browser_storage",
    "uploads",
    "submissions",
    "payments",
    "certifications",
    "cancellations",
    "mfa",
    "captcha",
    "inspection_scheduling",
}

FORBIDDEN_FIELD_REASONS = {
    "authState": "private auth state",
    "storageState": "private auth state",
    "storageStatePath": "private auth state",
    "cookies": "cookies",
    "cookieHeader": "cookies",
    "rawBrowserStorage": "raw browser storage",
    "localStorage": "raw browser storage",
    "sessionStorage": "raw browser storage",
    "indexedDB": "raw browser storage",
}

FORBIDDEN_ATTACHMENT_REASONS = {
    "trace": "traces",
    "screenshot": "screenshots",
    "uploaded_file": "uploads",
}

FORBIDDEN_ACTION_REASONS = {
    "upload_file": "uploads",
    "submit_application": "submissions",
    "submit_request": "submissions",
    "enter_payment": "payments",
    "pay_fee": "payments",
    "certify_statement": "certifications",
    "cancel_request": "cancellations",
    "mfa_challenge": "MFA",
    "mfa_response": "MFA",
    "captcha_challenge": "CAPTCHA",
    "captcha_response": "CAPTCHA",
    "schedule_inspection": "inspection scheduling",
}


class PlaywrightAuditEventSensitiveRejectionTest(unittest.TestCase):
    def test_allowed_audit_event_is_commit_safe(self) -> None:
        fixture = _load_fixture()
        event = fixture["allowedAuditEvent"]

        self.assertEqual([], _validate_audit_event(event))
        self.assertEqual("read_only", event["classification"])
        self.assertEqual("inspect_form_state", event["eventType"])
        self.assertFalse(event["userConfirmation"]["explicit"])
        self.assertTrue(event["redaction"]["valuesRedacted"])
        self.assertFalse(event["redaction"]["privateStatePersisted"])
        self.assertFalse(event["redaction"]["rawBrowserStoragePersisted"])
        self.assertEqual([], event["attachments"])

    def test_fixture_enumerates_every_required_sensitive_rejection(self) -> None:
        fixture = _load_fixture()
        categories = {case["category"] for case in fixture["rejectionCases"]}

        self.assertEqual(REQUIRED_REJECTION_CATEGORIES, categories)

    def test_rejection_cases_fail_with_expected_reason(self) -> None:
        fixture = _load_fixture()
        base_event = fixture["allowedAuditEvent"]

        for case in fixture["rejectionCases"]:
            with self.subTest(category=case["category"]):
                mutated = _mutated_event(base_event, case["category"])
                errors = _validate_audit_event(mutated)
                joined = "\n".join(errors).lower()

                self.assertTrue(errors)
                self.assertIn(case["expectedReason"].lower(), joined)


def _load_fixture() -> dict[str, Any]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{FIXTURE_PATH} must contain a JSON object")
    return data


def _validate_audit_event(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required_fields = (
        "id",
        "recordedAt",
        "workflow",
        "eventType",
        "classification",
        "selectorBasis",
        "sourceEvidenceIds",
        "userConfirmation",
        "redaction",
        "attachments",
    )
    for field in required_fields:
        if field not in event:
            errors.append(f"audit event missing {field}")

    if event.get("eventType") in FORBIDDEN_ACTION_REASONS:
        errors.append(f"audit event includes forbidden action: {FORBIDDEN_ACTION_REASONS[str(event['eventType'])]}")

    if event.get("classification") in {"consequential", "financial"}:
        errors.append("audit event fixture must not commit consequential or financial action execution")

    redaction = event.get("redaction")
    if not isinstance(redaction, dict):
        errors.append("audit event redaction metadata is required")
    else:
        if redaction.get("valuesRedacted") is not True:
            errors.append("audit event values must be redacted")
        if redaction.get("privateStatePersisted") is not False:
            errors.append("audit event must prove private auth state is not persisted")
        if redaction.get("rawBrowserStoragePersisted") is not False:
            errors.append("audit event must prove raw browser storage is not persisted")

    attachments = event.get("attachments")
    if not isinstance(attachments, list):
        errors.append("audit event attachments must be an array")
    else:
        for index, attachment in enumerate(attachments):
            if not isinstance(attachment, dict):
                errors.append(f"attachment {index} must be an object")
                continue
            kind = attachment.get("kind")
            if kind in FORBIDDEN_ATTACHMENT_REASONS:
                errors.append(f"audit event attachment includes forbidden artifact: {FORBIDDEN_ATTACHMENT_REASONS[str(kind)]}")

    for path, key in _walk_keys(event):
        reason = FORBIDDEN_FIELD_REASONS.get(key)
        if reason is not None:
            errors.append(f"audit event field {path} includes forbidden artifact: {reason}")

    return errors


def _walk_keys(value: Any, path: str = "$") -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            keys.append((child_path, str(key)))
            keys.extend(_walk_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            keys.extend(_walk_keys(child, f"{path}[{index}]"))
    return keys


def _mutated_event(base_event: dict[str, Any], category: str) -> dict[str, Any]:
    event = copy.deepcopy(base_event)

    if category == "private_auth_state":
        event["authState"] = {"origin": "[REDACTED]"}
    elif category == "cookies":
        event["cookies"] = [{"name": "[REDACTED]", "value": "[REDACTED]"}]
    elif category == "traces":
        event["attachments"] = [{"kind": "trace", "label": "[REDACTED_TRACE]"}]
    elif category == "screenshots":
        event["attachments"] = [{"kind": "screenshot", "label": "[REDACTED_SCREENSHOT]"}]
    elif category == "raw_browser_storage":
        event["rawBrowserStorage"] = {"localStorage": "[REDACTED]"}
    elif category == "uploads":
        event["eventType"] = "upload_file"
        event["classification"] = "consequential"
    elif category == "submissions":
        event["eventType"] = "submit_application"
        event["classification"] = "consequential"
    elif category == "payments":
        event["eventType"] = "enter_payment"
        event["classification"] = "financial"
    elif category == "certifications":
        event["eventType"] = "certify_statement"
        event["classification"] = "consequential"
    elif category == "cancellations":
        event["eventType"] = "cancel_request"
        event["classification"] = "consequential"
    elif category == "mfa":
        event["eventType"] = "mfa_challenge"
        event["classification"] = "consequential"
    elif category == "captcha":
        event["eventType"] = "captcha_challenge"
        event["classification"] = "consequential"
    elif category == "inspection_scheduling":
        event["eventType"] = "schedule_inspection"
        event["classification"] = "consequential"
    else:
        raise AssertionError(f"unknown rejection category: {category}")

    return event


if __name__ == "__main__":
    unittest.main()
