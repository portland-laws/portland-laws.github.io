"""Fixture-only missing-information schema checks for PP&D process models.

These tests derive requested user facts from the committed public process
fixture. They intentionally validate only reversible request fields: the output
is a list of questions/facts an agent may ask the user for, not browser actions,
selectors, uploads, submissions, payments, or other DevHub automation steps.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Mapping


FIXTURE_ROOT = Path(__file__).parent / "fixtures"
PROCESS_REQUIRED_KEYS = {
    "processId",
    "sourceEvidenceIds",
    "stages",
    "requiredInputs",
    "requiredDocuments",
    "stopGates",
    "lastReviewed",
}
FORBIDDEN_BROWSER_ACTION_KEYS = {
    "action",
    "actionClass",
    "action_class",
    "browserAction",
    "browser_action",
    "click",
    "fill",
    "locator",
    "payment",
    "selector",
    "submit",
    "upload",
}


def _fixture_json_files() -> list[Path]:
    return sorted(path for path in FIXTURE_ROOT.rglob("*.json") if path.is_file())


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _find_process_fixture() -> tuple[Path, Mapping[str, Any]]:
    for path in _fixture_json_files():
        payload = _load_json(path)
        if isinstance(payload, Mapping) and PROCESS_REQUIRED_KEYS.issubset(payload.keys()):
            return path, payload
    raise AssertionError("no committed PP&D process fixture with required process-model keys was found")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{field_name} must be a non-empty string")
    return value


def _input_id(required_input: Mapping[str, Any]) -> str:
    for key in ("inputId", "factId", "id", "key"):
        value = required_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise AssertionError(f"required input is missing a stable identifier: {required_input!r}")


def _input_label(required_input: Mapping[str, Any]) -> str:
    for key in ("label", "name", "prompt", "description"):
        value = required_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise AssertionError(f"required input is missing a user-facing label: {required_input!r}")


def _input_source_evidence_ids(required_input: Mapping[str, Any]) -> list[str]:
    value = required_input.get("sourceEvidenceIds", required_input.get("source_evidence_ids"))
    if not isinstance(value, list) or not value:
        raise AssertionError(f"required input {_input_id(required_input)} must cite source evidence")
    evidence_ids = [_require_text(item, "source evidence id") for item in value]
    return evidence_ids


def _derive_missing_information_requests(
    process_fixture: Mapping[str, Any],
    known_user_facts: Mapping[str, Any],
) -> list[dict[str, Any]]:
    process_id = _require_text(process_fixture.get("processId"), "processId")
    required_inputs = process_fixture.get("requiredInputs")
    if not isinstance(required_inputs, list) or not required_inputs:
        raise AssertionError("process fixture must include requiredInputs")

    requests: list[dict[str, Any]] = []
    for required_input in required_inputs:
        if not isinstance(required_input, Mapping):
            raise AssertionError("each required input must be an object")
        fact_id = _input_id(required_input)
        if known_user_facts.get(fact_id) not in (None, "", [], {}):
            continue
        requests.append(
            {
                "requestId": f"missing-{fact_id}",
                "processId": process_id,
                "requiredInputId": fact_id,
                "requestKind": "user_fact",
                "fieldMode": "reversible_request",
                "label": _input_label(required_input),
                "sourceEvidenceIds": _input_source_evidence_ids(required_input),
            }
        )
    return requests


def _assert_no_browser_action_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_BROWSER_ACTION_KEYS:
                raise AssertionError(f"missing-information request must not include browser action field {path}.{key_text}")
            _assert_no_browser_action_fields(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_browser_action_fields(child, f"{path}[{index}]")


class MissingInformationSchemaTest(unittest.TestCase):
    def test_derives_missing_user_facts_from_committed_process_fixture(self) -> None:
        fixture_path, process_fixture = _find_process_fixture()
        source_evidence_ids = process_fixture.get("sourceEvidenceIds")
        self.assertIsInstance(source_evidence_ids, list, fixture_path)
        self.assertTrue(source_evidence_ids, fixture_path)

        required_inputs = process_fixture.get("requiredInputs")
        self.assertIsInstance(required_inputs, list, fixture_path)
        self.assertTrue(required_inputs, fixture_path)

        first_input = required_inputs[0]
        self.assertIsInstance(first_input, Mapping, fixture_path)
        known_user_facts = {_input_id(first_input): "fixture-known-placeholder"}

        missing_requests = _derive_missing_information_requests(process_fixture, known_user_facts)
        expected_missing_count = len(required_inputs) - 1
        self.assertEqual(expected_missing_count, len(missing_requests))

        process_id = _require_text(process_fixture.get("processId"), "processId")
        known_requirement_ids = {_input_id(item) for item in required_inputs if isinstance(item, Mapping)}
        known_evidence_ids = {str(item) for item in source_evidence_ids}

        for request in missing_requests:
            self.assertEqual(process_id, request["processId"])
            self.assertEqual("user_fact", request["requestKind"])
            self.assertEqual("reversible_request", request["fieldMode"])
            self.assertIn(request["requiredInputId"], known_requirement_ids)
            self.assertIsInstance(request["label"], str)
            self.assertTrue(request["label"].strip())
            self.assertIsInstance(request["sourceEvidenceIds"], list)
            self.assertTrue(request["sourceEvidenceIds"])
            self.assertTrue(set(request["sourceEvidenceIds"]).issubset(known_evidence_ids))
            _assert_no_browser_action_fields(request)


if __name__ == "__main__":
    unittest.main()
