from __future__ import annotations

from pathlib import Path

import pytest

from ppd.devhub.attended_pilot_evidence_template import (
    REQUIRED_TEMPLATE_ID,
    assert_valid_evidence_template,
    load_evidence_template,
    validate_evidence_template,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "attended_pilot_evidence_template.json"


def test_attended_pilot_evidence_template_fixture_is_valid() -> None:
    template = load_evidence_template(FIXTURE_PATH)

    result = validate_evidence_template(template)

    assert result.template_id == REQUIRED_TEMPLATE_ID
    assert result.ok is True
    assert result.errors == ()


def test_template_requires_redacted_heading_label_status_abort_and_journal_sections() -> None:
    template = load_evidence_template(FIXTURE_PATH)
    sections = template["evidence_sections"]

    assert "redacted_headings" in sections
    assert "redacted_labels" in sections
    assert "status_categories" in sections
    assert "abort_conditions" in sections
    assert "journal_event_ids" in sections
    assert_valid_evidence_template(template)


def test_template_rejects_claimed_live_session() -> None:
    template = load_evidence_template(FIXTURE_PATH)
    template["live_session_performed"] = True

    result = validate_evidence_template(template)

    assert result.ok is False
    assert "committed template must not claim a live session was performed" in result.errors


def test_template_rejects_missing_prohibited_artifact() -> None:
    template = load_evidence_template(FIXTURE_PATH)
    template["prohibited_artifacts"] = [
        artifact for artifact in template["prohibited_artifacts"] if artifact != "har_files"
    ]

    result = validate_evidence_template(template)

    assert result.ok is False
    assert any("har_files" in error for error in result.errors)


def test_template_rejects_private_values_in_examples() -> None:
    template = load_evidence_template(FIXTURE_PATH)
    template["blank_row_examples"]["redacted_heading_row"]["redacted_heading_text"] = "Applicant email person@example.test"

    result = validate_evidence_template(template)

    assert result.ok is False
    assert any("private value" in error for error in result.errors)


def test_assert_valid_evidence_template_raises_stable_error() -> None:
    template = load_evidence_template(FIXTURE_PATH)
    template["evidence_sections"]["status_categories"]["record_private_values"] = True

    with pytest.raises(AssertionError, match="status_categories must not record private values"):
        assert_valid_evidence_template(template)
