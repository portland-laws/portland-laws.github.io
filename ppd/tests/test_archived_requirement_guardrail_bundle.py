from __future__ import annotations

import json
import re
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "formal_logic"
    / "archived_requirement_guardrail_bundle.json"
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED_REQUIREMENT_KEYS = {
    "obligation",
    "prerequisites",
    "stopGates",
    "reversibleActions",
    "exactConfirmationRequiredFor",
}
FAIL_CLOSED_REASONS = {
    "missing_citation",
    "stale_evidence",
    "private_value_present",
    "consequential_action_without_exact_confirmation",
    "financial_action_without_exact_confirmation",
}
FORBIDDEN_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "schedule_inspection",
}
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "raw_http_body",
    "download_path",
    "browser_cookie",
)


class ArchivedRequirementGuardrailBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_bundle_links_processor_archive_evidence_and_requirement_rules(self) -> None:
        evidence = {
            item["sourceEvidenceId"]: item for item in self.bundle["sourceEvidence"]
        }

        self.assertEqual("archived_requirement_guardrail_bundle", self.bundle["fixtureKind"])
        self.assertEqual("ipfs_datasets_py.processor", self.bundle["processorSuite"]["processorPackage"])
        self.assertTrue(self.bundle["archiveManifestId"])
        self.assertTrue(self.bundle["processorHandoffIds"])
        self.assertFalse(self.bundle["automationBoundary"]["networkAccess"])
        self.assertFalse(self.bundle["automationBoundary"]["liveBrowserStarted"])

        for item in evidence.values():
            self.assertIn(item["processorHandoffId"], self.bundle["processorHandoffIds"])
            self.assertTrue(item["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(item["canonicalUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertRegex(item["contentHashPlaceholder"], SHA256_RE)
            self.assertFalse(item["stale"])
            self.assertTrue(item["citation"]["title"])
            self.assertTrue(item["citation"]["locator"])
            self.assertTrue(item["citation"]["paraphrase"])

        for requirement in self.bundle["requirements"]:
            self.assertTrue(REQUIRED_REQUIREMENT_KEYS.issubset(requirement))
            self.assertTrue(set(requirement["sourceEvidenceIds"]).issubset(evidence))
            self.assertIn("OBLIGATED", requirement["obligation"]["formalRule"])
            self.assertTrue(requirement["prerequisites"])
            self.assertTrue(requirement["stopGates"])
            self.assertTrue(requirement["reversibleActions"])
            self.assertTrue(FORBIDDEN_ACTIONS.intersection(requirement["exactConfirmationRequiredFor"]))

    def test_guardrails_encode_fail_closed_reasons_and_exact_confirmation_gates(self) -> None:
        guardrail_reasons = {
            reason
            for guardrail in self.bundle["guardrails"]
            for reason in guardrail["blockedWhen"]
        }
        self.assertTrue(FAIL_CLOSED_REASONS.issubset(guardrail_reasons))

        for guardrail in self.bundle["guardrails"]:
            self.assertEqual("fail_closed", guardrail["defaultOutcome"])
            self.assertIn("PROHIBITED", guardrail["formalRule"])

        for action in self.bundle["blockedActions"]:
            self.assertIn(action["actionId"], FORBIDDEN_ACTIONS)
            self.assertIn(action["actionClass"], {"consequential", "financial"})
            self.assertTrue(action["requiresExactConfirmation"])
            self.assertFalse(action["exactConfirmationPresent"])
            self.assertEqual("refuse", action["defaultDecision"])

        outcome = self.bundle["agentPlannerOutcome"]
        self.assertFalse(outcome["mayAutonomouslySubmit"])
        self.assertFalse(outcome["mayAutonomouslyPay"])
        self.assertFalse(outcome["mayAutonomouslyUpload"])

    def test_reversible_actions_are_preview_only_and_redacted(self) -> None:
        for requirement in self.bundle["requirements"]:
            for gate in requirement["stopGates"]:
                self.assertEqual("ask_user", gate["defaultOutcome"])
                self.assertIn("consequential", gate["blocksActionClasses"])
                self.assertIn("financial", gate["blocksActionClasses"])

            for action in requirement["reversibleActions"]:
                self.assertEqual("reversible_draft_edit", action["actionClass"])
                self.assertEqual("preview_only", action["mode"])
                self.assertFalse(action["executesInFixture"])
                self.assertEqual("[REDACTED_EMPTY]", action["beforeValue"])
                self.assertTrue(action["afterValue"].startswith("[REDACTED_USER_SUPPLIED_"))

    def test_negative_mutations_fail_closed_for_missing_stale_private_and_risky_actions(self) -> None:
        broken = deepcopy(self.bundle)
        broken["sourceEvidence"][0]["citation"]["locator"] = ""
        broken["sourceEvidence"][1]["stale"] = True
        broken["requirements"][0]["reversibleActions"][0]["afterValue"] = "real user street address"
        broken["blockedActions"][0]["exactConfirmationPresent"] = True
        broken["blockedActions"][1]["defaultDecision"] = "allow"

        errors = validate_guardrail_bundle(broken)

        self.assertIn("sourceEvidence[0].citation is incomplete", errors)
        self.assertIn("sourceEvidence[1] is stale", errors)
        self.assertIn("requirements[0].reversibleActions[0] stores unredacted value", errors)
        self.assertIn("blockedActions[0] must refuse by default without confirmation", errors)
        self.assertIn("blockedActions[1] must refuse by default without confirmation", errors)

    def test_fixture_excludes_private_runtime_artifacts(self) -> None:
        serialized = json.dumps(self.bundle, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertEqual([], find_private_runtime_artifacts(self.bundle))


def validate_guardrail_bundle(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, item in enumerate(bundle.get("sourceEvidence", [])):
        citation = item.get("citation", {})
        if not all(citation.get(key) for key in ("title", "locator", "paraphrase")):
            errors.append(f"sourceEvidence[{index}].citation is incomplete")
        if item.get("stale"):
            errors.append(f"sourceEvidence[{index}] is stale")

    for req_index, requirement in enumerate(bundle.get("requirements", [])):
        for action_index, action in enumerate(requirement.get("reversibleActions", [])):
            after_value = str(action.get("afterValue", ""))
            if not after_value.startswith("[REDACTED_"):
                errors.append(
                    f"requirements[{req_index}].reversibleActions[{action_index}] stores unredacted value"
                )

    for index, action in enumerate(bundle.get("blockedActions", [])):
        if action.get("exactConfirmationPresent") or action.get("defaultDecision") != "refuse":
            errors.append(f"blockedActions[{index}] must refuse by default without confirmation")

    if find_private_runtime_artifacts(bundle):
        errors.append("private/runtime marker present")

    return errors


def find_private_runtime_artifacts(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in {"cookie", "cookies", "token", "password", "rawbody", "screenshotpath", "tracepath"}:
                findings.append(f"{path}.{key}")
            findings.extend(find_private_runtime_artifacts(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_private_runtime_artifacts(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_MARKERS):
            findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
