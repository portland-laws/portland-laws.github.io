"""Fixture-first stale citation remediation queue v6.

Consumes only public refresh result intake v6 fixture rows and builds an
offline remediation queue for cited requirement evidence. The queue identifies
which citations need re-extraction, which citations are unaffected, changed
source-hash placeholders, human-review holds, and downstream guardrail bundle
impact placeholders.

This module never crawls live sites, downloads documents, stores raw bodies,
opens DevHub, reads private documents, uploads, submits, certifies, pays,
schedules, or makes legal/permitting guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

QUEUE_VERSION = "stale-citation-remediation-queue-v6"
MODE = "fixture_first_offline_remediation_review_only"
INPUT_CONTRACT = "public_refresh_result_intake_v6_fixtures_only"

EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/agent_readiness/stale_citation_remediation_queue_v6.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_stale_citation_remediation_queue_v6.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

ALLOWED_REFRESH_OUTCOMES = frozenset({"changed", "unchanged", "removed", "unavailable", "review_hold"})
ALLOWED_REMEDIATION_ACTIONS = frozenset({"re_extract_cited_evidence", "none", "human_review_hold"})
ALLOWED_HUMAN_REVIEW_HOLDS = frozenset(
    {
        "hold_until_changed_source_hash_reviewed",
        "hold_until_removed_source_dispositioned",
        "hold_until_unavailable_source_retried_or_replaced",
        "hold_until_requirement_owner_approves",
        "hold_until_guardrail_impact_reviewed",
    }
)

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "live_crawling",
    "document_download",
    "raw_body_storage",
    "devhub_access",
    "private_document_read",
    "upload",
    "submission",
    "certification",
    "payment",
    "inspection_scheduling",
    "legal_or_permitting_guarantee",
)

REQUIRED_FALSE_FLAGS = (
    "live_crawl",
    "document_download",
    "raw_body_stored",
    "devhub_opened",
    "private_document_read",
    "upload_completed",
    "submission_completed",
    "certification_completed",
    "payment_completed",
    "inspection_scheduled",
    "legal_or_permitting_guarantee",
    "active_requirement_mutation",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "active_mutation",
)

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "devhub_session",
        "downloaded_document",
        "html_body",
        "local_private_path",
        "password",
        "private_document",
        "raw_body",
        "raw_crawl_output",
        "raw_html",
        "raw_pdf",
        "raw_text",
        "screenshot",
        "session_state",
        "trace",
        "warc_path",
    }
)

PROHIBITED_PHRASES = frozenset(
    {
        "certification completed",
        "devhub opened",
        "downloaded document",
        "guaranteed approval",
        "guaranteed permit",
        "legal advice",
        "live crawl completed",
        "payment completed",
        "permit guaranteed",
        "raw body stored",
        "submission completed",
        "upload completed",
    }
)


@dataclass(frozen=True)
class PublicRefreshResultIntakeV6Row:
    row_id: str
    refresh_result_id: str
    source_id: str
    canonical_url: str
    cited_requirement_id: str
    citation_evidence_id: str
    citation_span_id: str
    previous_source_hash_placeholder: str
    refreshed_source_hash_placeholder: str
    refresh_outcome: str
    remediation_action: str
    downstream_guardrail_bundle_impact_placeholders: tuple[str, ...]
    human_review_holds: tuple[str, ...]
    reviewer_note: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "PublicRefreshResultIntakeV6Row":
        _reject_prohibited_content(row)
        if row.get("public_refresh_result_intake_v6_row") is not True:
            raise ValueError("row must declare public_refresh_result_intake_v6_row true")
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"row must declare {flag} false")

        refresh_outcome = _required_text(row, "refresh_outcome")
        if refresh_outcome not in ALLOWED_REFRESH_OUTCOMES:
            raise ValueError(f"unsupported refresh_outcome: {refresh_outcome}")
        remediation_action = _required_text(row, "remediation_action")
        if remediation_action not in ALLOWED_REMEDIATION_ACTIONS:
            raise ValueError(f"unsupported remediation_action: {remediation_action}")
        human_review_holds = _required_allowed_tuple(row, "human_review_holds", ALLOWED_HUMAN_REVIEW_HOLDS, allow_empty=True)

        return cls(
            row_id=_required_text(row, "row_id"),
            refresh_result_id=_required_text(row, "refresh_result_id"),
            source_id=_required_text(row, "source_id"),
            canonical_url=_required_text(row, "canonical_url"),
            cited_requirement_id=_required_placeholder_text(row, "cited_requirement_id"),
            citation_evidence_id=_required_placeholder_text(row, "citation_evidence_id"),
            citation_span_id=_required_placeholder_text(row, "citation_span_id"),
            previous_source_hash_placeholder=_required_hash_placeholder(row, "previous_source_hash_placeholder"),
            refreshed_source_hash_placeholder=_required_hash_placeholder(row, "refreshed_source_hash_placeholder"),
            refresh_outcome=refresh_outcome,
            remediation_action=remediation_action,
            downstream_guardrail_bundle_impact_placeholders=_required_placeholder_tuple(
                row, "downstream_guardrail_bundle_impact_placeholders"
            ),
            human_review_holds=human_review_holds,
            reviewer_note=_required_text(row, "reviewer_note"),
        )


def build_stale_citation_remediation_queue_v6(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = tuple(PublicRefreshResultIntakeV6Row.from_mapping(row) for row in rows)
    if not normalized_rows:
        raise ValueError("at least one public refresh result intake v6 row is required")

    queue = {
        "queue_version": QUEUE_VERSION,
        "mode": MODE,
        "input_contract": INPUT_CONTRACT,
        "input_row_count": len(normalized_rows),
        "cited_requirement_evidence_needing_reextraction": _reextraction_rows(normalized_rows),
        "unaffected_citations": _unaffected_rows(normalized_rows),
        "changed_source_hash_placeholders": _changed_hash_placeholders(normalized_rows),
        "human_review_hold_rows": _human_review_rows(normalized_rows),
        "downstream_guardrail_bundle_impact_placeholders": _sorted_unique(
            _flatten(row.downstream_guardrail_bundle_impact_placeholders for row in normalized_rows)
        ),
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "attestations": {
            "fixture_first": True,
            "public_refresh_result_intake_v6_fixtures_only": True,
            "no_live_crawling": True,
            "no_document_downloads": True,
            "no_raw_body_storage": True,
            "no_devhub_access": True,
            "no_private_document_reads": True,
            "no_uploads_submissions_certifications_payments_or_scheduling": True,
            "no_active_requirement_process_or_guardrail_mutation": True,
            "no_legal_or_permitting_guarantees": True,
        },
    }
    validate_stale_citation_remediation_queue_v6(queue)
    return queue


def validate_stale_citation_remediation_queue_v6(queue: Mapping[str, Any]) -> None:
    _reject_prohibited_content(queue)
    if queue.get("queue_version") != QUEUE_VERSION:
        raise ValueError(f"queue_version must be {QUEUE_VERSION}")
    if queue.get("mode") != MODE:
        raise ValueError(f"mode must be {MODE}")
    if queue.get("input_contract") != INPUT_CONTRACT:
        raise ValueError(f"input_contract must be {INPUT_CONTRACT}")
    if queue.get("exact_offline_validation_commands") != [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]:
        raise ValueError("queue must include exact offline validation commands only")
    if queue.get("prohibited_actions") != list(PROHIBITED_ACTIONS):
        raise ValueError("queue must preserve prohibited actions")
    attestations = queue.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("attestations must be a mapping")
    for key, value in attestations.items():
        if value is not True:
            raise ValueError(f"attestation {key} must be true")


def load_public_refresh_result_intake_v6_rows(path: Path | str) -> tuple[Mapping[str, Any], ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("public_refresh_result_intake_v6_rows")
    if not isinstance(rows, list):
        raise ValueError("fixture must contain public_refresh_result_intake_v6_rows")
    return tuple(row for row in rows if isinstance(row, Mapping))


def build_queue_from_fixture(path: Path | str) -> dict[str, Any]:
    return build_stale_citation_remediation_queue_v6(load_public_refresh_result_intake_v6_rows(path))


def _reextraction_rows(rows: Sequence[PublicRefreshResultIntakeV6Row]) -> list[dict[str, Any]]:
    return [
        _row_summary(row)
        for row in sorted(rows, key=lambda item: item.row_id)
        if row.remediation_action == "re_extract_cited_evidence"
    ]


def _unaffected_rows(rows: Sequence[PublicRefreshResultIntakeV6Row]) -> list[dict[str, Any]]:
    return [
        _row_summary(row)
        for row in sorted(rows, key=lambda item: item.row_id)
        if row.remediation_action == "none" and row.refresh_outcome == "unchanged"
    ]


def _human_review_rows(rows: Sequence[PublicRefreshResultIntakeV6Row]) -> list[dict[str, Any]]:
    return [
        _row_summary(row)
        for row in sorted(rows, key=lambda item: item.row_id)
        if row.remediation_action == "human_review_hold" or row.human_review_holds
    ]


def _changed_hash_placeholders(rows: Sequence[PublicRefreshResultIntakeV6Row]) -> list[dict[str, str]]:
    changed = []
    for row in rows:
        if row.previous_source_hash_placeholder != row.refreshed_source_hash_placeholder:
            changed.append(
                {
                    "row_id": row.row_id,
                    "source_id": row.source_id,
                    "previous_source_hash_placeholder": row.previous_source_hash_placeholder,
                    "refreshed_source_hash_placeholder": row.refreshed_source_hash_placeholder,
                }
            )
    return sorted(changed, key=lambda item: item["row_id"])


def _row_summary(row: PublicRefreshResultIntakeV6Row) -> dict[str, Any]:
    return {
        "row_id": row.row_id,
        "refresh_result_id": row.refresh_result_id,
        "source_id": row.source_id,
        "canonical_url": row.canonical_url,
        "cited_requirement_id": row.cited_requirement_id,
        "citation_evidence_id": row.citation_evidence_id,
        "citation_span_id": row.citation_span_id,
        "refresh_outcome": row.refresh_outcome,
        "remediation_action": row.remediation_action,
        "human_review_holds": list(row.human_review_holds),
        "downstream_guardrail_bundle_impact_placeholders": list(row.downstream_guardrail_bundle_impact_placeholders),
        "reviewer_note": row.reviewer_note,
    }


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_placeholder_text(row: Mapping[str, Any], key: str) -> str:
    value = _required_text(row, key)
    if "placeholder" not in value and not value.startswith(("REQ-", "req-", "citation-", "evidence-")):
        raise ValueError(f"{key} must be a requirement/evidence placeholder")
    return value


def _required_hash_placeholder(row: Mapping[str, Any], key: str) -> str:
    value = _required_text(row, key)
    if not value.startswith("sha256:placeholder:"):
        raise ValueError(f"{key} must be a sha256 placeholder")
    return value


def _required_placeholder_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    values = row.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{key} must be a non-empty list")
    result = tuple(_require_string(value, key) for value in values)
    for value in result:
        if "placeholder" not in value:
            raise ValueError(f"{key} values must be placeholders")
    return result


def _required_allowed_tuple(
    row: Mapping[str, Any], key: str, allowed: frozenset[str], *, allow_empty: bool = False
) -> tuple[str, ...]:
    values = row.get(key)
    if not isinstance(values, list) or (not values and not allow_empty):
        raise ValueError(f"{key} must be a list")
    result = tuple(_require_string(value, key) for value in values)
    unsupported = [value for value in result if value not in allowed]
    if unsupported:
        raise ValueError(f"unsupported {key}: {unsupported}")
    return result


def _require_string(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} values must be non-empty strings")
    return value


def _flatten(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    return tuple(value for group in groups for value in group)


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values))


def _reject_prohibited_content(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in PROHIBITED_KEYS:
                raise ValueError(f"prohibited key present: {key}")
            _reject_prohibited_content(item)
    elif isinstance(value, list):
        for item in value:
            _reject_prohibited_content(item)
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in lowered:
                raise ValueError(f"prohibited phrase present: {phrase}")
