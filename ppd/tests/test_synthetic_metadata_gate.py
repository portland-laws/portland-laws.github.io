from __future__ import annotations

from ppd.devhub.synthetic_metadata_gate import (
    DocumentAction,
    SyntheticDocumentMetadata,
    validate_synthetic_document_action,
    validate_synthetic_document_set_action,
)


def test_noncompliant_synthetic_document_blocks_upload_staging() -> None:
    metadata = SyntheticDocumentMetadata(
        document_id="site-plan-draft",
        is_synthetic=True,
        compliance_status="noncompliant",
        provenance="local fixture",
        source_evidence_ids=("fixture-source",),
    )

    decision = validate_synthetic_document_action(metadata, DocumentAction.UPLOAD_STAGING)

    assert decision.allowed is False
    assert decision.blocked_document_ids == ("site-plan-draft",)
    assert "synthetic metadata status is noncompliant" in decision.reasons
    assert decision.requires_missing_information_prompt is True


def test_noncompliant_synthetic_document_blocks_certification_and_submission() -> None:
    metadata = {
        "document_id": "generated-application",
        "is_synthetic": True,
        "compliance_status": "unverified",
        "provenance": "fixture generator",
        "source_evidence_ids": ["source-a"],
    }

    certification = validate_synthetic_document_action(metadata, "certification")
    submission = validate_synthetic_document_action(metadata, "submission")

    assert certification.allowed is False
    assert certification.blocked_document_ids == ("generated-application",)
    assert submission.allowed is False
    assert submission.blocked_document_ids == ("generated-application",)


def test_noncompliant_synthetic_document_still_allows_preview_and_missing_information_prompt() -> None:
    metadata = SyntheticDocumentMetadata(
        document_id="draft-calculation",
        is_synthetic=True,
        compliance_status="missing_provenance",
    )

    preview = validate_synthetic_document_action(metadata, DocumentAction.LOCAL_PREVIEW)
    prompt = validate_synthetic_document_action(metadata, DocumentAction.MISSING_INFORMATION_PROMPT)

    assert preview.allowed is True
    assert prompt.allowed is True
    assert preview.blocked_document_ids == ()
    assert prompt.blocked_document_ids == ()


def test_compliant_synthetic_document_allows_consequential_actions() -> None:
    metadata = SyntheticDocumentMetadata(
        document_id="reviewed-plan",
        is_synthetic=True,
        compliance_status="human_verified",
        provenance="review packet 2026-05-14",
        source_evidence_ids=("source-1", "source-2"),
        human_review_status="approved",
    )

    decision = validate_synthetic_document_action(metadata, DocumentAction.UPLOAD_STAGING)

    assert decision.allowed is True
    assert decision.blocked_document_ids == ()


def test_non_synthetic_document_is_not_blocked_by_synthetic_metadata_gate() -> None:
    metadata = SyntheticDocumentMetadata(
        document_id="owner-supplied-plan",
        is_synthetic=False,
        compliance_status="unknown",
    )

    decision = validate_synthetic_document_action(metadata, DocumentAction.SUBMISSION)

    assert decision.allowed is True


def test_document_set_blocks_only_consequential_action_when_any_synthetic_metadata_is_noncompliant() -> None:
    documents = [
        {
            "document_id": "owner-plan",
            "is_synthetic": False,
        },
        {
            "document_id": "generated-structural-note",
            "is_synthetic": True,
            "compliance_status": "compliant",
            "provenance": "fixture generator",
            "source_evidence_ids": [],
        },
    ]

    decision = validate_synthetic_document_set_action(documents, DocumentAction.SUBMISSION)

    assert decision.allowed is False
    assert decision.blocked_document_ids == ("generated-structural-note",)
    assert "synthetic metadata is missing source evidence" in decision.reasons
