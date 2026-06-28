"""Fixture-first re-extraction candidate queue helpers.

This module intentionally consumes caller-provided rows only. It performs no
network access, browser automation, document downloads, active requirement
mutation, crawler-state writes, daemon-state writes, or archive updates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

QUEUE_VERSION = "reextraction_candidate_queue_v1"
SYNTHETIC_REVIEWER_ROW_KIND = "synthetic_stale_readiness_reviewer_disposition"
PUBLIC_MONITORING_PLACEHOLDER_KIND = "public_monitoring_placeholder"

OFFLINE_VALIDATION_COMMANDS: List[List[str]] = [
    ["python3", "-m", "unittest", "ppd.tests.test_reextraction_candidate_queue"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REEXTRACT_DISPOSITIONS = {
    "stale_requires_reextraction",
    "citation_placeholder_required",
    "blocked_stale_source_dependency",
}

_REQUIRED_REVIEWER_LIST_FIELDS = (
    "citation_placeholder_needs",
    "extraction_confidence_notes",
    "blocked_stale_source_dependencies",
)

_REQUIRED_HUMAN_REVIEW_FIELDS = ("review_queue", "reason")

_ACTIVE_MUTATION_FLAG_KEYS = {
    "active_mutation",
    "active_mutation_enabled",
    "active_registry_mutated",
    "active_requirements_mutated",
    "active_artifacts_mutated",
    "mutates_active_artifacts",
    "mutation_enabled",
    "write_active_artifacts",
}

_PRIVATE_OR_RAW_KEY_TOKENS = (
    "auth_state",
    "cookie",
    "credential",
    "downloaded_artifact",
    "har",
    "local_private",
    "payment_detail",
    "private_artifact",
    "raw_artifact",
    "raw_body",
    "raw_crawl",
    "screenshot",
    "session_file",
    "trace",
    "warc",
)

_FORBIDDEN_TEXT_PHRASES = (
    "active artifact mutation",
    "active corpus updated",
    "authenticated devhub observed",
    "devhub session captured",
    "downloaded document",
    "downloaded live",
    "fetched live",
    "guaranteed approval",
    "guarantees permit",
    "legal advice",
    "legally sufficient",
    "live crawl",
    "live devhub",
    "live fetch",
    "permit approval guaranteed",
    "production ready",
    "promoted to current",
    "raw crawl",
    "release promoted",
    "will be approved",
)


class ReextractionCandidateQueueV1Error(ValueError):
    """Raised when a re-extraction candidate queue is unsafe."""


def load_json_fixture(path: Path) -> Any:
    """Load a committed JSON fixture from an explicit local path."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_reextraction_candidate_queue(
    reviewer_disposition_rows: Sequence[Mapping[str, Any]],
    public_monitoring_placeholders: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Build a deterministic queue from synthetic rows and public placeholders.

    The returned queue is advisory only. It lists candidate requirement IDs and
    review metadata, but it does not extract text, crawl sources, download
    documents, open DevHub, or mutate any active PP&D data products.
    """
    placeholders_by_source_id = _index_public_placeholders(public_monitoring_placeholders)
    candidates: List[Dict[str, Any]] = []
    skipped_rows: List[Dict[str, Any]] = []

    for row in sorted(reviewer_disposition_rows, key=_reviewer_row_sort_key):
        validation_error = _validate_reviewer_row(row)
        if validation_error is not None:
            skipped_rows.append(_skip(row, validation_error))
            continue

        disposition = str(row["reviewer_disposition"])
        if disposition not in _REEXTRACT_DISPOSITIONS:
            skipped_rows.append(_skip(row, "reviewer_disposition_not_queueable"))
            continue

        source_evidence_ids = _string_list(row.get("source_evidence_ids", []))
        if not source_evidence_ids:
            skipped_rows.append(_skip(row, "requirement_is_not_source_backed"))
            continue

        source_id = str(row["source_id"])
        placeholder = placeholders_by_source_id.get(source_id)
        if placeholder is None:
            skipped_rows.append(_skip(row, "missing_public_monitoring_placeholder"))
            continue

        placeholder_error = _validate_public_placeholder(placeholder)
        if placeholder_error is not None:
            skipped_rows.append(_skip(row, placeholder_error))
            continue

        candidates.append(
            {
                "requirement_id": str(row["requirement_id"]),
                "source_id": source_id,
                "source_evidence_ids": source_evidence_ids,
                "reviewer_disposition": disposition,
                "citation_placeholder_needs": _citation_placeholder_needs(row, placeholder),
                "extraction_confidence_notes": _confidence_notes(row),
                "human_review_routing": _human_review_routing(row, placeholder),
                "blocked_stale_source_dependencies": _blocked_dependencies(row, placeholder),
                "monitoring_placeholder": {
                    "placeholder_id": str(placeholder["placeholder_id"]),
                    "public_source_url": str(placeholder["public_source_url"]),
                    "freshness_status": str(placeholder["freshness_status"]),
                    "last_public_check_at": str(placeholder["last_public_check_at"]),
                },
            }
        )

    candidates.sort(key=lambda item: item["requirement_id"])
    skipped_rows.sort(key=lambda item: item.get("requirement_id", ""))

    queue = {
        "queue_version": QUEUE_VERSION,
        "input_contract": {
            "reviewer_rows": SYNTHETIC_REVIEWER_ROW_KIND,
            "monitoring_placeholders": PUBLIC_MONITORING_PLACEHOLDER_KIND,
        },
        "side_effects": {
            "live_extraction_performed": False,
            "crawler_or_download_performed": False,
            "devhub_opened": False,
            "active_requirements_mutated": False,
            "private_files_written": False,
        },
        "candidate_requirement_ids": [item["requirement_id"] for item in candidates],
        "candidates": candidates,
        "skipped_rows": skipped_rows,
        "offline_validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
    }
    validate_reextraction_candidate_queue_v1(queue)
    return queue


def validate_reextraction_candidate_queue_v1(queue: Mapping[str, Any]) -> None:
    """Raise if a built queue is incomplete or unsafe for offline review."""
    issues: List[str] = []
    if queue.get("queue_version") != QUEUE_VERSION:
        issues.append("missing_or_invalid_queue_version")

    commands = queue.get("offline_validation_commands")
    if not isinstance(commands, list) or not commands:
        issues.append("missing_validation_commands")
    else:
        for index, command in enumerate(commands):
            if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
                issues.append(f"invalid_validation_command_{index}")

    side_effects = queue.get("side_effects")
    if not isinstance(side_effects, Mapping):
        issues.append("missing_side_effect_attestation")
    else:
        for key in (
            "live_extraction_performed",
            "crawler_or_download_performed",
            "devhub_opened",
            "active_requirements_mutated",
            "private_files_written",
        ):
            if side_effects.get(key) is not False:
                issues.append(f"unsafe_side_effect_flag_{key}")

    candidate_ids = queue.get("candidate_requirement_ids")
    if not isinstance(candidate_ids, list) or any(not isinstance(item, str) or not item for item in candidate_ids):
        issues.append("missing_candidate_requirement_ids")

    candidates = queue.get("candidates")
    if not isinstance(candidates, list):
        issues.append("missing_candidates")
    else:
        seen_ids: List[str] = []
        for index, candidate in enumerate(candidates):
            path = f"candidates[{index}]"
            if not isinstance(candidate, Mapping):
                issues.append(f"invalid_candidate_{index}")
                continue
            requirement_id = candidate.get("requirement_id")
            if not isinstance(requirement_id, str) or not requirement_id:
                issues.append(f"{path}.missing_requirement_id")
            else:
                seen_ids.append(requirement_id)
            if not _string_list(candidate.get("citation_placeholder_needs")):
                issues.append(f"{path}.missing_citation_placeholder_needs")
            if not _string_list(candidate.get("extraction_confidence_notes")):
                issues.append(f"{path}.missing_extraction_confidence_notes")
            if not _string_list(candidate.get("blocked_stale_source_dependencies")):
                issues.append(f"{path}.missing_stale_source_dependency_blockers")
            route = candidate.get("human_review_routing")
            if not isinstance(route, Mapping):
                issues.append(f"{path}.missing_human_review_routing")
            else:
                for field in _REQUIRED_HUMAN_REVIEW_FIELDS:
                    if not isinstance(route.get(field), str) or not route.get(field):
                        issues.append(f"{path}.missing_human_review_{field}")
                if route.get("requires_human_before_requirement_mutation") is not True:
                    issues.append(f"{path}.missing_human_review_mutation_gate")
            placeholder = candidate.get("monitoring_placeholder")
            if not isinstance(placeholder, Mapping) or not isinstance(placeholder.get("placeholder_id"), str) or not placeholder.get("placeholder_id"):
                issues.append(f"{path}.missing_public_monitoring_placeholder_reference")
        if isinstance(candidate_ids, list) and sorted(seen_ids) != sorted(candidate_ids):
            issues.append("candidate_requirement_ids_do_not_match_candidates")

    issues.extend(_forbidden_value_issues(queue))
    if issues:
        raise ReextractionCandidateQueueV1Error("; ".join(sorted(set(issues))))


def queue_from_fixture_paths(
    reviewer_dispositions_path: Path,
    public_monitoring_placeholders_path: Path,
) -> Dict[str, Any]:
    """Load fixture files and build the queue."""
    reviewer_rows = load_json_fixture(reviewer_dispositions_path)
    monitoring_placeholders = load_json_fixture(public_monitoring_placeholders_path)
    if not isinstance(reviewer_rows, list):
        raise ValueError("reviewer disposition fixture must contain a JSON array")
    if not isinstance(monitoring_placeholders, list):
        raise ValueError("monitoring placeholder fixture must contain a JSON array")
    return build_reextraction_candidate_queue(reviewer_rows, monitoring_placeholders)


def _index_public_placeholders(
    placeholders: Iterable[Mapping[str, Any]]
) -> Dict[str, Mapping[str, Any]]:
    indexed: Dict[str, Mapping[str, Any]] = {}
    for placeholder in placeholders:
        if placeholder.get("row_kind") != PUBLIC_MONITORING_PLACEHOLDER_KIND:
            continue
        source_id = placeholder.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            continue
        if _validate_public_placeholder(placeholder) is None:
            indexed[source_id] = placeholder
    return indexed


def _validate_public_placeholder(placeholder: Mapping[str, Any]) -> str | None:
    if _forbidden_value_issues(placeholder):
        return "unsafe_public_monitoring_placeholder"
    required_fields = (
        "placeholder_id",
        "source_id",
        "public_source_url",
        "freshness_status",
        "last_public_check_at",
        "citation_placeholder_need",
    )
    for field in required_fields:
        if not isinstance(placeholder.get(field), str) or not placeholder.get(field):
            return f"missing_public_monitoring_placeholder_{field}"
    return None


def _validate_reviewer_row(row: Mapping[str, Any]) -> str | None:
    if row.get("row_kind") != SYNTHETIC_REVIEWER_ROW_KIND:
        return "not_a_synthetic_stale_readiness_reviewer_row"
    if _forbidden_value_issues(row):
        return "unsafe_private_live_mutating_or_overclaiming_row"
    for field in ("requirement_id", "source_id", "reviewer_disposition"):
        if not isinstance(row.get(field), str) or not row.get(field):
            return f"missing_{field}"
    for field in _REQUIRED_REVIEWER_LIST_FIELDS:
        if not _string_list(row.get(field)):
            return f"missing_{field}"
    route = row.get("human_review_routing")
    if not isinstance(route, Mapping):
        return "missing_human_review_routing"
    for field in _REQUIRED_HUMAN_REVIEW_FIELDS:
        if not isinstance(route.get(field), str) or not route.get(field):
            return f"missing_human_review_{field}"
    if route.get("requires_human_before_requirement_mutation") is not True:
        return "missing_human_review_mutation_gate"
    return None


def _citation_placeholder_needs(
    row: Mapping[str, Any], placeholder: Mapping[str, Any]
) -> List[str]:
    needs = _string_list(row.get("citation_placeholder_needs", []))
    if row.get("reviewer_disposition") == "citation_placeholder_required":
        fallback = "citation span must be refreshed from public placeholder before any extraction update"
        if fallback not in needs:
            needs.append(fallback)
    placeholder_need = placeholder.get("citation_placeholder_need")
    if isinstance(placeholder_need, str) and placeholder_need and placeholder_need not in needs:
        needs.append(placeholder_need)
    return sorted(needs)


def _confidence_notes(row: Mapping[str, Any]) -> List[str]:
    notes = _string_list(row.get("extraction_confidence_notes", []))
    stale_reason = row.get("stale_reason")
    if isinstance(stale_reason, str) and stale_reason:
        notes.append(f"stale readiness reviewer note: {stale_reason}")
    return sorted(set(notes))


def _human_review_routing(row: Mapping[str, Any], placeholder: Mapping[str, Any]) -> Dict[str, Any]:
    route = row["human_review_routing"]
    return {
        "review_queue": str(route["review_queue"]),
        "reason": str(route["reason"]),
        "requires_human_before_requirement_mutation": True,
        "public_placeholder_id": str(placeholder["placeholder_id"]),
    }


def _blocked_dependencies(row: Mapping[str, Any], placeholder: Mapping[str, Any]) -> List[str]:
    dependencies = _string_list(row.get("blocked_stale_source_dependencies", []))
    if row.get("reviewer_disposition") == "blocked_stale_source_dependency":
        source_id = str(row.get("source_id", "unknown_source"))
        dependencies.append(f"source freshness must be resolved for {source_id}")
    if placeholder.get("freshness_status") in {"stale", "blocked", "unknown"}:
        dependencies.append(
            "public monitoring placeholder reports "
            + str(placeholder.get("freshness_status"))
            + " freshness"
        )
    return sorted(set(dependencies))


def _forbidden_value_issues(value: Any, path: str = "$", key_name: str = "") -> List[str]:
    issues: List[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}"
            if key_text in _ACTIVE_MUTATION_FLAG_KEYS and item is not False:
                issues.append(f"active_mutation_flag:{child_path}")
            if any(token in key_text for token in _PRIVATE_OR_RAW_KEY_TOKENS):
                issues.append(f"private_or_raw_artifact_reference:{child_path}")
            issues.extend(_forbidden_value_issues(item, child_path, key_text))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(_forbidden_value_issues(item, f"{path}[{index}]", key_name))
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in _FORBIDDEN_TEXT_PHRASES:
            if phrase in lowered:
                issues.append(f"forbidden_claim:{path}")
    return issues


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _skip(row: Mapping[str, Any], reason: str) -> Dict[str, Any]:
    requirement_id = row.get("requirement_id")
    source_id = row.get("source_id")
    return {
        "requirement_id": requirement_id if isinstance(requirement_id, str) else "",
        "source_id": source_id if isinstance(source_id, str) else "",
        "skip_reason": reason,
    }


def _reviewer_row_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    requirement_id = row.get("requirement_id")
    source_id = row.get("source_id")
    return (
        requirement_id if isinstance(requirement_id, str) else "",
        source_id if isinstance(source_id, str) else "",
    )
