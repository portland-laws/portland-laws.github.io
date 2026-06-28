"""Regression coverage for tranche 2 source-evidence continuation.

The fixture is intentionally deterministic: it proves the platform contracts keep
public source evidence IDs attached as data moves from archival planning through
DevHub draft automation, local PDF draft filling, and formal-logic guardrails.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tranche2_evidence_continuation.json"


class Tranche2EvidenceContinuationTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_every_stage_uses_declared_source_evidence(self) -> None:
        known_ids = set(self.fixture["source_evidence_ids"])
        shared_ids = set(self.fixture["expected_shared_source_evidence_ids"])

        self.assertTrue(shared_ids, "fixture must declare at least one shared evidence ID")
        self.assertLessEqual(shared_ids, known_ids)

        for stage_name, stage in self.fixture["stages"].items():
            stage_ids = set(stage["source_evidence_ids"])
            self.assertTrue(stage_ids, f"{stage_name} must carry source evidence IDs")
            self.assertLessEqual(stage_ids, known_ids, f"{stage_name} uses undeclared evidence")
            self.assertLessEqual(shared_ids, stage_ids, f"{stage_name} lost shared evidence")

            for output in stage["outputs"]:
                output_ids = set(output["source_evidence_ids"])
                output_label = f"{stage_name}:{output['kind']}:{output['id']}"
                self.assertTrue(output_ids, f"{output_label} must carry source evidence IDs")
                self.assertLessEqual(output_ids, stage_ids, f"{output_label} uses non-stage evidence")
                self.assertLessEqual(shared_ids, output_ids, f"{output_label} lost shared evidence")

    def test_downstream_outputs_remain_connected_to_archived_documents(self) -> None:
        stages = self.fixture["stages"]
        archival_document_ids: set[str] = set()

        for output in stages["whole_site_archival"]["outputs"]:
            archival_document_ids.update(output.get("document_ids", []))

        self.assertTrue(archival_document_ids, "archival stage must expose document IDs")

        for stage_name in (
            "playwright_draft_automation",
            "pdf_field_filling",
            "formal_logic_outputs",
        ):
            input_document_ids = set(stages[stage_name]["input_document_ids"])
            self.assertTrue(input_document_ids, f"{stage_name} must declare document inputs")
            self.assertLessEqual(
                input_document_ids,
                archival_document_ids,
                f"{stage_name} references documents outside the archive manifest",
            )

    def test_formal_logic_guardrails_preserve_action_boundaries(self) -> None:
        logic_outputs = self.fixture["stages"]["formal_logic_outputs"]["outputs"]
        guardrail_batch = next(output for output in logic_outputs if output["kind"] == "guardrail_batch")
        predicates = set(guardrail_batch["predicates"])

        required_predicates = {
            "requires_source_evidence",
            "draft_fill_is_reversible",
            "exact_confirmation_required_before_official_action",
            "refuse_payment_submission_without_manual_handoff",
        }
        self.assertLessEqual(required_predicates, predicates)


if __name__ == "__main__":
    unittest.main()
