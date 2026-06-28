from __future__ import annotations

import unittest

from ppd.logic.requirement_regeneration_queue import (
    assert_requirement_regeneration_queue_plan,
    validate_requirement_regeneration_queue_plan,
)


class RequirementRegenerationQueueValidationTest(unittest.TestCase):
    def _valid_plan(self) -> dict[str, object]:
        return {
            "plan_id": "fixture-first-requirement-regeneration",
            "source_evidence": [
                {
                    "source_evidence_id": "ev-file-standards-2026-05-08",
                    "canonical_url": "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
                    "freshness_status": "changed",
                }
            ],
            "queue_policy": {
                "fixture_first": True,
                "live_crawl_required": False,
                "blocks_downstream_activation_until_review_acknowledgement": True,
            },
            "queue_items": [
                {
                    "queue_item_id": "regen-ppd-file-standards",
                    "source_id": "ppd-file-standards",
                    "source_url": "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
                    "change_kinds": ["changed_file_rule"],
                    "source_evidence_ids": ["ev-file-standards-2026-05-08"],
                    "affected_requirement_ids": ["req-file-name-standard"],
                    "affected_process_model_ids": ["process-single-pdf-submit-plans"],
                    "affected_guardrail_bundle_ids": ["guardrail-single-pdf-submit-plans"],
                    "human_review_owners": ["ppd-requirements-review"],
                    "blocked_downstream_activation": True,
                    "reviewer_acknowledgement_required": True,
                }
            ],
        }

    def test_accepts_fixture_first_cited_blocked_plan(self) -> None:
        result = validate_requirement_regeneration_queue_plan(self._valid_plan())
        self.assertTrue(result.ready, result.messages())
        assert_requirement_regeneration_queue_plan(self._valid_plan())

    def test_rejects_uncited_changed_source_mapping(self) -> None:
        plan = self._valid_plan()
        plan["queue_items"][0].pop("source_evidence_ids")  # type: ignore[index,union-attr]

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        self.assertIn("uncited_changed_source_mapping", {issue.code for issue in result.issues})

    def test_rejects_missing_downstream_links(self) -> None:
        plan = self._valid_plan()
        item = plan["queue_items"][0]  # type: ignore[index]
        item["affected_requirement_ids"] = []  # type: ignore[index]
        item["affected_process_model_ids"] = []  # type: ignore[index]
        item["affected_guardrail_bundle_ids"] = []  # type: ignore[index]

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        codes = {issue.code for issue in result.issues}
        self.assertIn("missing_affected_requirement_links", codes)
        self.assertIn("missing_affected_process_links", codes)
        self.assertIn("missing_affected_guardrail_links", codes)

    def test_rejects_private_case_facts(self) -> None:
        plan = self._valid_plan()
        plan["case_facts"] = {"property_owner_name": "private fixture value"}

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        self.assertIn("private_case_facts", {issue.code for issue in result.issues})

    def test_rejects_stale_source_marked_current_without_acknowledgement(self) -> None:
        plan = self._valid_plan()
        evidence = plan["source_evidence"][0]  # type: ignore[index]
        evidence["freshness_status"] = "stale"  # type: ignore[index]
        evidence["cache_status"] = "current"  # type: ignore[index]

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        self.assertIn("stale_source_marked_current_without_acknowledgement", {issue.code for issue in result.issues})

    def test_accepts_stale_source_marked_current_with_reviewer_acknowledgement(self) -> None:
        plan = self._valid_plan()
        evidence = plan["source_evidence"][0]  # type: ignore[index]
        evidence["freshness_status"] = "stale"  # type: ignore[index]
        evidence["cache_status"] = "current"  # type: ignore[index]
        evidence["stale_source_current_acknowledgement"] = True  # type: ignore[index]

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertTrue(result.ready, result.messages())

    def test_rejects_downstream_activation_without_reviewer_review(self) -> None:
        plan = self._valid_plan()
        item = plan["queue_items"][0]  # type: ignore[index]
        item["blocked_downstream_activation"] = False  # type: ignore[index]
        item["activate_downstream"] = True  # type: ignore[index]

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        self.assertIn("downstream_activation_without_reviewer_review", {issue.code for issue in result.issues})

    def test_rejects_live_crawl_provenance(self) -> None:
        plan = self._valid_plan()
        plan["provenance"] = {"capture_mode": "live_crawl"}

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        self.assertIn("live_crawl_provenance", {issue.code for issue in result.issues})

    def test_rejects_raw_document_references(self) -> None:
        plan = self._valid_plan()
        plan["raw_document_refs"] = ["/tmp/downloads/source.pdf"]

        result = validate_requirement_regeneration_queue_plan(plan)

        self.assertFalse(result.ready)
        self.assertIn("raw_document_reference", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
