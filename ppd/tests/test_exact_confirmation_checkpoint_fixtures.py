"""Validate exact-confirmation checkpoint fixtures for consequential DevHub planning."""

from __future__ import annotations

import json
import re
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "exact_confirmation_checkpoint_rejections.json"
GATED_CLASSIFICATIONS = {"consequential", "financial"}
REDACTED_VALUE = "[REDACTED]"
PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b\d{3,6}\s+[A-Za-z0-9 .'-]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Drive|Dr|Way)\b"),
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"),
)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise AssertionError("exact-confirmation fixture must be a JSON object")
    return data


def _parse_utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise AssertionError(f"timestamp must end in Z: {value}")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _contains_private_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_private_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_private_value(item) for item in value)
    if not isinstance(value, str):
        return False
    if value == REDACTED_VALUE:
        return False
    return any(pattern.search(value) for pattern in PRIVATE_VALUE_PATTERNS)


def _validate_checkpoint(checkpoint: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]], generated_at: datetime, max_age_days: int) -> list[str]:
    errors: list[str] = []
    checkpoint_id = str(checkpoint.get("id", ""))
    classification = checkpoint.get("actionClassification")
    planned_action = str(checkpoint.get("plannedActionString", ""))
    confirmation = checkpoint.get("confirmation", {})
    audit_event = checkpoint.get("auditEvent", {})
    preview = checkpoint.get("preview", {})

    if not checkpoint_id:
        errors.append("checkpoint id is required")
    if classification not in GATED_CLASSIFICATIONS:
        return errors
    if not planned_action.strip():
        errors.append("planned action string is required")

    if not isinstance(confirmation, dict):
        errors.append("confirmation checkpoint is required")
        confirmation = {}
    if confirmation.get("required") is not True or confirmation.get("exactRequired") is not True:
        errors.append("exact confirmation is required for consequential or financial DevHub planning")
    exact_phrase = confirmation.get("exactPhrase")
    user_confirmation = confirmation.get("userConfirmation")
    if exact_phrase != planned_action or user_confirmation != planned_action:
        errors.append("exact confirmation must match the planned action string")

    source_ids = checkpoint.get("sourceEvidenceIds", [])
    if not isinstance(source_ids, list) or not source_ids:
        errors.append("source evidence ids are required")
        source_ids = []
    for evidence_id in source_ids:
        evidence = evidence_by_id.get(str(evidence_id))
        if evidence is None:
            errors.append(f"missing source evidence id {evidence_id}")
            continue
        captured_at = _parse_utc(str(evidence.get("capturedAt", "")))
        age_days = (generated_at - captured_at).days
        if age_days > max_age_days:
            errors.append(f"stale source evidence {evidence_id}")
        if evidence.get("public") is not True:
            errors.append(f"source evidence {evidence_id} must be public")

    if not isinstance(preview, dict):
        errors.append("preview is required")
        preview = {}
    if preview.get("privateValuesIncluded") is not False or _contains_private_value(preview):
        errors.append("private value is not allowed in checkpoint fixtures")
    for value_key in ("beforeValue", "afterValue"):
        if preview.get(value_key) != REDACTED_VALUE:
            errors.append(f"{value_key} must be redacted")

    if not isinstance(audit_event, dict):
        errors.append("audit event is required")
        audit_event = {}
    audit_id = str(audit_event.get("id", ""))
    if not audit_id.startswith("audit_"):
        errors.append("audit event id is required")
    if audit_event.get("actionString") != planned_action:
        errors.append("audit action string must match the planned action string")
    if audit_event.get("sourceEvidenceIds") != source_ids:
        errors.append("audit source evidence ids must match checkpoint source evidence ids")

    return errors


class ExactConfirmationCheckpointFixtureTest(unittest.TestCase):
    def test_exact_confirmation_checkpoint_rejections_gate_planning(self) -> None:
        fixture = _load_fixture()
        self.assertEqual(fixture.get("schemaVersion"), 1)
        generated_at = _parse_utc(str(fixture.get("generatedAt", "")))
        self.assertEqual(generated_at.tzinfo, timezone.utc)
        max_age_days = int(fixture.get("maxEvidenceAgeDays", 0))
        self.assertGreater(max_age_days, 0)

        evidence_items = fixture.get("sourceEvidence", [])
        self.assertIsInstance(evidence_items, list)
        evidence_by_id = {str(item.get("id", "")): item for item in evidence_items if isinstance(item, dict)}
        self.assertEqual(len(evidence_by_id), len(evidence_items))

        checkpoints = fixture.get("checkpoints", [])
        self.assertIsInstance(checkpoints, list)
        self.assertGreaterEqual(len(checkpoints), 6)

        accepted_count = 0
        rejected_reasons: set[str] = set()
        for checkpoint in checkpoints:
            self.assertIsInstance(checkpoint, dict)
            errors = _validate_checkpoint(checkpoint, evidence_by_id, generated_at, max_age_days)
            outcome = checkpoint.get("planningOutcome", {})
            self.assertIsInstance(outcome, dict)
            can_plan = outcome.get("canPlan")
            if can_plan is True:
                accepted_count += 1
                self.assertEqual(errors, [], checkpoint.get("id"))
                continue

            self.assertIs(can_plan, False, checkpoint.get("id"))
            self.assertTrue(errors, checkpoint.get("id"))
            expected = str(outcome.get("expectedErrorContains", ""))
            self.assertTrue(expected, checkpoint.get("id"))
            joined_errors = "; ".join(errors)
            self.assertIn(expected, joined_errors, checkpoint.get("id"))
            rejected_reasons.add(expected)

        self.assertEqual(accepted_count, 1)
        self.assertEqual(
            rejected_reasons,
            {"exact confirmation", "stale source evidence", "private value", "audit event id", "action string"},
        )


if __name__ == "__main__":
    unittest.main()
