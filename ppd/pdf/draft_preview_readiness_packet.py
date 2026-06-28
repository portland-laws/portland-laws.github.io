"""Fixture-first reversible PDF draft preview readiness packets.

The builder consumes already-committed synthetic helper outputs:
file-preparation compliance metadata, safe-next-action user handoff checklists,
and missing-information prompt regression corpora. It never reads PDF binaries,
private files, DevHub session state, browser traces, or downloaded documents, and
it never produces filled documents.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.file_preparation_compliance import (
    SyntheticDocumentMetadata,
    evaluate_metadata,
    load_metadata_fixture,
)
from ppd.logic.missing_information_prompt_corpus import (
    validate_prompt_corpus,
)
from ppd.user_handoff_checklist import validate_user_handoff_checklist_packet


PACKET_TYPE = "ppd.pdf.draft_preview_readiness_packet.v1"
FORBIDDEN_KEYS = frozenset(
    {
        "auth_state",
        "browser_state",
        "cookies",
        "credential",
        "credentials",
        "download_path",
        "download_url",
        "downloaded_document",
        "filled_document",
        "filled_pdf",
        "har",
        "local_pdf_path",
        "password",
        "payment_details",
        "pdf_base64",
        "pdf_binary",
        "pdf_bytes",
        "private_file",
        "raw_crawl_output",
        "raw_html",
        "raw_pdf",
        "screenshot",
        "session_cookie",
        "storage_state",
        "token",
        "trace",
        "upload_payload",
    }
)
PRIVATE_OR_BINARY_TEXT = re.compile(
    r"(%PDF-|file://|/home/|/Users/|C:\\\\Users\\|trace\.zip|\.har\b|storage[-_ ]?state|session[-_ ]?cookie|raw[-_ ]?pdf|filled[-_ ]?pdf)",
    re.IGNORECASE,
)
CONSEQUENTIAL_ACTIONS = frozenset({"upload", "submit", "certify", "payment", "pay", "schedule", "cancel"})


class DraftPreviewReadinessPacketError(ValueError):
    """Raised when a PDF draft preview readiness packet is unsafe."""


def load_json_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed JSON fixture object without following external refs."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DraftPreviewReadinessPacketError("fixture must be a JSON object")
    return payload


def build_fixture_first_draft_preview_readiness_packet(
    document_metadata: Sequence[SyntheticDocumentMetadata],
    handoff_checklist: Mapping[str, Any],
    prompt_corpus: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a reversible, local-preview-only readiness packet.

    Inputs must already be synthetic fixture outputs. The packet contains only
    metadata, prompts, notices, checkpoints, and attestations.
    """

    document_findings = evaluate_metadata(document_metadata)
    handoff_errors = validate_user_handoff_checklist_packet(handoff_checklist)
    corpus_result = validate_prompt_corpus(prompt_corpus)

    if document_findings:
        detail = "; ".join(f"{finding.code}: {finding.message}" for finding in document_findings)
        raise DraftPreviewReadinessPacketError(f"document metadata is not preview-safe: {detail}")
    if handoff_errors:
        raise DraftPreviewReadinessPacketError("handoff checklist is not valid: " + "; ".join(handoff_errors))
    if corpus_result.errors:
        raise DraftPreviewReadinessPacketError("prompt corpus is not valid: " + "; ".join(corpus_result.errors))

    cases = _document_cases(document_metadata)
    missing_fact_prompts = _required_missing_fact_prompts(prompt_corpus)
    notices = _local_preview_only_notices(handoff_checklist, prompt_corpus)
    checkpoints = _reviewer_checkpoints(handoff_checklist)
    attestations = _upload_blocking_attestations(handoff_checklist, cases)

    packet = {
        "packet_id": "ppd-pdf-draft-preview-readiness-packet-synthetic-v1",
        "packet_type": PACKET_TYPE,
        "mode": "fixture_first_reversible_pdf_draft_preview_readiness",
        "fixture_first": True,
        "offline_only": True,
        "synthetic_only": True,
        "reads_private_pdfs": False,
        "reads_pdf_binary": False,
        "produces_filled_documents": False,
        "writes_pdf_binary": False,
        "launches_devhub": False,
        "network_requests_made": False,
        "preview_scope": "local_preview_only_metadata_packet",
        "readiness_status": "blocked_until_missing_facts_and_reviewer_checkpoints_clear",
        "source_packets": {
            "file_preparation_compliance": {
                "consumed": True,
                "document_count": len(cases),
                "finding_count": 0,
            },
            "safe_next_action_user_handoff_checklist": {
                "consumed": True,
                "packet_id": _text(handoff_checklist.get("packet_id")),
                "packet_type": _text(handoff_checklist.get("packet_type")),
            },
            "missing_information_prompt_regression_corpus": {
                "consumed": True,
                "corpus_id": _text(prompt_corpus.get("corpus_id")),
                "case_count": corpus_result.case_count,
                "prompt_categories": sorted(corpus_result.prompt_categories),
            },
        },
        "synthetic_document_metadata_cases": cases,
        "required_missing_fact_prompts": missing_fact_prompts,
        "local_preview_only_notices": notices,
        "reviewer_checkpoints": checkpoints,
        "upload_blocking_attestations": attestations,
        "output_attestations": {
            "metadata_only": True,
            "local_preview_only": True,
            "reversible": True,
            "official_submission_ready": False,
            "filled_document_created": False,
            "upload_staging_created": False,
            "private_pdf_read": False,
            "pdf_binary_written": False,
        },
    }
    assert_valid_fixture_first_draft_preview_readiness_packet(packet)
    return packet


