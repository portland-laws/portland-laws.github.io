"""Fixture-only stale-answer reconciliation checks for PP&D user facts.

These tests intentionally keep the reconciliation logic local and narrow. The
fixture models user document-store facts that were true or believed true at an
earlier capture time, then compares them with newer PP&D evidence. Any conflict
in timestamp, citation, or requirement identity must fail closed before an agent
uses the stale fact.
"""

from __future__ import annotations

import copy
import json
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "stale_answer_reconciliation"
    / "stale_user_fact_conflicts.json"
)


@dataclass(frozen=True)
class ReconciliationFinding:
    fact_id: str
    evidence_id: str
    reasons: tuple[str, ...]


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise AssertionError("stale-answer fixture must be a JSON object")
    return data


def _parse_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise AssertionError(f"{field_name} must end in Z")
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(timezone.utc)


def _string_field(record: Mapping[str, Any], field_name: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{field_name} must be a non-empty string")
    return value


def _citation(record: Mapping[str, Any], owner_id: str) -> Mapping[str, Any]:
    citation = record.get("citation")
    if not isinstance(citation, Mapping):
        raise AssertionError(f"{owner_id} citation must be an object")
    for field_name in ("sourceId", "url", "anchor", "capturedAt"):
        _string_field(citation, field_name)
    if not _string_field(citation, "url").startswith("https://www.portland.gov/ppd"):
        raise AssertionError(f"{owner_id} citation must point at public PP&D guidance")
    _parse_utc(_string_field(citation, "capturedAt"), f"{owner_id}.citation.capturedAt")
    return citation


def _superseded_requirement_ids(evidence: Mapping[str, Any]) -> set[str]:
    supersedes = evidence.get("supersedesRequirementIds")
    if not isinstance(supersedes, list) or not supersedes:
        raise AssertionError("PP&D evidence must list superseded requirement IDs")
    ids: set[str] = set()
    for item in supersedes:
        if not isinstance(item, str) or not item.strip():
            raise AssertionError("superseded requirement IDs must be non-empty strings")
        ids.add(item)
    return ids


def reconcile_stale_answers(data: Mapping[str, Any]) -> tuple[str, list[ReconciliationFinding]]:
    user_facts = data.get("userFacts")
    evidence_records = data.get("ppdEvidence")
    if not isinstance(user_facts, list) or not user_facts:
        raise AssertionError("fixture requires at least one user fact")
    if not isinstance(evidence_records, list) or not evidence_records:
        raise AssertionError("fixture requires at least one PP&D evidence record")

    findings: list[ReconciliationFinding] = []
    for fact in user_facts:
        if not isinstance(fact, Mapping):
            raise AssertionError("user fact entries must be objects")
        fact_id = _string_field(fact, "factId")
        fact_requirement_id = _string_field(fact, "requirementId")
        fact_value = _string_field(fact, "value")
        fact_asserted_at = _parse_utc(_string_field(fact, "assertedAt"), f"{fact_id}.assertedAt")
        fact_citation = _citation(fact, fact_id)

        for evidence in evidence_records:
            if not isinstance(evidence, Mapping):
                raise AssertionError("PP&D evidence entries must be objects")
            evidence_id = _string_field(evidence, "evidenceId")
            evidence_requirement_id = _string_field(evidence, "requirementId")
            evidence_value = _string_field(evidence, "value")
            evidence_observed_at = _parse_utc(_string_field(evidence, "observedAt"), f"{evidence_id}.observedAt")
            evidence_citation = _citation(evidence, evidence_id)
            superseded_ids = _superseded_requirement_ids(evidence)

            if fact_requirement_id not in superseded_ids and fact_requirement_id != evidence_requirement_id:
                continue

            reasons: list[str] = []
            if evidence_observed_at > fact_asserted_at:
                reasons.append("newer_evidence")
            if fact_requirement_id != evidence_requirement_id:
                reasons.append("requirement_id_conflict")
            if fact_citation["sourceId"] != evidence_citation["sourceId"]:
                reasons.append("citation_conflict")
            if fact_value.casefold() == evidence_value.casefold():
                raise AssertionError(f"{fact_id} should not be paired with identical newer evidence")
            if reasons:
                findings.append(ReconciliationFinding(fact_id=fact_id, evidence_id=evidence_id, reasons=tuple(sorted(set(reasons)))))

    status = "fail_closed" if findings else "allow_current_fact_use"
    return status, findings


class StaleAnswerReconciliationTest(unittest.TestCase):
    def test_fixture_fails_closed_for_newer_conflicting_ppd_evidence(self) -> None:
        data = _load_fixture()

        self.assertEqual(data.get("schemaVersion"), 1)
        status, findings = reconcile_stale_answers(data)

        expected = data.get("expectedDecision")
        self.assertIsInstance(expected, dict)
        self.assertEqual(status, expected["status"])
        self.assertEqual(status, "fail_closed")
        self.assertEqual(
            sorted(finding.fact_id for finding in findings),
            sorted(expected["staleFactIds"]),
        )
        observed_reasons = {reason for finding in findings for reason in finding.reasons}
        self.assertTrue(set(expected["conflictReasons"]).issubset(observed_reasons))
        self.assertEqual(
            expected["requiredAgentAction"],
            "ask_user_to_confirm_current_ppd_requirements_before_using_stale_document_store_facts",
        )

    def test_missing_citations_are_rejected_before_reconciliation(self) -> None:
        data = _load_fixture()
        broken = copy.deepcopy(data)
        del broken["userFacts"][0]["citation"]

        with self.assertRaisesRegex(AssertionError, "citation must be an object"):
            reconcile_stale_answers(broken)

    def test_evidence_without_superseded_requirement_ids_is_rejected(self) -> None:
        data = _load_fixture()
        broken = copy.deepcopy(data)
        broken["ppdEvidence"][0]["supersedesRequirementIds"] = []

        with self.assertRaisesRegex(AssertionError, "superseded requirement IDs"):
            reconcile_stale_answers(broken)

    def test_non_ppd_citation_is_rejected(self) -> None:
        data = _load_fixture()
        broken = copy.deepcopy(data)
        broken["ppdEvidence"][0]["citation"]["url"] = "https://example.test/not-ppd"

        with self.assertRaisesRegex(AssertionError, "public PP&D guidance"):
            reconcile_stale_answers(broken)


if __name__ == "__main__":
    unittest.main()
