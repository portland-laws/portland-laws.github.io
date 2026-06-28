import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "human_review_requirements.json"
)

REQUIRED_REVIEW_REASON_CODES = {
    "low_confidence",
    "ocr_derived",
    "stale_source",
    "conflicting_evidence",
    "unsupported_path",
}


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_review_fixture_covers_all_required_escalation_reasons():
    fixture = load_fixture()

    observed_codes = set()
    for requirement in fixture["requirements"]:
        observed_codes.update(requirement["extraction_metadata"]["review_reason_codes"])

    assert REQUIRED_REVIEW_REASON_CODES.issubset(observed_codes)


def test_review_fixture_blocks_flagged_requirements_before_formalization():
    fixture = load_fixture()

    for requirement in fixture["requirements"]:
        reason_codes = requirement["extraction_metadata"]["review_reason_codes"]
        assert reason_codes, requirement["requirement_id"]
        assert requirement["human_review_status"] == "needs_human_review"
        assert requirement["formalization_status"] == "blocked_pending_review"
        assert requirement["source_evidence_ids"]
        assert requirement["confidence"] >= 0
        assert requirement["confidence"] <= 1


def test_review_reasons_match_machine_readable_codes():
    fixture = load_fixture()

    for requirement in fixture["requirements"]:
        metadata_codes = set(requirement["extraction_metadata"]["review_reason_codes"])
        review_reason_codes = {reason["code"] for reason in requirement["review_reasons"]}
        assert metadata_codes == review_reason_codes
        assert metadata_codes <= REQUIRED_REVIEW_REASON_CODES
