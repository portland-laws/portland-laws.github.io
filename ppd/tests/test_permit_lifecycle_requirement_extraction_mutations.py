import copy
import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "lifecycle"
    / "permit_lifecycle_requirement_extraction_expected_output.json"
)


REQUIRED_RECORD_FIELDS = {
    "categoryId",
    "categoryLabel",
    "requirementType",
    "subject",
    "action",
    "object",
    "conditions",
    "deadlineOrTemporalScope",
    "classification",
    "stopGate",
    "sourceEvidenceIds",
    "evidence",
    "confidence",
    "formalizationStatus",
}


REQUIRED_EVIDENCE_FIELDS = {
    "evidenceId",
    "sourceUrl",
    "sourceTitle",
    "authorityLabel",
    "recrawlCadence",
    "supports",
    "redacted",
}


STRING_RECORD_FIELDS = (
    "categoryId",
    "categoryLabel",
    "requirementType",
    "subject",
    "action",
    "object",
    "deadlineOrTemporalScope",
    "classification",
    "formalizationStatus",
)


STRING_EVIDENCE_FIELDS = (
    "evidenceId",
    "sourceUrl",
    "sourceTitle",
    "authorityLabel",
    "recrawlCadence",
    "supports",
)


def load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def assert_non_empty_string(test_case, value, field_name):
    test_case.assertIsInstance(value, str, field_name)
    test_case.assertTrue(value.strip(), field_name)


def assert_string_list(test_case, value, field_name):
    test_case.assertIsInstance(value, list, field_name)
    test_case.assertTrue(value, field_name)
    for item in value:
        assert_non_empty_string(test_case, item, field_name)


def assert_valid_evidence(test_case, evidence_item):
    test_case.assertIsInstance(evidence_item, dict)
    test_case.assertTrue(REQUIRED_EVIDENCE_FIELDS.issubset(evidence_item.keys()))
    for field_name in STRING_EVIDENCE_FIELDS:
        assert_non_empty_string(test_case, evidence_item[field_name], field_name)
    test_case.assertIsInstance(evidence_item["redacted"], bool)


def assert_valid_category_record(test_case, record):
    test_case.assertIsInstance(record, dict)
    test_case.assertTrue(REQUIRED_RECORD_FIELDS.issubset(record.keys()))

    for field_name in STRING_RECORD_FIELDS:
        assert_non_empty_string(test_case, record[field_name], field_name)

    assert_string_list(test_case, record["conditions"], "conditions")
    assert_string_list(test_case, record["sourceEvidenceIds"], "sourceEvidenceIds")

    test_case.assertIsInstance(record["stopGate"], bool)
    confidence = record["confidence"]
    if not isinstance(confidence, (int, float)):
        raise AssertionError("confidence must be a number")
    if confidence > 1:
        raise AssertionError("confidence must be less than or equal to 1")
    if confidence < 0:
        raise AssertionError("confidence must be greater than or equal to 0")

    evidence = record["evidence"]
    test_case.assertIsInstance(evidence, list)
    test_case.assertTrue(evidence)
    for evidence_item in evidence:
        assert_valid_evidence(test_case, evidence_item)

    evidence_ids = {evidence_item["evidenceId"] for evidence_item in evidence}
    for source_evidence_id in record["sourceEvidenceIds"]:
        test_case.assertIn(source_evidence_id, evidence_ids)


def requirement_key(record):
    return (
        record["categoryId"],
        record["action"],
        record["object"],
        tuple(record["sourceEvidenceIds"]),
    )


def assert_valid_fixture(test_case, fixture):
    test_case.assertIsInstance(fixture, dict)
    test_case.assertIn("categoryRecords", fixture)
    category_records = fixture["categoryRecords"]
    test_case.assertIsInstance(category_records, list)
    test_case.assertTrue(category_records)

    requirement_keys = set()
    for record in category_records:
        assert_valid_category_record(test_case, record)
        key = requirement_key(record)
        test_case.assertNotIn(key, requirement_keys)
        requirement_keys.add(key)


class PermitLifecycleRequirementExtractionMutationSkeletonTest(unittest.TestCase):
    def test_committed_category_records_fixture_matches_checkbox_24_schema(self):
        assert_valid_fixture(self, load_fixture())

    def test_missing_category_id_is_rejected(self):
        fixture = copy.deepcopy(load_fixture())
        del fixture["categoryRecords"][0]["categoryId"]

        with self.assertRaises(AssertionError):
            assert_valid_fixture(self, fixture)

    def test_missing_source_evidence_ids_is_rejected(self):
        fixture = copy.deepcopy(load_fixture())
        del fixture["categoryRecords"][0]["sourceEvidenceIds"]

        with self.assertRaises(AssertionError):
            assert_valid_fixture(self, fixture)

    def test_missing_local_evidence_id_is_rejected(self):
        fixture = copy.deepcopy(load_fixture())
        del fixture["categoryRecords"][0]["evidence"][0]["evidenceId"]

        with self.assertRaises(AssertionError):
            assert_valid_fixture(self, fixture)

    def test_out_of_range_confidence_is_rejected(self):
        fixture = copy.deepcopy(load_fixture())
        fixture["categoryRecords"][0]["confidence"] = 1.1

        with self.assertRaises(AssertionError):
            assert_valid_fixture(self, fixture)


if __name__ == "__main__":
    unittest.main()
