from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Iterable


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub"
REGISTRY_PATH = FIXTURE_DIR / "playwright_source_evidence_registry.json"
PLAYWRIGHT_PLANNING_FIXTURES = (
    "playwright_accessible_selector_contract.json",
    "action_classification_playwright.json",
    "playwright_planning_confirmation_guardrails.json",
    "draft_action_preview.json",
    "missing_information_form_field_mapping.json",
    "guardrail_playwright_mapping.json"
)
VALUE_KEYS = {
    "afterValue",
    "beforeValue",
    "currentValue",
    "redactedValue",
    "recordedValue"
}


class PlaywrightSourceEvidenceContinuityTest(unittest.TestCase):
    def test_playwright_planning_fixtures_reference_known_evidence_or_processes(self) -> None:
        registry = _load_json(REGISTRY_PATH)
        known_evidence = set(registry["evidenceIds"])
        known_processes = set(registry["processIds"])

        for fixture_name in PLAYWRIGHT_PLANNING_FIXTURES:
            with self.subTest(fixture=fixture_name):
                fixture = _load_json(FIXTURE_DIR / fixture_name)
                evidence_ids = set(_collect_values_for_keys(fixture, {"sourceEvidenceId", "sourceEvidenceIds"}))
                process_ids = set(_collect_values_for_keys(fixture, {"processId"}))

                self.assertTrue(evidence_ids or process_ids, f"{fixture_name} must reference source evidence or process fixtures")
                self.assertFalse(evidence_ids - known_evidence, f"{fixture_name} has unknown evidence ids: {sorted(evidence_ids - known_evidence)}")
                self.assertFalse(process_ids - known_processes, f"{fixture_name} has unknown process ids: {sorted(process_ids - known_processes)}")

    def test_playwright_planning_fixture_values_are_redacted(self) -> None:
        for fixture_name in PLAYWRIGHT_PLANNING_FIXTURES:
            with self.subTest(fixture=fixture_name):
                fixture = _load_json(FIXTURE_DIR / fixture_name)
                for key, value in _walk_key_values(fixture):
                    if key not in VALUE_KEYS:
                        continue
                    if value in {"", None}:
                        continue
                    self.assertIsInstance(value, str)
                    self.assertTrue(
                        value.startswith("[") and value.endswith("]"),
                        f"{fixture_name} {key} must be redacted or blank, got {value!r}",
                    )


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path.name} must contain a JSON object")
    return data


def _collect_values_for_keys(value: Any, keys: set[str]) -> Iterable[str]:
    for key, item in _walk_key_values(value):
        if key not in keys:
            continue
        if isinstance(item, str):
            yield item
        elif isinstance(item, list):
            for child in item:
                if isinstance(child, str):
                    yield child


def _walk_key_values(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk_key_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_key_values(item)


if __name__ == "__main__":
    unittest.main()
