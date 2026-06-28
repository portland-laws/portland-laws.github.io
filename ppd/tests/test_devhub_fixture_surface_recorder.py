from pathlib import Path

from ppd.devhub.fixture_surface_recorder import (
    CONSEQUENTIAL,
    FINANCIAL,
    READ_ONLY,
    record_devhub_fixture_surface,
)


def test_fixture_surface_recorder_captures_redacted_status_review_surface() -> None:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "devhub"
        / "synthetic_permit_details_status_review.html"
    )
    recording = record_devhub_fixture_surface(fixture_path.read_text(encoding="utf-8"))

    assert recording.surface_id == "devhub-permit-details-status-review"
    assert "Permit details for [REDACTED_PERMIT]" in recording.headings
    assert "Status review" in recording.headings
    assert "Project roles" in recording.headings
    assert "Attachments" in recording.headings
    assert "main" in recording.roles
    assert "navigation" in recording.roles
    assert "status" in recording.roles
    assert "alert" in recording.roles
    assert "Correction response is required before review can continue." in recording.validation_messages
    assert "One required document is missing from the response package." in recording.validation_messages
    assert recording.attachment_labels == (
        "Plan set PDF",
        "Structural calculations PDF",
        "Correction response letter",
    )
    assert "Plan Review - Corrections Required" in recording.status_labels


def test_fixture_surface_recorder_classifies_high_risk_devhub_controls() -> None:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "devhub"
        / "synthetic_permit_details_status_review.html"
    )
    recording = record_devhub_fixture_surface(fixture_path.read_text(encoding="utf-8"))
    actions = recording.actions_by_label()

    assert actions["View details"].classification == READ_ONLY
    assert actions["Download status summary"].classification == READ_ONLY
    assert actions["Upload corrections"].classification == CONSEQUENTIAL
    assert actions["Upload response package"].classification == CONSEQUENTIAL
    assert actions["Schedule inspection"].classification == CONSEQUENTIAL
    assert actions["Submit application"].classification == CONSEQUENTIAL
    assert actions["Pay fees"].classification == FINANCIAL

    high_risk_labels = {
        label
        for label, action in actions.items()
        if action.classification in {CONSEQUENTIAL, FINANCIAL}
    }
    assert high_risk_labels == {
        "Upload corrections",
        "Upload response package",
        "Schedule inspection",
        "Submit application",
        "Pay fees",
    }
