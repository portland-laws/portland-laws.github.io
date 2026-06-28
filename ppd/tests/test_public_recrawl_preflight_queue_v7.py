from __future__ import annotations

import importlib.util
from pathlib import Path

from ppd.crawler.public_recrawl_preflight_queue_v7 import (
    assert_valid_public_recrawl_preflight_queue_v7,
    validate_public_recrawl_preflight_queue_v7,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_recrawl_preflight_queue_v7"
    / "valid_queue.py"
)


def _load_valid_rows() -> list[dict[str, object]]:
    spec = importlib.util.spec_from_file_location("valid_queue_fixture", FIXTURE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return [dict(row) for row in module.VALID_PUBLIC_RECRAWL_PREFLIGHT_QUEUE_V7]


def _single_row_with(**updates: object) -> list[dict[str, object]]:
    rows = _load_valid_rows()
    rows[0].update(updates)
    return rows


def test_valid_queue_fixture_passes() -> None:
    result = validate_public_recrawl_preflight_queue_v7(_load_valid_rows())

    assert result.ok is True
    assert result.issues == ()
    assert_valid_public_recrawl_preflight_queue_v7(_load_valid_rows())


def test_rejects_missing_authorization_packet_reference() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(authorization_packet_ref="")
    )

    assert result.ok is False
    assert {issue.code for issue in result.issues} == {"missing_preflight_reference"}
    assert result.issues[0].field == "authorization_packet_ref"


def test_rejects_missing_allowlist_and_robots_policy_fixture_references() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(allowlist_fixture_ref="", robots_policy_fixture_ref=None)
    )

    assert result.ok is False
    assert [issue.field for issue in result.issues] == [
        "allowlist_fixture_ref",
        "robots_policy_fixture_ref",
    ]


def test_rejects_missing_canonical_redirect_skip_host_rate_and_handoff_rows() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(
            canonical_url_queue_row_ref="",
            redirect_expectation_ref="",
            skip_reason_row_ref="",
            host_policy_decision_ref="",
            rate_limit_reminder_ref="",
            processor_handoff_eligibility_note="",
        )
    )

    assert result.ok is False
    assert {issue.field for issue in result.issues} == {
        "canonical_url_queue_row_ref",
        "redirect_expectation_ref",
        "skip_reason_row_ref",
        "host_policy_decision_ref",
        "rate_limit_reminder_ref",
        "processor_handoff_eligibility_note",
    }


def test_rejects_missing_validation_commands() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(validation_commands=[])
    )

    assert result.ok is False
    assert any(issue.code == "missing_validation_commands" for issue in result.issues)


def test_rejects_live_crawl_execution_claims() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(
            execution_status="completed",
            notes="Live crawl completed and fetched live content.",
            processor_handoff_eligibility_note="Eligible only after validation.",
        )
    )

    assert result.ok is False
    assert any(issue.code == "live_crawl_execution_claim" for issue in result.issues)


def test_rejects_downloaded_raw_private_session_and_auth_artifacts() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(
            downloaded_artifact_ref="downloads/page.html",
            raw_crawl_artifact_ref="raw/body.html",
            private_session_ref="state.json",
            auth_artifact_ref="cookies.json",
        )
    )

    assert result.ok is False
    assert [issue.code for issue in result.issues] == [
        "forbidden_artifact_reference",
        "forbidden_artifact_reference",
        "forbidden_artifact_reference",
        "forbidden_artifact_reference",
    ]


def test_rejects_official_action_completion_claims() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(
            notes="Permit submitted after the recrawl preflight.",
            processor_handoff_eligibility_note="Eligible only after validation.",
        )
    )

    assert result.ok is False
    assert any(
        issue.code == "official_action_completion_claim" for issue in result.issues
    )


def test_rejects_legal_or_permitting_guarantees() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(
            notes="This queue proves the permit will be approved.",
            processor_handoff_eligibility_note="Eligible only after validation.",
        )
    )

    assert result.ok is False
    assert any(issue.code == "legal_or_permitting_guarantee" for issue in result.issues)


def test_rejects_active_mutation_flags() -> None:
    result = validate_public_recrawl_preflight_queue_v7(
        _single_row_with(active_mutation=True, upload_enabled=True)
    )

    assert result.ok is False
    assert [issue.code for issue in result.issues] == [
        "active_mutation_flag",
        "active_mutation_flag",
    ]
