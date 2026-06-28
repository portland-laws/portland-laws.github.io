"""Validation for agent gap-analysis rerun packets.

The validator is deliberately side-effect free and schema-light. It checks the
safety properties required before an agent may rely on a rerun packet produced
from committed PP&D fixtures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(?:^|[\s'\"])(?:/home/[^\s'\"]+|/Users/[^\s'\"]+|/private/[^\s'\"]+|/var/folders/[^\s'\"]+|[A-Za-z]:\\Users\\[^\s'\"]+)"
)

PRIVATE_DOCUMENT_VALUE_KEYS = {
    "address",
    "authorization",
    "bank_account",
    "card_number",
    "cookie",
    "credit_card",
    "date_of_birth",
    "dob",
    "document_value",
    "driver_license",
    "email",
    "ein",
    "file_path",
    "full_text",
    "local_path",
    "password",
    "path",
    "phone",
    "private_path",
    "raw_document",
    "raw_value",
    "routing_number",
    "secret",
    "session",
    "ssn",
    "tax_id",
    "token",
}

ALLOWED_LOCAL_PREVIEW_ACTIONS = {
    "preview_draft_guardrail_explanations",
    "preview_missing_fact_question_list",
    "preview_reversible_draft_plan",
    "prepare_reversible_form_draft_values",
    "render_local_pdf_field_mapping_preview",
}

ALLOWED_NEXT_SAFE_ACTIONS = {
    "ask_user_for_missing_documents",
    "ask_user_for_missing_facts",
    "ask_user_to_resolve_conflicts",
    "preview_draft_guardrail_explanations",
    "preview_missing_fact_question_list",
    "preview_reversible_draft_plan",
    "render_local_pdf_field_mapping_preview",
    "review_public_requirements",
}

CONSEQUENTIAL_ACTION_WORDS = {
    "acknowledge",
    "cancel",
    "certification",
    "certify",
    "file",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "submission",
    "upload",
    "withdraw",
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


def validate_agent_gap_analysis_rerun_packet(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for an agent gap-analysis rerun packet."""
    issues: list[ValidationIssue] = []

    if not isinstance(packet, Mapping):
        return [ValidationIssue("invalid_packet", "$", "rerun packet must be an object")]

    _validate_private_document_values(packet, issues)
    _validate_prior_comparison(packet, issues)
    _validate_cited_prompts(packet, issues)
    _validate_next_actions(packet, issues)
    _validate_blocked_action_downgrades(packet, issues)
    _validate_consequential_automation(packet, issues)

    return issues


def issue_codes(packet: Mapping[str, Any]) -> set[str]:
    return {issue.code for issue in validate_agent_gap_analysis_rerun_packet(packet)}


