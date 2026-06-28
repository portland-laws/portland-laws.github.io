from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ppd.logic.agent_bundle_loader import (  # noqa: E402
    AgentBundleValidationError,
    collect_agent_bundle_validation_errors,
    load_agent_bundle,
)

FIXTURES = Path(__file__).parent / "fixtures" / "agent_bundles"


class AgentBundleLoaderValidationTests(unittest.TestCase):
    def test_accepts_cited_bundle_with_manual_handoff_and_cited_explanations(self) -> None:
        bundle = load_agent_bundle(FIXTURES / "valid_agent_bundle.json")
        self.assertEqual(bundle["guardrail_bundle"]["guardrail_bundle_id"], "gb-valid-demo")

    def test_rejects_required_source_grounding_and_handoff_violations(self) -> None:
        with (FIXTURES / "invalid_agent_bundle.json").open("r", encoding="utf-8") as handle:
            bundle = json.load(handle)

        issues = collect_agent_bundle_validation_errors(bundle)
        codes = {issue.code for issue in issues}

        self.assertIn("uncited_process_stage", codes)
        self.assertIn("unsupported_action_missing_manual_handoff", codes)
        self.assertIn("guardrail_predicate_missing_evidence_ids", codes)
        self.assertIn("next_safe_action_explanation_missing_citation_spans", codes)

    def test_loader_raises_for_invalid_bundle(self) -> None:
        with self.assertRaises(AgentBundleValidationError) as caught:
            load_agent_bundle(FIXTURES / "invalid_agent_bundle.json")

        self.assertIn("uncited_process_stage", str(caught.exception))
        self.assertGreaterEqual(len(caught.exception.issues), 4)


if __name__ == "__main__":
    unittest.main()
