"""Fixture tests for public crawl frontier checkpoint validation."""

from __future__ import annotations

import json
from pathlib import Path

from ppd.contracts.frontier_checkpoint import (
    assert_valid_frontier_checkpoint_fixture,
    validate_frontier_checkpoint_fixture,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "crawl_frontier_checkpoint"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_public_frontier_checkpoint_fixture_is_valid() -> None:
    fixture = _load_fixture("public_frontier_checkpoint.valid.json")
    assert_valid_frontier_checkpoint_fixture(fixture)


def test_public_frontier_checkpoint_rejection_cases_are_rejected() -> None:
    cases_fixture = _load_fixture("public_frontier_checkpoint.rejection_cases.json")
    cases = cases_fixture["cases"]
    assert cases

    for case in cases:
        findings = validate_frontier_checkpoint_fixture(case["fixture"])
        reasons = " | ".join(finding.reason for finding in findings)
        assert findings, f"{case['case_id']} should be rejected"
        assert case["expected_reason_contains"] in reasons, reasons


if __name__ == "__main__":
    test_public_frontier_checkpoint_fixture_is_valid()
    test_public_frontier_checkpoint_rejection_cases_are_rejected()
