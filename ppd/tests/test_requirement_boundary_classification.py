from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_boundary"
    / "requirement_boundary_classification.json"
)

EXPECTED_CLASSIFICATIONS = {
    "legal_obligation",
    "operational_ui_hint",
    "user_fact",
    "document_requirement",
    "fee_notice",
    "deadline",
}

EXPECTED_REQUIREMENT_TYPES = {
    "legal_obligation": "obligation",
    "operational_ui_hint": "workflow_hint",
    "user_fact": "precondition",
    "document_requirement": "submittal_requirement",
    "fee_notice": "fee_notice",
    "deadline": "deadline",
}


class RequirementBoundaryClassificationTest(unittest.TestCase):
    def test_requirement_boundary_fixture_classifies_adjacent_requirement_types_separately(self) -> None:
        fixture = _load_fixture()

        errors = _validate_requirement_boundary_fixture(fixture)

        self.assertEqual([], errors)

    def test_requirement_boundary_validation_fails_closed_without_citations(self) -> None:
        fixture = _load_fixture()
        fixture["records"][0]["citations"] = []

        errors = _validate_requirement_boundary_fixture(fixture)

        self.assertIn("record rb-legal-obligation-001: at least one citation is required", errors)

    def test_requirement_boundary_validation_fails_closed_without_review_needed_flag(self) -> None:
        fixture = _load_fixture()
        fixture["records"][1].pop("reviewNeeded")

        errors = _validate_requirement_boundary_fixture(fixture)

        self.assertIn("record rb-operational-ui-hint-001: reviewNeeded boolean is required", errors)

    def test_requirement_boundary_validation_rejects_merged_boundary_classes(self) -> None:
        fixture = _load_fixture()
        fixture["records"][2]["classification"] = "legal_obligation"

        errors = _validate_requirement_boundary_fixture(fixture)

        self.assertIn("fixture must contain exactly one record for each requirement-boundary classification", errors)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _validate_requirement_boundary_fixture(fixture: dict[str, Any]) -> list[str]:
    data = deepcopy(fixture)
    errors: list[str] = []

    if data.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")

    records = data.get("records")
    if not isinstance(records, list) or not records:
        return errors + ["records must be a non-empty list"]

    seen_ids: set[str] = set()
    classifications: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record at index {index}: must be an object")
            continue

        record_id = _non_empty_text(record.get("id")) or f"index {index}"
        if record_id in seen_ids:
            errors.append(f"record {record_id}: duplicate id")
        seen_ids.add(record_id)

        classification = _non_empty_text(record.get("classification"))
        if classification is None:
            errors.append(f"record {record_id}: classification is required")
        elif classification not in EXPECTED_CLASSIFICATIONS:
            errors.append(f"record {record_id}: unsupported classification {classification}")
        else:
            classifications.append(classification)
            expected_type = EXPECTED_REQUIREMENT_TYPES[classification]
            if record.get("requirementType") != expected_type:
                errors.append(
                    f"record {record_id}: {classification} must use requirementType {expected_type}"
                )

        if _non_empty_text(record.get("statement")) is None:
            errors.append(f"record {record_id}: statement is required")

        if "reviewNeeded" not in record or not isinstance(record.get("reviewNeeded"), bool):
            errors.append(f"record {record_id}: reviewNeeded boolean is required")

        citations = record.get("citations")
        if not isinstance(citations, list) or not citations:
            errors.append(f"record {record_id}: at least one citation is required")
        else:
            for citation_index, citation in enumerate(citations):
                errors.extend(_validate_citation(record_id, citation_index, citation))

        evidence_ids = record.get("sourceEvidenceIds")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            errors.append(f"record {record_id}: sourceEvidenceIds must be a non-empty list")

    if set(classifications) != EXPECTED_CLASSIFICATIONS or len(classifications) != len(EXPECTED_CLASSIFICATIONS):
        errors.append("fixture must contain exactly one record for each requirement-boundary classification")

    return errors


def _validate_citation(record_id: str, index: int, citation: Any) -> list[str]:
    if not isinstance(citation, dict):
        return [f"record {record_id}: citation {index} must be an object"]

    errors: list[str] = []
    source_url = _non_empty_text(citation.get("sourceUrl"))
    source_anchor = _non_empty_text(citation.get("sourceAnchor"))
    evidence_id = _non_empty_text(citation.get("evidenceId"))

    if source_url is None or not source_url.startswith("https://www.portland.gov/"):
        errors.append(f"record {record_id}: citation {index} requires a public Portland.gov sourceUrl")
    if source_anchor is None:
        errors.append(f"record {record_id}: citation {index} requires sourceAnchor")
    if evidence_id is None:
        errors.append(f"record {record_id}: citation {index} requires evidenceId")

    return errors


def _non_empty_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


if __name__ == "__main__":
    unittest.main()
