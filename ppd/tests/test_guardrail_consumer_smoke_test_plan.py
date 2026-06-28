from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.agent_readiness.consumer_contract_audit import build_consumer_contract_audit_packet
from ppd.agent_readiness.guardrail_consumer_smoke_test_plan import (
    PROHIBITED_OPERATIONS,
    SMOKE_SCENARIO_CATEGORIES,
    build_guardrail_consumer_smoke_test_plan,
    validate_guardrail_consumer_smoke_test_plan,
)
from ppd.release_blockers import reconcile_agent_readiness_release_blockers


FIXTURES = Path(__file__).parent / "fixtures"


class GuardrailConsumerSmokeTestPlanTests(unittest.TestCase):
    def _release_reconciliation_packet(self) -> dict:
        fixture_path = FIXTURES / "release_blockers" / "agent_readiness_inputs.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        return reconcile_agent_readiness_release_blockers(
            fixture["guardrail_consumer_contract_audit"],
            fixture["post_release_audit_findings"],
            fixture["safe_next_action_user_handoff_checklist"],
        )

    def _consumer_contract_audit_packet(self) -> dict:
        fixture_path = FIXTURES / "agent_readiness" / "guardrail_consumer_contract_audit_fixture.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        return build_consumer_contract_audit_packet(
            consumer_integration_checklist=fixture["consumer_integration_checklist"],
            post_release_audit_findings=fixture["post_release_audit_findings"],
        )

    def _expectations(self) -> dict:
        fixture_path = FIXTURES / "agent_readiness" / "guardrail_consumer_smoke_test_plan_expectations.json"
        return json.loads(fixture_path.read_text(encoding="utf-8"))

    def _plan(self) -> dict:
        return build_guardrail_consumer_smoke_test_plan(
            release_blocker_reconciliation_packet=self._release_reconciliation_packet(),
            consumer_contract_audit_packet=self._consumer_contract_audit_packet(),
        )

    def test_builds_offline_fixture_first_smoke_test_plan_from_readiness_packets(self) -> None:
        expectations = self._expectations()
        packet = self._plan()

        self.assertEqual(packet["packet_type"], "ppd.guardrail_consumer_offline_smoke_test_plan.v1")
        for key, expected in expectations["required_plan_flags"].items():
            self.assertEqual(packet[key], expected)
        self.assertEqual(packet["scenario_categories"], expectations["scenario_categories"])
        self.assertEqual(packet["prohibited_operations"], expectations["prohibited_operations"])
        self.assertEqual(packet["scenario_categories"], list(SMOKE_SCENARIO_CATEGORIES))
        self.assertEqual(packet["prohibited_operations"], list(PROHIBITED_OPERATIONS))

    def test_scenarios_are_cited_and_do_not_invoke_consumers_or_devhub(self) -> None:
        expectations = self._expectations()
        packet = self._plan()

        scenarios = packet["synthetic_scenarios"]
        self.assertEqual([scenario["category"] for scenario in scenarios], expectations["scenario_categories"])
        for scenario in scenarios:
            self.assertEqual(scenario["source_packets"], expectations["required_source_packets"])
            self.assertEqual(scenario["must_not"], expectations["prohibited_operations"])
            self.assertTrue(scenario["consumer_contract_source_evidence_ids"])
            self.assertTrue(scenario["release_reconciliation_refs"])
            self.assertTrue(scenario["offline_validation_checks"])
            self.assertNotIn("/home/", json.dumps(scenario, sort_keys=True))

        validation = validate_guardrail_consumer_smoke_test_plan(packet)
        self.assertTrue(validation.ready, validation.problems)

    def test_rejects_packet_that_claims_live_execution(self) -> None:
        packet = self._plan()
        packet["llm_called"] = True
        packet["devhub_launched"] = True
        packet["synthetic_scenarios"][0]["must_not"] = []

        validation = validate_guardrail_consumer_smoke_test_plan(packet)
        self.assertFalse(validation.ready)
        self.assertIn("llm_called must be False", validation.problems)
        self.assertIn("devhub_launched must be False", validation.problems)
        self.assertIn("synthetic_scenarios[0] must prohibit every live operation", validation.problems)

    def test_rejects_uncited_scenarios_and_private_case_facts(self) -> None:
        packet = self._plan()
        packet["synthetic_scenarios"][0]["consumer_contract_source_evidence_ids"] = []
        packet["synthetic_scenarios"][0]["release_reconciliation_refs"] = []
        packet["synthetic_scenarios"][0]["private_case_facts"] = {"owner_email": "person@example.test"}

        validation = validate_guardrail_consumer_smoke_test_plan(packet)

        self.assertFalse(validation.ready)
        self.assertIn("synthetic_scenarios[0] must cite consumer contract evidence", validation.problems)
        self.assertIn("synthetic_scenarios[0] must cite release reconciliation refs", validation.problems)
        self.assertIn(
            "private case fact or live artifact is not allowed at $.synthetic_scenarios[0].private_case_facts",
            validation.problems,
        )

    def test_rejects_private_paths_and_raw_crawl_download_archive_refs(self) -> None:
        packet = self._plan()
        packet["synthetic_scenarios"][1]["local_file_path"] = "/home/alex/private/devhub-case.pdf"
        packet["synthetic_scenarios"][1]["raw_crawl_ref"] = "raw crawl output 2026-05-28"
        packet["synthetic_scenarios"][2]["notes"] = "Use the WARC archive artifact from the last download."

        validation = validate_guardrail_consumer_smoke_test_plan(packet)

        self.assertFalse(validation.ready)
        self.assertIn("private local path is not allowed at $.synthetic_scenarios[1].local_file_path", validation.problems)
        self.assertIn(
            "raw crawl, download, or archive reference is not allowed at $.synthetic_scenarios[1].raw_crawl_ref",
            validation.problems,
        )
        self.assertIn(
            "raw crawl, download, or archive reference is not allowed at $.synthetic_scenarios[2].notes",
            validation.problems,
        )

    def test_rejects_live_execution_claims_and_enabled_consequential_controls(self) -> None:
        packet = self._plan()
        packet["synthetic_scenarios"][3]["observed_result"] = "The test has launched DevHub and submitted the permit request."
        packet["synthetic_scenarios"][3]["payment_enabled"] = True
        packet["synthetic_scenarios"][4]["controls"] = [
            {"id": "upload-corrections", "action": "upload", "enabled": True},
            {"id": "certify-acknowledgement", "action": "certify", "enabled": True},
        ]

        validation = validate_guardrail_consumer_smoke_test_plan(packet)

        self.assertFalse(validation.ready)
        self.assertIn(
            "live execution or consequential action claim is not allowed at $.synthetic_scenarios[3].observed_result",
            validation.problems,
        )
        self.assertIn("enabled consequential control is not allowed at $.synthetic_scenarios[3].payment_enabled", validation.problems)
        self.assertIn("enabled consequential control is not allowed at $.synthetic_scenarios[4].controls", validation.problems)

    def test_rejects_scenarios_that_expect_legal_or_permitting_outcome_guarantees(self) -> None:
        packet = self._plan()
        packet["synthetic_scenarios"][5]["expected_consumer_obligation"] = (
            "The consumer guarantees permit approval and ensures the project is legally compliant."
        )

        validation = validate_guardrail_consumer_smoke_test_plan(packet)

        self.assertFalse(validation.ready)
        self.assertIn(
            "legal or permitting outcome guarantee is not allowed at $.synthetic_scenarios[5].expected_consumer_obligation",
            validation.problems,
        )

    def test_required_scenarios_remain_valid_under_stricter_text_scanning(self) -> None:
        packet = self._plan()
        clone = copy.deepcopy(packet)

        validation = validate_guardrail_consumer_smoke_test_plan(clone)

        self.assertTrue(validation.ready, validation.problems)


if __name__ == "__main__":
    unittest.main()
