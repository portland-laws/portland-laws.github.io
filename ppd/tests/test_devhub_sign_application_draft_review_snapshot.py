import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "sign_application_draft_review_snapshot.json"
REDACTED = "[REDACTED]"


class DevhubSignApplicationDraftReviewSnapshotTest(unittest.TestCase):
    def setUp(self):
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_uses_mocked_redacted_source_only(self):
        self.assertEqual("mocked_devhub_fixture", self.fixture["sourceKind"])
        policy = self.fixture["redactionPolicy"]
        self.assertEqual("redacted_fixture_only", policy["mode"])
        self.assertFalse(policy["containsLiveAccountData"])
        self.assertFalse(policy["containsRawCrawlOutput"])
        self.assertFalse(policy["containsDownloadedDocuments"])
        self._assert_no_forbidden_private_artifacts(self.fixture)
        self._assert_redacted_values_only(self.fixture)

    def test_records_semantic_selectors_for_draft_review_controls(self):
        selectors = {item["selectorId"]: item for item in self.fixture["semanticSelectors"]}
        expected_selector_ids = {
            "project-name-input",
            "site-address-input",
            "sign-type-select",
            "applicant-email-input",
            "plans-upload-control",
            "save-for-later-button",
            "continue-to-certify-button",
        }
        self.assertEqual(expected_selector_ids, set(selectors))

        for selector_id, selector in selectors.items():
            with self.subTest(selector_id=selector_id):
                self.assertTrue(selector["role"])
                self.assertTrue(selector["accessibleName"])
                self.assertTrue(selector["labelText"])
                self.assertTrue(selector["nearbyHeading"])
                self.assertEqual("draft_review", selector["stableUrlState"])
                self.assertIsNone(selector["fallbackCss"])

    def test_records_required_fields_and_validation_messages(self):
        fields = {field["fieldId"]: field for field in self.fixture["requiredFields"]}
        self.assertEqual({"project-name", "site-address", "sign-type", "applicant-email"}, set(fields))

        for field_id, field in fields.items():
            with self.subTest(field_id=field_id):
                self.assertTrue(field["required"])
                self.assertIn(field["valueState"], {"redacted_present", "redacted_missing"})
                self.assertEqual(REDACTED, field["redactedValue"])

        self.assertEqual("Site address is required before continuing.", fields["site-address"]["validationMessage"])
        self.assertEqual("Select a sign type.", fields["sign-type"]["validationMessage"])
        self.assertIsNone(fields["project-name"]["validationMessage"])

        messages = {message["messageId"]: message for message in self.fixture["validationMessages"]}
        self.assertTrue(messages["missing-site-address"]["blocksContinue"])
        self.assertTrue(messages["missing-sign-type"]["blocksContinue"])
        self.assertTrue(messages["missing-sign-plans"]["blocksContinue"])
        self.assertFalse(messages["draft-saved"]["blocksContinue"])

    def test_records_upload_controls_without_files(self):
        uploads = {upload["uploadId"]: upload for upload in self.fixture["uploadControls"]}
        self.assertEqual({"sign-plans-upload", "owner-authorization-upload"}, set(uploads))

        required_upload = uploads["sign-plans-upload"]
        self.assertTrue(required_upload["required"])
        self.assertEqual(["pdf"], required_upload["acceptedFileHints"])
        self.assertEqual("none_attached", required_upload["currentFileState"])
        self.assertEqual(REDACTED, required_upload["redactedFileName"])
        self.assertEqual("Attach the required sign plans PDF before continuing.", required_upload["validationMessage"])

        optional_upload = uploads["owner-authorization-upload"]
        self.assertFalse(optional_upload["required"])
        self.assertEqual("redacted_attached", optional_upload["currentFileState"])
        self.assertEqual(REDACTED, optional_upload["redactedFileName"])

    def test_records_save_for_later_state_and_navigation_edges(self):
        save_state = self.fixture["saveForLaterState"]
        self.assertTrue(save_state["available"])
        self.assertEqual("save-for-later-button", save_state["selectorId"])
        self.assertEqual("unsaved_changes_present", save_state["stateBeforeClick"])
        self.assertEqual("draft_saved", save_state["stateAfterClick"])
        self.assertEqual("draft_review_resume", save_state["resumeStateId"])

        edges = {edge["edgeId"]: edge for edge in self.fixture["navigationEdges"]}
        self.assertEqual("reversible_draft_edit", edges["save-for-later"]["actionClassification"])
        self.assertFalse(edges["save-for-later"]["requiresExactConfirmation"])
        self.assertEqual("potentially_consequential", edges["continue-to-certification"]["actionClassification"])
        self.assertTrue(edges["continue-to-certification"]["requiresExactConfirmation"])
        self.assertTrue(edges["submit-sign-application"]["requiresExactConfirmation"])

    def test_records_exact_confirmation_gates(self):
        gates = {gate["gateId"]: gate for gate in self.fixture["confirmationGates"]}
        self.assertEqual(
            {"continue-to-certification-gate", "submit-sign-application-gate", "official-upload-gate"},
            set(gates),
        )

        for gate_id, gate in gates.items():
            with self.subTest(gate_id=gate_id):
                self.assertEqual("potentially_consequential", gate["classification"])
                self.assertFalse(gate["allowedWithoutConfirmation"])
                self.assertTrue(gate["previewRequired"])
                self.assertTrue(gate["exactConfirmationRequired"].startswith("I confirm I want to "))
                self.assertIn("redacted", gate["exactConfirmationRequired"].lower())
                self.assertTrue(gate["stopReason"])

        self.assertIn("submit", gates["submit-sign-application-gate"]["exactConfirmationRequired"])
        self.assertIn("attach", gates["official-upload-gate"]["exactConfirmationRequired"])

    def _assert_no_forbidden_private_artifacts(self, value):
        forbidden_fragments = (
            "storage_state",
            "storage-state",
            "auth_state",
            "auth-state",
            "password",
            "credential",
            "secret",
            "token=",
            "cookie",
            "captcha",
            "mfa",
            "trace.zip",
            ".har",
            ".png",
            ".jpg",
            ".jpeg",
            ".webm",
            "ppd/data/private",
            "raw_crawl_output",
            "downloaded_private_document",
        )
        for path, leaf in self._walk(value):
            if isinstance(leaf, str):
                lowered = leaf.lower()
                for fragment in forbidden_fragments:
                    self.assertNotIn(fragment, lowered, f"{path} contains forbidden fragment {fragment}")
                if lowered.startswith("http"):
                    parsed = urlparse(leaf)
                    self.assertEqual("https", parsed.scheme)
                    self.assertEqual("devhub.portlandoregon.gov", parsed.netloc)
                    self.assertTrue(parsed.path.startswith("/mock/"))

    def _assert_redacted_values_only(self, value):
        for path, leaf in self._walk(value):
            if not isinstance(leaf, str):
                continue
            if path.endswith("redactedValue") or path.endswith("redactedFileName"):
                self.assertEqual(REDACTED, leaf)
            self.assertIsNone(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}", leaf, re.IGNORECASE), path)
            self.assertIsNone(re.search(r"\\b\\d{3,6}\\s+[A-Za-z0-9 .'-]+\\b", leaf), path)

    def _walk(self, value, path="root"):
        if isinstance(value, dict):
            for key, child in value.items():
                yield from self._walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from self._walk(child, f"{path}[{index}]")
        else:
            yield path, value


if __name__ == "__main__":
    unittest.main()
