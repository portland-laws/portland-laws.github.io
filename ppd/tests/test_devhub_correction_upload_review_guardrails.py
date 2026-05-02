from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.correction_upload_review_guardrails import (
    CorrectionReviewAction,
    CorrectionReviewDecision,
    CorrectionReviewRequest,
    CorrectionUploadReviewState,
    evaluate_correction_upload_review,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "correction_upload_review_guardrail_fixture.json"


class CorrectionUploadReviewGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.state = CorrectionUploadReviewState.from_dict(fixture["reviewState"])
        self.confirmations = fixture["confirmations"]

    def test_correction_upload_review_can_produce_read_only_preview(self) -> None:
        result = evaluate_correction_upload_review(
            self.state,
            CorrectionReviewRequest(action=CorrectionReviewAction.PREVIEW, session_id=self.state.session_id),
        )

        self.assertTrue(result.allowed)
        self.assertEqual(CorrectionReviewDecision.ALLOW_PREVIEW, result.decision)
        self.assertGreaterEqual(len(result.action_preview), 3)
        self.assertEqual((), result.executed_browser_actions)
        self.assertTrue(any("No browser upload" in item for item in result.action_preview))

    def test_official_upload_is_refused_without_exact_session_confirmation(self) -> None:
        for user_confirmation in (
            None,
            "Upload my corrections",
            self.confirmations["wrongSessionUpload"],
            self.confirmations["certification"],
        ):
            with self.subTest(user_confirmation=user_confirmation):
                result = evaluate_correction_upload_review(
                    self.state,
                    CorrectionReviewRequest(
                        action=CorrectionReviewAction.OFFICIAL_UPLOAD,
                        session_id=self.state.session_id,
                        user_confirmation=user_confirmation,
                    ),
                )

                self.assertFalse(result.allowed)
                self.assertEqual(CorrectionReviewDecision.REFUSE_MISSING_EXACT_CONFIRMATION, result.decision)
                self.assertEqual((), result.executed_browser_actions)

    def test_certification_is_refused_without_exact_session_confirmation(self) -> None:
        for user_confirmation in (
            None,
            "I certify",
            self.confirmations["wrongSessionCertification"],
            self.confirmations["officialUpload"],
        ):
            with self.subTest(user_confirmation=user_confirmation):
                result = evaluate_correction_upload_review(
                    self.state,
                    CorrectionReviewRequest(
                        action=CorrectionReviewAction.CERTIFICATION,
                        session_id=self.state.session_id,
                        user_confirmation=user_confirmation,
                    ),
                )

                self.assertFalse(result.allowed)
                self.assertEqual(CorrectionReviewDecision.REFUSE_MISSING_EXACT_CONFIRMATION, result.decision)
                self.assertEqual((), result.executed_browser_actions)

    def test_exact_session_specific_confirmation_allows_consequential_gates_only(self) -> None:
        upload_result = evaluate_correction_upload_review(
            self.state,
            CorrectionReviewRequest(
                action=CorrectionReviewAction.OFFICIAL_UPLOAD,
                session_id=self.state.session_id,
                user_confirmation=self.confirmations["officialUpload"],
            ),
        )
        certification_result = evaluate_correction_upload_review(
            self.state,
            CorrectionReviewRequest(
                action=CorrectionReviewAction.CERTIFICATION,
                session_id=self.state.session_id,
                user_confirmation=self.confirmations["certification"],
            ),
        )

        self.assertTrue(upload_result.allowed)
        self.assertTrue(certification_result.allowed)
        self.assertEqual(CorrectionReviewDecision.ALLOW_CONFIRMED_CONSEQUENTIAL_ACTION, upload_result.decision)
        self.assertEqual(CorrectionReviewDecision.ALLOW_CONFIRMED_CONSEQUENTIAL_ACTION, certification_result.decision)
        self.assertEqual((), upload_result.executed_browser_actions)
        self.assertEqual((), certification_result.executed_browser_actions)

    def test_matching_phrase_from_different_session_is_refused(self) -> None:
        result = evaluate_correction_upload_review(
            self.state,
            CorrectionReviewRequest(
                action=CorrectionReviewAction.OFFICIAL_UPLOAD,
                session_id="devhub-session-OTHER",
                user_confirmation=self.confirmations["officialUpload"],
            ),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(CorrectionReviewDecision.REFUSE_MISSING_EXACT_CONFIRMATION, result.decision)
        self.assertEqual((), result.executed_browser_actions)


if __name__ == "__main__":
    unittest.main()
