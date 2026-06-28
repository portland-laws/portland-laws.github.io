from pathlib import Path

from ppd.draft_assistance import (
    DraftAssistanceRequest,
    FieldManifest,
    PdfPreview,
    build_draft_assistance_plan,
)


def test_draft_assistance_redacts_and_refuses_execution_actions() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "draft_assistance"
    preview = PdfPreview.from_local_path(fixture_dir / "local_pdf_preview.txt")
    manifest = FieldManifest(
        source="devhub-fixture",
        fields=("project_address", "applicant_email", "permit_type"),
        required=("project_address", "permit_type"),
    )
    request = DraftAssistanceRequest(
        user_facts={
            "project_address": "1120 SW 5th Ave",
            "applicant_email": "planner@example.test",
            "password": "do-not-keep",
        },
        manifests=(manifest,),
        pdf_previews=(preview,),
        requested_actions=("draft", "save_for_later", "upload", "submit", "payment"),
    )

    plan = build_draft_assistance_plan(request)

    assert plan.redacted_facts["password"] == "[REDACTED]"
    assert plan.field_sources["permit_type"] == "devhub-fixture"
    assert plan.missing_required_fields == ("permit_type",)
    assert plan.pdf_previews[0].exists is True
    assert plan.allowed_actions == ("draft", "save_for_later")
    assert plan.refused_actions == ("payment", "submit", "upload")
    assert plan.attended_save_for_later is True
    assert plan.reversible is True


def test_unknown_actions_are_refused_by_default() -> None:
    request = DraftAssistanceRequest(
        user_facts={"project_address": "1900 SW 4th Ave"},
        manifests=(FieldManifest(source="fixture", fields=("project_address",), required=()),),
        requested_actions=("inspection", "cancel", "unexpected_live_action"),
    )

    plan = build_draft_assistance_plan(request)

    assert plan.allowed_actions == ()
    assert plan.refused_actions == ("cancel", "inspection", "unexpected_live_action")
    assert plan.attended_save_for_later is False
