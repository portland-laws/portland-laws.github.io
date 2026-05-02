"""Fixture-only validation for public PP&D form-field extraction contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "forms"
    / "building_permit_application_field_contract.json"
)
REDACTED_PLACEHOLDER_RE = re.compile(r"^$")
FORBIDDEN_VALUE_FRAGMENTS = ("john", "jane", "@", "555-", "password", "token", "cookie")


class PublicFormFieldExtractionContractTest(unittest.TestCase):
    def test_fixture_records_required_labels_options_markers_and_source_anchors(self) -> None:
        fixture = _load_fixture()
        anchors = _anchor_ids(fixture)

        self.assertEqual(fixture["schemaVersion"], 1)
        self.assertEqual(fixture["contractType"], "ppd_public_form_field_extraction")
        self.assertTrue(fixture["fixtureOnly"])
        self.assertFalse(fixture["sourceDocument"]["capturedFromLiveSite"])
        self.assertFalse(fixture["sourceDocument"]["downloadedDocumentIncluded"])
        self.assertTrue(fixture["sourceDocument"]["sourceUrl"].startswith("https://www.portland.gov/ppd"))

        required_fields = fixture["requiredFields"]
        self.assertGreaterEqual(len(required_fields), 3)
        for field in required_fields:
            self.assertTrue(field["fieldId"].strip())
            self.assertTrue(field["label"].strip())
            self.assertTrue(field["required"])
            self.assertIn(field["fieldKind"], {"text", "textarea", "single_select", "multi_select", "checkbox"})
            _assert_redacted_placeholder(self, field["redactedPlaceholderValue"])
            _assert_known_source_anchors(self, field["sourceAnchorIds"], anchors)

        option_fields = [field for field in required_fields if field.get("enumeratedOptions")]
        self.assertTrue(option_fields, "at least one required field must record enumerated options")
        for field in option_fields:
            self.assertGreaterEqual(len(field["enumeratedOptions"]), 2)
            for option in field["enumeratedOptions"]:
                self.assertTrue(option["optionId"].strip())
                self.assertTrue(option["label"].strip())
                _assert_known_source_anchors(self, option["sourceAnchorIds"], anchors)

        markers = fixture["signatureOrAcknowledgementMarkers"]
        marker_kinds = {marker["markerKind"] for marker in markers}
        self.assertIn("signature", marker_kinds)
        self.assertIn("acknowledgement", marker_kinds)
        for marker in markers:
            self.assertTrue(marker["markerId"].strip())
            self.assertTrue(marker["label"].strip())
            self.assertTrue(marker["required"])
            _assert_redacted_placeholder(self, marker["redactedPlaceholderValue"])
            _assert_known_source_anchors(self, marker["sourceAnchorIds"], anchors)

    def test_fixture_contains_redacted_placeholder_values_only(self) -> None:
        fixture = _load_fixture()
        self.assertTrue(fixture["privacyPolicy"]["redactedValuesOnly"])

        placeholder_values = []
        placeholder_values.extend(field["redactedPlaceholderValue"] for field in fixture["requiredFields"])
        placeholder_values.extend(
            marker["redactedPlaceholderValue"]
            for marker in fixture["signatureOrAcknowledgementMarkers"]
        )

        self.assertTrue(placeholder_values)
        for value in placeholder_values:
            _assert_redacted_placeholder(self, value)
            lowered = value.lower()
            for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                self.assertNotIn(fragment, lowered)

        forbidden_artifacts = set(fixture["privacyPolicy"]["forbiddenArtifacts"])
        self.assertIn("private_devhub_session", forbidden_artifacts)
        self.assertIn("downloaded_document", forbidden_artifacts)
        self.assertIn("browser_trace", forbidden_artifacts)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError("form-field extraction fixture must be a JSON object")
    return data


def _anchor_ids(fixture: dict[str, Any]) -> set[str]:
    anchors = fixture["sourcePageAnchors"]
    if not anchors:
        raise AssertionError("fixture must define source page anchors")
    anchor_ids = {anchor["anchorId"] for anchor in anchors}
    if len(anchor_ids) != len(anchors):
        raise AssertionError("source page anchor IDs must be unique")
    for anchor in anchors:
        if not anchor["sourceUrl"].startswith("https://www.portland.gov/ppd"):
            raise AssertionError(f"unexpected non-PP&D source URL: {anchor['sourceUrl']}")
        if not anchor["sectionLabel"].strip():
            raise AssertionError(f"source anchor {anchor['anchorId']} is missing sectionLabel")
    return anchor_ids


def _assert_known_source_anchors(
    test_case: unittest.TestCase,
    source_anchor_ids: list[str],
    known_anchor_ids: set[str],
) -> None:
    test_case.assertTrue(source_anchor_ids)
    for source_anchor_id in source_anchor_ids:
        test_case.assertIn(source_anchor_id, known_anchor_ids)


def _assert_redacted_placeholder(test_case: unittest.TestCase, value: str) -> None:
    test_case.assertRegex(value, REDACTED_PLACEHOLDER_RE)


if __name__ == "__main__":
    unittest.main()