def build_fixture_first_draft_preview_readiness_packet_from_paths(
    document_metadata_path: str | Path,
    handoff_checklist_path: str | Path,
    prompt_corpus_path: str | Path,
) -> dict[str, Any]:
    """Build a readiness packet from committed PP&D fixture paths."""

    return build_fixture_first_draft_preview_readiness_packet(
        load_metadata_fixture(Path(document_metadata_path)),
        load_json_fixture(handoff_checklist_path),
        load_json_fixture(prompt_corpus_path),
    )


def validate_fixture_first_draft_preview_readiness_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    """Return deterministic safety errors for a readiness packet."""

    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    for field in ("fixture_first", "offline_only", "synthetic_only"):
        if packet.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "reads_private_pdfs",
        "reads_pdf_binary",
        "produces_filled_documents",
        "writes_pdf_binary",
        "launches_devhub",
        "network_requests_made",
    ):
        if packet.get(field) is not False:
            errors.append(f"{field} must be false")

    _validate_source_packets(errors, packet.get("source_packets"))
    _validate_document_cases(errors, packet.get("synthetic_document_metadata_cases"))
    _validate_required_prompts(errors, packet.get("required_missing_fact_prompts"))
    _validate_local_preview_notices(errors, packet.get("local_preview_only_notices"))
    _validate_reviewer_checkpoints(errors, packet.get("reviewer_checkpoints"))
    _validate_upload_attestations(errors, packet.get("upload_blocking_attestations"))
    _validate_output_attestations(errors, packet.get("output_attestations"))
    _validate_no_forbidden_content(errors, packet)
    return tuple(dict.fromkeys(errors))


def assert_valid_fixture_first_draft_preview_readiness_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_fixture_first_draft_preview_readiness_packet(packet)
    if errors:
        raise DraftPreviewReadinessPacketError("; ".join(errors))


