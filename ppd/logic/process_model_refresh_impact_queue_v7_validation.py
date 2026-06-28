"""Validation for PP&D process model refresh impact queue v7.

The queue is commit-safe metadata only. It describes what a process model
refresh would affect, but it must not claim to mutate guardrails, run live
crawls, complete official actions, or carry private/session/raw artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_QUEUE_FIELDS = (
    "requirement_node_candidate_set_refs",
    "affected_process_model_rows",
    "eligibility_impact_placeholders",
    "document_impact_placeholders",
    "fee_impact_placeholders",
    "deadline_impact_placeholders",
    "stage_impact_placeholders",
    "unsupported_path_carry_forward_notes",
    "guardrail_bundle_recompile_suggestions",
    "stale_evidence_holds",
    "reviewer_signoff_placeholders",
    "validation_commands",
)

PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "browser_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har",
    "local_private_path",
    "mfa_token",
    "password",
    "private_upload",
    "screenshot",
    "session",
    "session_id",
    "storage_state",
    "trace",
}

RAW_OR_DOWNLOADED_ARTIFACT_KEYS = {
    "downloaded_artifact",
    "downloaded_artifacts",
    "download_path",
    "raw_body",
    "raw_crawl_artifact",
    "raw_crawl_artifacts",
    "raw_html",
    "raw_pdf",
    "warc_path",
}

ACTIVE_MUTATION_KEYS = {
    "active_guardrail_mutation",
    "active_mutation",
    "apply_mutation",
    "guardrail_mutation",
    "mutation_enabled",
    "mutations_enabled",
    "write_enabled",
    "writes_enabled",
}

OFFICIAL_ACTION_KEYS = {
    "certification_completed",
    "fee_payment_completed",
    "inspection_scheduled",
    "official_action_completed",
    "official_submission_completed",
    "permit_submitted",
    "submitted_to_city",
    "upload_completed",
}

LIVE_CRAWL_KEYS = {
    "crawl_executed",
    "live_crawl",
    "live_crawl_executed",
    "network_crawl_completed",
    "public_crawl_executed",
}

LEGAL_GUARANTEE_PHRASES = (
    "approval guaranteed",
    "approved permit guaranteed",
    "guarantee approval",
    "guarantee code compliance",
    "guarantee permit issuance",
    "guaranteed approval",
    "guaranteed compliant",
    "guaranteed permit",
    "legal advice",
    "permit guaranteed",
    "will be approved",
    "will pass inspection",
)

UNSAFE_CLAIM_PHRASES = (
    "actively mutated guardrails",
    "completed official action",
    "downloaded crawl artifact",
    "executed live crawl",
    "raw crawl artifact",
    "submitted the permit",
)


@dataclass(frozen=True)
class QueueValidationIssue:
    """A deterministic validation issue for a queue payload."""

    code: str
    path: str
    message: str


def validate_process_model_refresh_impact_queue_v7(payload: Mapping[str, Any]) -> list[QueueValidationIssue]:
    """Return validation issues for a process model refresh impact queue v7 payload."""

    issues: list[QueueValidationIssue] = []
    queue_version = payload.get("queue_version")
    if queue_version != "process_model_refresh_impact_queue_v7":
        issues.append(
            QueueValidationIssue(
                code="invalid_queue_version",
                path="queue_version",
                message="queue_version must be process_model_refresh_impact_queue_v7.",
            )
        )

    for field in REQUIRED_QUEUE_FIELDS:
        if _is_missing(payload.get(field)):
            issues.append(
                QueueValidationIssue(
                    code="missing_required_refresh_impact_field",
                    path=field,
                    message=f"{field} must be present and non-empty.",
                )
            )

    issues.extend(_validate_candidate_refs(payload.get("requirement_node_candidate_set_refs")))
    issues.extend(_validate_process_model_rows(payload.get("affected_process_model_rows")))
    issues.extend(_validate_validation_commands(payload.get("validation_commands")))
    issues.extend(_scan_for_disallowed_content(payload))
    return issues


def reject_process_model_refresh_impact_queue_v7(payload: Mapping[str, Any]) -> None:
    """Raise ValueError when the queue payload is not commit-safe."""

    issues = validate_process_model_refresh_impact_queue_v7(payload)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"process model refresh impact queue v7 is invalid: {details}")


def _validate_candidate_refs(value: Any) -> list[QueueValidationIssue]:
    issues: list[QueueValidationIssue] = []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return issues
    for index, ref in enumerate(value):
        if not isinstance(ref, Mapping):
            issues.append(
                QueueValidationIssue(
                    code="invalid_requirement_candidate_set_ref",
                    path=f"requirement_node_candidate_set_refs[{index}]",
                    message="RequirementNode candidate set references must be objects.",
                )
            )
            continue
        if _is_missing(ref.get("candidate_set_id")):
            issues.append(
                QueueValidationIssue(
                    code="missing_requirement_candidate_set_id",
                    path=f"requirement_node_candidate_set_refs[{index}].candidate_set_id",
                    message="RequirementNode candidate set reference must include candidate_set_id.",
                )
            )
        if _is_missing(ref.get("requirement_ids")):
            issues.append(
                QueueValidationIssue(
                    code="missing_requirement_candidate_ids",
                    path=f"requirement_node_candidate_set_refs[{index}].requirement_ids",
                    message="RequirementNode candidate set reference must include candidate RequirementNode ids.",
                )
            )
    return issues


def _validate_process_model_rows(value: Any) -> list[QueueValidationIssue]:
    issues: list[QueueValidationIssue] = []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return issues
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            issues.append(
                QueueValidationIssue(
                    code="invalid_affected_process_model_row",
                    path=f"affected_process_model_rows[{index}]",
                    message="Affected ProcessModel rows must be objects.",
                )
            )
            continue
        for key in ("process_id", "permit_type", "guardrail_bundle_id"):
            if _is_missing(row.get(key)):
                issues.append(
                    QueueValidationIssue(
                        code="missing_affected_process_model_row_field",
                        path=f"affected_process_model_rows[{index}].{key}",
                        message=f"Affected ProcessModel row must include {key}.",
                    )
                )
    return issues


def _validate_validation_commands(value: Any) -> list[QueueValidationIssue]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    issues: list[QueueValidationIssue] = []
    for index, command in enumerate(value):
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)) or not command:
            issues.append(
                QueueValidationIssue(
                    code="invalid_validation_command",
                    path=f"validation_commands[{index}]",
                    message="Validation commands must be non-empty argv arrays.",
                )
            )
            continue
        if not all(isinstance(part, str) and part for part in command):
            issues.append(
                QueueValidationIssue(
                    code="invalid_validation_command_part",
                    path=f"validation_commands[{index}]",
                    message="Validation command argv parts must be non-empty strings.",
                )
            )
    return issues


def _scan_for_disallowed_content(payload: Mapping[str, Any]) -> list[QueueValidationIssue]:
    issues: list[QueueValidationIssue] = []
    for path, key, value in _walk(payload):
        normalized_key = _normalize_token(key)
        normalized_value = _normalize_value(value)
        if normalized_key in PRIVATE_ARTIFACT_KEYS:
            issues.append(_issue("private_or_auth_artifact", path, "Private, session, auth, trace, or browser artifacts are not allowed."))
        if normalized_key in RAW_OR_DOWNLOADED_ARTIFACT_KEYS:
            issues.append(_issue("raw_or_downloaded_artifact", path, "Downloaded and raw crawl artifacts are not allowed in committed queue metadata."))
        if normalized_key in LIVE_CRAWL_KEYS and _truthy_claim(value):
            issues.append(_issue("live_crawl_execution_claim", path, "Queue metadata must not claim live crawl execution."))
        if normalized_key in ACTIVE_MUTATION_KEYS and _truthy_claim(value):
            issues.append(_issue("active_mutation_claim", path, "Queue metadata must not claim active mutation or writes."))
        if normalized_key in OFFICIAL_ACTION_KEYS and _truthy_claim(value):
            issues.append(_issue("official_action_completion_claim", path, "Queue metadata must not claim official-action completion."))
        for phrase in LEGAL_GUARANTEE_PHRASES:
            if phrase in normalized_value:
                issues.append(_issue("legal_or_permitting_guarantee", path, "Legal advice and permitting guarantees are not allowed."))
                break
        for phrase in UNSAFE_CLAIM_PHRASES:
            if phrase in normalized_value:
                issues.append(_issue("unsafe_refresh_queue_claim", path, "Queue metadata contains an unsafe execution or mutation claim."))
                break
    return issues


def _walk(value: Any, path: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{path}.{child_key_text}" if path != "$" else child_key_text
            yield from _walk(child_value, child_path, child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", key)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (Sequence, Mapping)) and not isinstance(value, (str, bytes)) and len(value) == 0:
        return True
    return False


def _truthy_claim(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"active", "applied", "complete", "completed", "done", "enabled", "executed", "true", "yes"}
    return bool(value) and not isinstance(value, (Mapping, Sequence))


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    return ""


def _issue(code: str, path: str, message: str) -> QueueValidationIssue:
    return QueueValidationIssue(code=code, path=path, message=message)
