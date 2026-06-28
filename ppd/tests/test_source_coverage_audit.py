from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.source_coverage_audit import (
    finding_codes,
    require_valid_source_coverage_audit_packet,
    validate_source_coverage_audit_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_coverage_audit"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_source_coverage_audit_packet_has_no_findings() -> None:
    packet = _load_fixture("valid_packet.json")

    findings = validate_source_coverage_audit_packet(packet)

    assert findings == []
    require_valid_source_coverage_audit_packet(packet)


def test_invalid_source_coverage_audit_packet_reports_required_guardrails() -> None:
    packet = _load_fixture("invalid_packet.json")

    codes = finding_codes(validate_source_coverage_audit_packet(packet))

    assert {
        "missing_official_anchor",
        "uncited_downstream_link",
        "private_or_authenticated_url",
        "outside_allowlist_host",
        "raw_body_or_download_path",
        "missing_skipped_reason_code",
        "complete_without_human_review",
    }.issubset(codes)


def test_invalid_source_coverage_audit_packet_can_be_rejected() -> None:
    packet = _load_fixture("invalid_packet.json")

    with pytest.raises(ValueError, match="invalid source coverage audit packet"):
        require_valid_source_coverage_audit_packet(packet)