def _document_cases(records: Sequence[SyntheticDocumentMetadata]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for record in records:
        cases.append(
            {
                "case_id": f"document-metadata:{record.document_id}",
                "document_id": record.document_id,
                "title": record.title,
                "media_type": record.media_type,
                "synthetic": record.synthetic,
                "downloaded": record.downloaded,
                "private": record.private,
                "upload_staging": record.upload_staging,
                "raw_pdf_persisted": record.raw_pdf_persisted,
                "compliance_status": "metadata_only_preview_safe",
                "preview_readiness": "eligible_for_local_metadata_preview",
            }
        )
    return cases


def _required_missing_fact_prompts(corpus: Mapping[str, Any]) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    for case in _sequence(corpus.get("synthetic_user_cases")):
        case_map = _mapping(case)
        for prompt in _sequence(case_map.get("expected_prompts")):
            prompt_map = _mapping(prompt)
            category = _text(prompt_map.get("category"))
            if category not in {"missing_fact_question", "stale_evidence_prompt", "manual_handoff_prompt"}:
                continue
            prompts.append(
                {
                    "case_id": _text(case_map.get("case_id")),
                    "category": category,
                    "prompt": _text(prompt_map.get("text")),
                    "required_before_preview_completion": True,
                    "required_before_official_action": True,
                    "citations": _citations(prompt_map.get("citations")),
                }
            )
    return prompts


def _local_preview_only_notices(handoff_checklist: Mapping[str, Any], corpus: Mapping[str, Any]) -> list[dict[str, Any]]:
    notices: list[dict[str, Any]] = []
    for preview in _sequence(handoff_checklist.get("allowed_reversible_local_previews")):
        preview_map = _mapping(preview)
        notices.append(
            {
                "notice_id": _text(preview_map.get("preview_id")),
                "notice": _text(preview_map.get("description")),
                "local_only": preview_map.get("local_only") is True,
                "reversible": preview_map.get("reversible") is True,
                "official_action_allowed": False,
                "citations": _text_list(preview_map.get("citations")),
            }
        )
    for case in _sequence(corpus.get("synthetic_user_cases")):
        case_map = _mapping(case)
        for prompt in _sequence(case_map.get("expected_prompts")):
            prompt_map = _mapping(prompt)
            if prompt_map.get("category") == "local_preview_only_expectation":
                notices.append(
                    {
                        "notice_id": f"local-preview-only:{_text(case_map.get('case_id'))}",
                        "notice": _text(prompt_map.get("text")),
                        "local_only": True,
                        "reversible": True,
                        "official_action_allowed": False,
                        "citations": _citations(prompt_map.get("citations")),
                    }
                )
    return notices


def _reviewer_checkpoints(handoff_checklist: Mapping[str, Any]) -> list[dict[str, Any]]:
    checkpoints: list[dict[str, Any]] = []
    for checkpoint in _sequence(handoff_checklist.get("reviewer_prompts")):
        checkpoint_map = _mapping(checkpoint)
        checkpoints.append(
            {
                "checkpoint_id": _text(checkpoint_map.get("prompt_id")),
                "reviewer_role": _text(checkpoint_map.get("reviewer_role")),
                "question": _text(checkpoint_map.get("question")),
                "requires_reviewer": checkpoint_map.get("requires_reviewer") is True,
                "must_clear_before_upload": True,
                "citations": _text_list(checkpoint_map.get("citations")),
            }
        )
    return checkpoints


def _upload_blocking_attestations(
    handoff_checklist: Mapping[str, Any], document_cases: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    attestations: list[dict[str, Any]] = []
    for action in _sequence(handoff_checklist.get("blocked_consequential_actions")):
        action_map = _mapping(action)
        action_id = _text(action_map.get("action_id"))
        if not action_id:
            continue
        attestations.append(
            {
                "attestation_id": f"blocked-action:{action_id}",
                "action_id": action_id,
                "blocked": True,
                "enabled": False,
                "requires_attended_user_confirmation": True,
                "reason": _text(action_map.get("reason")),
                "citations": _text_list(action_map.get("citations")),
            }
        )
    for case in document_cases:
        document_id = _text(case.get("document_id"))
        attestations.append(
            {
                "attestation_id": f"no-upload-staging:{document_id}",
                "action_id": "official_upload_staging",
                "document_id": document_id,
                "blocked": True,
                "enabled": False,
                "requires_attended_user_confirmation": True,
                "reason": "Synthetic document metadata may support local preview review only; no upload payload or official staging is produced.",
                "citations": ["file_preparation_compliance:metadata_only"],
            }
        )
    return attestations


def _validate_source_packets(errors: list[str], value: Any) -> None:
    packets = _mapping(value)
    for key in (
        "file_preparation_compliance",
        "safe_next_action_user_handoff_checklist",
        "missing_information_prompt_regression_corpus",
    ):
        packet = _mapping(packets.get(key))
        if packet.get("consumed") is not True:
            errors.append(f"source_packets.{key}.consumed must be true")


def _validate_document_cases(errors: list[str], value: Any) -> None:
    cases = _sequence(value)
    if not cases:
        errors.append("synthetic_document_metadata_cases must be non-empty")
    seen: set[str] = set()
    for index, case in enumerate(cases):
        case_map = _mapping(case)
        prefix = f"synthetic_document_metadata_cases[{index}]"
        document_id = _text(case_map.get("document_id"))
        if not document_id:
            errors.append(f"{prefix}.document_id is required")
        elif document_id in seen:
            errors.append(f"duplicate document_id: {document_id}")
        seen.add(document_id)
        if case_map.get("synthetic") is not True:
            errors.append(f"{prefix}.synthetic must be true")
        for field in ("downloaded", "private", "upload_staging", "raw_pdf_persisted"):
            if case_map.get(field) is not False:
                errors.append(f"{prefix}.{field} must be false")
        if case_map.get("compliance_status") != "metadata_only_preview_safe":
            errors.append(f"{prefix}.compliance_status must be metadata_only_preview_safe")


def _validate_required_prompts(errors: list[str], value: Any) -> None:
    prompts = _sequence(value)
    if not prompts:
        errors.append("required_missing_fact_prompts must be non-empty")
    for index, prompt in enumerate(prompts):
        prompt_map = _mapping(prompt)
        prefix = f"required_missing_fact_prompts[{index}]"
        if not _text(prompt_map.get("case_id")):
            errors.append(f"{prefix}.case_id is required")
        if not _text(prompt_map.get("prompt")):
            errors.append(f"{prefix}.prompt is required")
        if not _citations(prompt_map.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")
        if prompt_map.get("required_before_official_action") is not True:
            errors.append(f"{prefix}.required_before_official_action must be true")


def _validate_local_preview_notices(errors: list[str], value: Any) -> None:
    notices = _sequence(value)
    if not notices:
        errors.append("local_preview_only_notices must be non-empty")
    for index, notice in enumerate(notices):
        notice_map = _mapping(notice)
        prefix = f"local_preview_only_notices[{index}]"
        if notice_map.get("local_only") is not True:
            errors.append(f"{prefix}.local_only must be true")
        if notice_map.get("reversible") is not True:
            errors.append(f"{prefix}.reversible must be true")
        if notice_map.get("official_action_allowed") is not False:
            errors.append(f"{prefix}.official_action_allowed must be false")
        if not _citations(notice_map.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")


def _validate_reviewer_checkpoints(errors: list[str], value: Any) -> None:
    checkpoints = _sequence(value)
    if not checkpoints:
        errors.append("reviewer_checkpoints must be non-empty")
    for index, checkpoint in enumerate(checkpoints):
        checkpoint_map = _mapping(checkpoint)
        prefix = f"reviewer_checkpoints[{index}]"
        if checkpoint_map.get("requires_reviewer") is not True:
            errors.append(f"{prefix}.requires_reviewer must be true")
        if checkpoint_map.get("must_clear_before_upload") is not True:
            errors.append(f"{prefix}.must_clear_before_upload must be true")
        if not _citations(checkpoint_map.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")


def _validate_upload_attestations(errors: list[str], value: Any) -> None:
    attestations = _sequence(value)
    if not attestations:
        errors.append("upload_blocking_attestations must be non-empty")
    has_upload_block = False
    for index, attestation in enumerate(attestations):
        attestation_map = _mapping(attestation)
        prefix = f"upload_blocking_attestations[{index}]"
        action_id = _text(attestation_map.get("action_id"))
        if any(token in action_id.lower() for token in CONSEQUENTIAL_ACTIONS):
            has_upload_block = True
        if attestation_map.get("blocked") is not True:
            errors.append(f"{prefix}.blocked must be true")
        if attestation_map.get("enabled") is not False:
            errors.append(f"{prefix}.enabled must be false")
        if attestation_map.get("requires_attended_user_confirmation") is not True:
            errors.append(f"{prefix}.requires_attended_user_confirmation must be true")
        if not _citations(attestation_map.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")
    if not has_upload_block:
        errors.append("upload_blocking_attestations must include an upload, submit, certify, payment, scheduling, or cancellation block")


def _validate_output_attestations(errors: list[str], value: Any) -> None:
    attestations = _mapping(value)
    for field in ("metadata_only", "local_preview_only", "reversible"):
        if attestations.get(field) is not True:
            errors.append(f"output_attestations.{field} must be true")
    for field in (
        "official_submission_ready",
        "filled_document_created",
        "upload_staging_created",
        "private_pdf_read",
        "pdf_binary_written",
    ):
        if attestations.get(field) is not False:
            errors.append(f"output_attestations.{field} must be false")


def _validate_no_forbidden_content(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized in FORBIDDEN_KEYS:
                errors.append(f"forbidden private, PDF, or browser artifact key: {child_path}")
            _validate_no_forbidden_content(errors, child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_content(errors, child, f"{path}[{index}]")
    elif isinstance(value, str) and PRIVATE_OR_BINARY_TEXT.search(value):
        errors.append(f"forbidden private path, PDF binary, or runtime artifact text: {path}")


def _citations(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return [item for item in value if item]


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return value
    return ()


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""
