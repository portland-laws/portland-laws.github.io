"""Validation guardrails for PP&D human review queue packets."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


PRIVATE_KEY_PARTS = (
    "password",
    "passwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "cookie",
    "session",
    "storage_state",
    "authorization",
    "auth_header",
    "private",
    "ssn",
)

PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"\b(sessionid|connect\.sid|auth_token|access_token)=", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE),
)

RAW_OR_AUTH_ARTIFACT_KEYS = (
    "raw_html",
    "raw_body",
    "response_body",
    "raw_response",
    "raw_crawl",
    "crawl_artifact",
    "authenticated_artifact",
    "har_path",
    "trace_path",
    "screenshot_path",
    "storage_state_path",
    "auth_state_path",
    "devhub_session",
)

DOCUMENT_PATH_KEY_PARTS = (
    "downloaded_document",
    "download_path",
    "document_path",
    "local_path",
    "file_path",
)

DOCUMENT_PATH_PATTERN = re.compile(
    r"(^|[/\\.])(downloads?|downloaded_documents|raw_crawl|crawl_output)([/\\]|$)|\.(pdf|doc|docx|xls|xlsx|zip)$",
    re.IGNORECASE,
)

PRODUCTION_READY_STATUSES = {
    "production_ready",
    "ready_for_production",
    "approved_for_production",
    "ready",
}

CONSEQUENTIAL_ACTION_WORDS = (
    "submit",
    "certify",
    "pay",
    "payment",
    "cancel",
    "upload",
    "create account",
    "schedule inspection",
    "send application",
    "file application",
    "approve permit",
    "sign",
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


def validate_human_review_queue_packet(packet: dict[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for a human review queue packet."""
    issues: list[ValidationIssue] = []

    if not isinstance(packet, dict):
        return [ValidationIssue("packet_type", "$", "packet must be a JSON object")]

    _scan_value(packet, "$", issues)
    _validate_packet_links(packet, issues)
    _validate_reviewer_prompts(packet, issues)
    _validate_production_ready_status(packet, issues)
    _validate_recommendations(packet, issues)
    return issues


def assert_valid_human_review_queue_packet(packet: dict[str, Any]) -> None:
    """Raise ValueError when a packet violates human review queue guardrails."""
    issues = validate_human_review_queue_packet(packet)
    if issues:
        detail = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def _scan_value(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            lowered = str(key).lower()
            if any(part in lowered for part in PRIVATE_KEY_PARTS):
                issues.append(ValidationIssue("private_value", child_path, "private or authentication field is not allowed"))
            if lowered in RAW_OR_AUTH_ARTIFACT_KEYS or any(part in lowered for part in RAW_OR_AUTH_ARTIFACT_KEYS):
                issues.append(ValidationIssue("raw_or_authenticated_artifact", child_path, "raw crawl or authenticated artifact is not allowed"))
            if any(part in lowered for part in DOCUMENT_PATH_KEY_PARTS) and isinstance(child, str):
                issues.append(ValidationIssue("downloaded_document_path", child_path, "downloaded document paths are not allowed"))
            _scan_value(child, child_path, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_value(child, f"{path}[{index}]", issues)
    elif isinstance(value, str):
        for pattern in PRIVATE_VALUE_PATTERNS:
            if pattern.search(value):
                issues.append(ValidationIssue("private_value", path, "private value pattern is not allowed"))
                break
        if DOCUMENT_PATH_PATTERN.search(value):
            issues.append(ValidationIssue("downloaded_document_path", path, "local downloaded document or raw crawl path is not allowed"))


def _validate_packet_links(packet: dict[str, Any], issues: list[ValidationIssue]) -> None:
    links = packet.get("packet_links", packet.get("links"))
    if not isinstance(links, list) or not links:
        issues.append(ValidationIssue("missing_packet_links", "$.packet_links", "at least one packet link is required"))
        return
    for index, link in enumerate(links):
        if not isinstance(link, dict) or not str(link.get("url", "")).startswith(("http://", "https://")):
            issues.append(ValidationIssue("missing_packet_links", f"$.packet_links[{index}]", "packet link must include an http(s) url"))


def _validate_reviewer_prompts(packet: dict[str, Any], issues: list[ValidationIssue]) -> None:
    prompts = packet.get("reviewer_prompts", packet.get("reviewer_prompt"))
    if isinstance(prompts, str):
        ok = bool(prompts.strip())
    elif isinstance(prompts, list):
        ok = any(isinstance(prompt, str) and prompt.strip() for prompt in prompts)
    else:
        ok = False
    if not ok:
        issues.append(ValidationIssue("missing_reviewer_prompts", "$.reviewer_prompts", "reviewer prompts are required"))


def _validate_production_ready_status(packet: dict[str, Any], issues: list[ValidationIssue]) -> None:
    status = str(packet.get("status", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if status not in PRODUCTION_READY_STATUSES:
        return
    review = packet.get("human_review", {})
    reviewed = isinstance(review, dict) and review.get("reviewed") is True and bool(review.get("reviewed_by"))
    if not reviewed:
        issues.append(ValidationIssue("unreviewed_production_ready_status", "$.status", "production-ready status requires completed human review"))


def _validate_recommendations(packet: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for path, text in _recommendation_texts(packet):
        lowered = text.lower()
        if any(word in lowered for word in CONSEQUENTIAL_ACTION_WORDS):
            issues.append(ValidationIssue("live_or_consequential_action_recommendation", path, "live or consequential action recommendations are not allowed"))


def _recommendation_texts(value: Any, path: str = "$", key_hint: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            child_path = f"{path}.{key}"
            if isinstance(child, str) and ("recommend" in lowered or lowered in {"action", "next_action", "decision"}):
                yield child_path, child
            yield from _recommendation_texts(child, child_path, lowered)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _recommendation_texts(child, f"{path}[{index}]", key_hint)
    elif isinstance(value, str) and "recommend" in key_hint:
        yield path, value
