"""Fixture-only tests for PP&D guidance change-impact reporting."""

from __future__ import annotations

import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "change_impact"
    / "changed_guidance_snapshot.json"
)

EXPECTED_CHANGE_TYPES = {
    "file_naming_rule": {
        "requirement": "req-file-naming-sheet-prefix",
        "process": "process-building-plan-review",
        "guardrail": "guardrail-building-plan-review",
    },
    "required_document": {
        "requirement": "req-doc-structural-calculations",
        "process": "process-building-plan-review",
        "guardrail": "guardrail-building-plan-review",
    },
    "fee_trigger": {
        "requirement": "req-fee-intake-payment-trigger",
        "process": "process-building-plan-review",
        "guardrail": "guardrail-fee-payment",
    },
    "deadline": {
        "requirement": "req-deadline-correction-response",
        "process": "process-corrections-upload",
        "guardrail": "guardrail-corrections-upload",
    },
    "devhub_action_guidance": {
        "requirement": "req-action-gate-certify-submit",
        "process": "process-building-plan-review",
        "guardrail": "guardrail-devhub-consequential-actions",
    },
}


def _load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_change_impact_fixture_is_deterministic_and_public_only() -> None:
    fixture = _load_fixture()
    snapshot = fixture["source_snapshot"]

    assert fixture["fixture_id"] == "ppd-change-impact-guidance-2026-05-12"
    assert snapshot["captured_at"] == "2026-05-12T00:00:00Z"
    assert snapshot["live_crawl_performed"] is False
    assert snapshot["authenticated_session_used"] is False
    assert all(source_id.startswith("src-ppd-") for source_id in snapshot["source_ids"])


def test_changed_guidance_categories_identify_affected_ids() -> None:
    fixture = _load_fixture()
    changes_by_type = {change["change_type"]: change for change in fixture["changes"]}

    assert set(changes_by_type) == set(EXPECTED_CHANGE_TYPES)

    for change_type, expected_ids in EXPECTED_CHANGE_TYPES.items():
        change = changes_by_type[change_type]

        assert change["change_id"].startswith("chg-")
        assert change["source_id"].startswith("src-ppd-")
        assert change["changed_guidance"].strip()
        assert expected_ids["requirement"] in change["affected_requirement_ids"]
        assert expected_ids["process"] in change["affected_process_model_ids"]
        assert expected_ids["guardrail"] in change["affected_guardrail_bundle_ids"]
        assert change["affected_requirement_ids"]
        assert change["affected_process_model_ids"]
        assert change["affected_guardrail_bundle_ids"]


def test_consequential_and_financial_changes_route_to_specific_guardrails() -> None:
    fixture = _load_fixture()
    changes_by_id = {change["change_id"]: change for change in fixture["changes"]}

    fee_change = changes_by_id["chg-fee-payment-before-review"]
    assert "guardrail-fee-payment" in fee_change["affected_guardrail_bundle_ids"]

    devhub_change = changes_by_id["chg-devhub-certify-submit"]
    assert "guardrail-devhub-consequential-actions" in devhub_change[
        "affected_guardrail_bundle_ids"
    ]
    assert "exact action-specific confirmation" in devhub_change["changed_guidance"]
