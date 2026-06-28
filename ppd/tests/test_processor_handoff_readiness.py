import json
from pathlib import Path

import pytest

from ppd.crawler.processor_handoff_readiness import (
    require_processor_handoff_readiness,
    validate_processor_handoff_readiness,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "processor_handoff_readiness_packets.json"
)

EXPECTED_CODES = {
    "missing_prerequisite_links": "MISSING_PREREQUISITE_LINKS",
    "private_authenticated_target": "PRIVATE_OR_AUTHENTICATED_TARGET",
    "non_allowlisted_target": "NON_ALLOWLISTED_TARGET",
    "raw_download_reference": "RAW_REFERENCE_PRESENT",
    "live_processor_execution_flag": "LIVE_PROCESSOR_EXECUTION_FLAG",
    "missing_no_raw_body_attestation": "MISSING_NO_RAW_BODY_ATTESTATION",
    "missing_skipped_target_reason": "MISSING_SKIPPED_TARGET_REASON",
    "archive_artifact_claim": "ARCHIVE_ARTIFACT_CLAIM",
}


def _fixtures():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_public_readiness_packet_passes():
    packet = _fixtures()["valid_minimal"]

    result = validate_processor_handoff_readiness(packet)

    assert result.ok is True
    assert result.issues == ()
    require_processor_handoff_readiness(packet)


@pytest.mark.parametrize("case_name, expected_code", sorted(EXPECTED_CODES.items()))
def test_invalid_readiness_packets_report_policy_issue(case_name, expected_code):
    packet = _fixtures()["invalid_cases"][case_name]

    result = validate_processor_handoff_readiness(packet)

    assert result.ok is False
    assert expected_code in {issue.code for issue in result.issues}
    with pytest.raises(ValueError, match=expected_code):
        require_processor_handoff_readiness(packet)


def test_nested_forbidden_fields_are_rejected():
    packet = {
        "prerequisite_links": ["https://www.portland.gov/ppd"],
        "targets": ["https://www.portland.gov/ppd/devhub-faqs"],
        "attestations": {"no_raw_body_persisted": True},
        "processor": {
            "options": {
                "live_processor_execution": True,
                "archive_artifacts": ["warc-placeholder"],
            }
        },
    }

    result = validate_processor_handoff_readiness(packet)

    assert result.ok is False
    assert "LIVE_PROCESSOR_EXECUTION_FLAG" in {issue.code for issue in result.issues}
    assert "ARCHIVE_ARTIFACT_CLAIM" in {issue.code for issue in result.issues}
