from __future__ import annotations

import unittest
from pathlib import Path

from ppd.recrawl_rehearsal_validation import (
    PublicRecrawlRehearsalPlan,
    assert_valid_public_recrawl_rehearsal_plan,
    validate_public_recrawl_rehearsal_plan,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "public_recrawl_rehearsal"


class PublicRecrawlRehearsalValidationTest(unittest.TestCase):
    def test_accepts_deterministic_public_rehearsal_plan(self) -> None:
        plan = PublicRecrawlRehearsalPlan(
            urls=("https://www.portland.gov/ppd/zoning-code",),
            robots_prerequisites_confirmed=True,
            policy_prerequisites_confirmed=True,
            processor_handoff_intent="Hand validated public HTML to the PP&D document processor fixture path.",
            abort_conditions=("Abort if robots or policy status cannot be verified from committed prerequisites.",),
            notes="Dry-run rehearsal only; no live crawl was run.",
        )

        self.assertEqual(validate_public_recrawl_rehearsal_plan(plan), [])
        assert_valid_public_recrawl_rehearsal_plan(plan)

    def test_rejects_private_authenticated_and_non_allowlisted_urls(self) -> None:
        errors = validate_public_recrawl_rehearsal_plan(
            {
                "urls": [
                    "http://localhost/admin",
                    "https://user:secret@example.com/public",
                    "https://www.portland.gov/login",
                ],
                "robots_prerequisites_confirmed": True,
                "policy_prerequisites_confirmed": True,
                "processor_handoff_intent": "processor handoff planned",
                "abort_conditions": ["abort on prerequisite mismatch"],
            }
        )

        self.assertTrue(any("https" in error for error in errors))
        self.assertTrue(any("private or local" in error for error in errors))
        self.assertTrue(any("not allowlisted" in error for error in errors))
        self.assertTrue(any("embedded credentials" in error for error in errors))
        self.assertTrue(any("authenticated path" in error for error in errors))

    def test_rejects_raw_download_archive_paths(self) -> None:
        errors = validate_public_recrawl_rehearsal_plan(
            PublicRecrawlRehearsalPlan(
                urls=(
                    "https://www.portland.gov/code/raw",
                    "https://www.portland.gov/code/download?download=true",
                    "https://www.portland.gov/code/archive",
                ),
                robots_prerequisites_confirmed=True,
                policy_prerequisites_confirmed=True,
                processor_handoff_intent="processor handoff planned",
                abort_conditions=("abort on raw output request",),
            )
        )

        self.assertEqual(sum("raw body, download, or archive" in error for error in errors), 3)

    def test_rejects_missing_prerequisites_live_flags_and_missing_handoff_controls(self) -> None:
        errors = validate_public_recrawl_rehearsal_plan(
            PublicRecrawlRehearsalPlan(
                urls=("https://www.portland.gov/ppd/zoning-code",),
                live_network_execution=True,
                authenticated_automation=True,
            )
        )

        self.assertTrue(any("robots prerequisites" in error for error in errors))
        self.assertTrue(any("policy prerequisites" in error for error in errors))
        self.assertTrue(any("live network execution" in error for error in errors))
        self.assertTrue(any("authenticated automation" in error for error in errors))
        self.assertTrue(any("processor handoff intent" in error for error in errors))
        self.assertTrue(any("abort condition" in error for error in errors))

    def test_rejects_claim_that_real_recrawl_was_performed(self) -> None:
        errors = validate_public_recrawl_rehearsal_plan(
            PublicRecrawlRehearsalPlan(
                urls=("https://www.portland.gov/ppd/zoning-code",),
                robots_prerequisites_confirmed=True,
                policy_prerequisites_confirmed=True,
                processor_handoff_intent="processor handoff planned",
                abort_conditions=("abort before network access",),
                notes="The completed live recrawl refreshed the corpus.",
            )
        )

        self.assertTrue(any("real recrawl" in error for error in errors))

    def test_fixture_directory_is_ppd_local(self) -> None:
        self.assertIn("ppd/tests/fixtures/public_recrawl_rehearsal", FIXTURES_DIR.as_posix())


if __name__ == "__main__":
    unittest.main()