def _validate_private_document_values(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for path, key, value in _walk(packet):
        lowered_key = key.lower() if key else ""
        if isinstance(value, str) and LOCAL_PRIVATE_PATH_RE.search(value):
            issues.append(ValidationIssue("private_document_path", path, "rerun packets must not include local private document paths"))
        if lowered_key in PRIVATE_DOCUMENT_VALUE_KEYS and _has_value(value):
            issues.append(ValidationIssue("private_document_value", path, "rerun packets must not include private document values or raw content"))


def _validate_prior_comparison(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    comparison = packet.get("comparison_to_prior_gap_analysis")
    if not isinstance(comparison, Mapping):
        issues.append(ValidationIssue("missing_prior_comparison", "comparison_to_prior_gap_analysis", "rerun packets must compare against the prior gap-analysis result"))
        return

    required_fields = (
        "prior_result_id",
        "current_result_id",
        "changed_missing_facts",
        "changed_blocked_actions",
    )
    for field in required_fields:
        if not _has_value(comparison.get(field)):
            issues.append(ValidationIssue("missing_prior_comparison", f"comparison_to_prior_gap_analysis.{field}", "prior comparison is missing a required field"))


def _validate_cited_prompts(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    prompts = _list_at(packet, "user_facing_questions") + _list_at(packet, "prompts")
    for index, prompt in enumerate(prompts):
        prompt_path = f"user_facing_questions[{index}]"
        if not isinstance(prompt, Mapping):
            issues.append(ValidationIssue("uncited_prompt", prompt_path, "agent prompts must be objects with citations"))
            continue
        if not _has_citation(prompt):
            issues.append(ValidationIssue("uncited_prompt", prompt_path, "agent prompts must cite source evidence ids or source citations"))


def _validate_next_actions(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for field in ("next_safe_actions", "next_actions", "recommended_actions"):
        for index, action in enumerate(_list_at(packet, field)):
            action_id = _action_id(action)
            if action_id and action_id not in ALLOWED_NEXT_SAFE_ACTIONS:
                issues.append(ValidationIssue("unsupported_next_action", f"{field}[{index}]", "rerun packet contains an unsupported next action"))

    for index, preview in enumerate(_list_at(packet, "allowed_local_previews")):
        action_id = _action_id(preview)
        if action_id and action_id not in ALLOWED_LOCAL_PREVIEW_ACTIONS:
            issues.append(ValidationIssue("unsupported_next_action", f"allowed_local_previews[{index}]", "local preview action is not in the supported allowlist"))


def _validate_blocked_action_downgrades(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    comparison = packet.get("comparison_to_prior_gap_analysis")
    if not isinstance(comparison, Mapping):
        return
    changed = comparison.get("changed_blocked_actions")
    if not isinstance(changed, Mapping):
        return
    removed = _string_list(changed.get("removed"))
    if removed:
        issues.append(ValidationIssue("blocked_action_downgrade", "comparison_to_prior_gap_analysis.changed_blocked_actions.removed", "rerun packets must not downgrade previously blocked actions"))


def _validate_consequential_automation(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for field in ("allowed_local_previews", "next_safe_actions", "next_actions", "recommended_actions"):
        for index, action in enumerate(_list_at(packet, field)):
            action_text = _action_text(action)
            if _is_consequential(action_text):
                issues.append(ValidationIssue("consequential_automation", f"{field}[{index}]", "consequential PP&D actions cannot be advertised as automated or next-safe"))

    limits = packet.get("privacy_and_execution_limits")
    if isinstance(limits, Mapping):
        for key in ("launches_devhub", "uses_authenticated_session", "reads_private_files", "automates_official_actions"):
            if limits.get(key) is True:
                issues.append(ValidationIssue("consequential_automation", f"privacy_and_execution_limits.{key}", "rerun packets must remain offline and non-consequential"))


def _walk(value: Any, path: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            yield from _walk(child_value, f"{path}.{child_key_text}", child_key_text)
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", key)


def _list_at(packet: Mapping[str, Any], key: str) -> list[Any]:
    value = packet.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _has_citation(item: Mapping[str, Any]) -> bool:
    evidence_ids = item.get("source_evidence_ids")
    if isinstance(evidence_ids, list) and any(str(evidence_id).strip() for evidence_id in evidence_ids):
        return True

    citations = item.get("citations") or item.get("sources") or item.get("source_citations")
    if not isinstance(citations, list):
        return False
    for citation in citations:
        if isinstance(citation, str) and citation.startswith("http"):
            return True
        if isinstance(citation, Mapping) and _has_value(citation.get("url")) and _has_value(citation.get("title")):
            return True
    return False


def _action_id(action: Any) -> str:
    if isinstance(action, Mapping):
        for key in ("action_id", "action", "id", "label"):
            value = action.get(key)
            if _has_value(value):
                return str(value)
        return ""
    return str(action) if _has_value(action) else ""


def _action_text(action: Any) -> str:
    if isinstance(action, Mapping):
        return " ".join(str(action.get(key, "")) for key in ("action_id", "action", "label", "description", "title"))
    return str(action)


def _is_consequential(action_text: str) -> bool:
    normalized = action_text.replace("-", "_").lower()
    return any(word in normalized for word in CONSEQUENTIAL_ACTION_WORDS)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
