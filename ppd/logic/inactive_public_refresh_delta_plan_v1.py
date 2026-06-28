"""Offline inactive ProcessModel delta planning for public refresh fixtures.

This module is intentionally side-effect free. It accepts already-extracted,
synthetic queue rows and produces inactive placeholders for human review. It
must not crawl, download, open DevHub, mutate active process models, or update
compiled guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

QUEUE_VERSION = "synthetic-public-refresh-requirement-reextraction-queue-v2"
PLAN_VERSION = "inactive-public-refresh-process-model-delta-plan-v1"
INACTIVE_STATUS = "inactive_placeholder"

OFFLINE_VALIDATION_COMMANDS = [
    [
        "python3",
        "-m",
        "py_compile",
        "ppd/logic/inactive_public_refresh_delta_plan_v1.py",
        "ppd/tests/test_inactive_public_refresh_delta_plan_v1.py",
    ],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_public_refresh_delta_plan_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_ROW_FIELDS = {
    "queue_version",
    "row_id",
    "process_id",
    "permit_type",
    "process_stage",
    "change_type",
    "requirement_id",
    "requirement_type",
    "proposed_text",
    "source_evidence_ids",
    "evidence_status",
    "guardrail_bundle_refs",
    "reviewer_groups",
    "rollback_note",
}

_ALLOWED_CHANGE_TYPES = {
    "eligibility_rule",
    "document_requirement",
    "unsupported_path",
    "guardrail_reference",
}

_HOLD_STATUSES = {"stale", "conflicting"}


@dataclass(frozen=True)
class QueueValidationIssue:
    row_id: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"row_id": self.row_id, "reason": self.reason}


@dataclass
class _PlanAccumulator:
    process_model_delta_placeholders: list[dict[str, Any]] = field(default_factory=list)
    stage_level_eligibility_changes: list[dict[str, Any]] = field(default_factory=list)
    document_requirement_changes: list[dict[str, Any]] = field(default_factory=list)
    unsupported_path_notes: list[dict[str, Any]] = field(default_factory=list)
    stale_evidence_holds: list[dict[str, Any]] = field(default_factory=list)
    conflicting_evidence_holds: list[dict[str, Any]] = field(default_factory=list)
    affected_guardrail_bundle_refs: list[dict[str, Any]] = field(default_factory=list)
    reviewer_routing: list[dict[str, Any]] = field(default_factory=list)
    rollback_notes: list[dict[str, Any]] = field(default_factory=list)
    rejected_rows: list[dict[str, str]] = field(default_factory=list)


def build_inactive_public_refresh_delta_plan(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build an inactive public-refresh delta plan from synthetic queue rows.

    Rows with missing fields, non-synthetic queue versions, or unsupported
    change types are rejected into the returned plan instead of raising. This
    keeps validation deterministic for fixture review and prevents partial live
    side effects.
    """

    accumulator = _PlanAccumulator()

    for raw_row in rows:
        row = dict(raw_row)
        issue = _validate_row(row)
        if issue is not None:
            accumulator.rejected_rows.append(issue.as_dict())
            continue

        normalized = _normalize_row(row)
        accumulator.process_model_delta_placeholders.append(_placeholder(normalized))

        change_type = normalized["change_type"]
        if change_type == "eligibility_rule":
            accumulator.stage_level_eligibility_changes.append(_stage_eligibility_change(normalized))
        elif change_type == "document_requirement":
            accumulator.document_requirement_changes.append(_document_requirement_change(normalized))
        elif change_type == "unsupported_path":
            accumulator.unsupported_path_notes.append(_unsupported_path_note(normalized))

        if normalized["evidence_status"] == "stale":
            accumulator.stale_evidence_holds.append(_evidence_hold(normalized, "stale_public_refresh_evidence"))
        elif normalized["evidence_status"] == "conflicting":
            accumulator.conflicting_evidence_holds.append(_evidence_hold(normalized, "conflicting_public_refresh_evidence"))

        for guardrail_bundle_id in normalized["guardrail_bundle_refs"]:
            accumulator.affected_guardrail_bundle_refs.append(
                {
                    "guardrail_bundle_id": guardrail_bundle_id,
                    "process_id": normalized["process_id"],
                    "requirement_id": normalized["requirement_id"],
                    "action": "review_only_no_mutation",
                }
            )

        accumulator.reviewer_routing.append(
            {
                "row_id": normalized["row_id"],
                "process_id": normalized["process_id"],
                "reviewer_groups": normalized["reviewer_groups"],
                "routing_reason": _routing_reason(normalized),
                "requires_human_review": True,
            }
        )
        accumulator.rollback_notes.append(
            {
                "row_id": normalized["row_id"],
                "process_id": normalized["process_id"],
                "rollback_note": normalized["rollback_note"],
                "rollback_scope": "discard_inactive_placeholder_only",
            }
        )

    return _dedupe_plan(
        {
            "plan_version": PLAN_VERSION,
            "queue_version": QUEUE_VERSION,
            "status": INACTIVE_STATUS,
            "source_policy": {
                "input_source": "synthetic_fixture_rows_only",
                "live_extraction": False,
                "live_crawling": False,
                "document_downloads": False,
                "devhub_access": False,
                "active_process_model_mutation": False,
                "active_guardrail_mutation": False,
                "official_actions": False,
            },
            "process_model_delta_placeholders": accumulator.process_model_delta_placeholders,
            "stage_level_eligibility_changes": accumulator.stage_level_eligibility_changes,
            "document_requirement_changes": accumulator.document_requirement_changes,
            "unsupported_path_notes": accumulator.unsupported_path_notes,
            "evidence_holds": {
                "stale": accumulator.stale_evidence_holds,
                "conflicting": accumulator.conflicting_evidence_holds,
            },
            "affected_guardrail_bundle_refs": accumulator.affected_guardrail_bundle_refs,
            "reviewer_routing": accumulator.reviewer_routing,
            "rollback_notes": accumulator.rollback_notes,
            "rejected_rows": accumulator.rejected_rows,
            "validation_commands": OFFLINE_VALIDATION_COMMANDS,
        }
    )


def _validate_row(row: dict[str, Any]) -> QueueValidationIssue | None:
    row_id = str(row.get("row_id", ""))
    missing = sorted(field_name for field_name in _REQUIRED_ROW_FIELDS if field_name not in row)
    if missing:
        return QueueValidationIssue(row_id=row_id, reason="missing fields: " + ", ".join(missing))
    if row.get("queue_version") != QUEUE_VERSION:
        return QueueValidationIssue(row_id=row_id, reason="unsupported queue_version")
    if row.get("change_type") not in _ALLOWED_CHANGE_TYPES:
        return QueueValidationIssue(row_id=row_id, reason="unsupported change_type")
    if row.get("evidence_status") not in {"current", "stale", "conflicting"}:
        return QueueValidationIssue(row_id=row_id, reason="unsupported evidence_status")
    if not _is_string_list(row.get("source_evidence_ids")):
        return QueueValidationIssue(row_id=row_id, reason="source_evidence_ids must be a list of strings")
    if not _is_string_list(row.get("guardrail_bundle_refs")):
        return QueueValidationIssue(row_id=row_id, reason="guardrail_bundle_refs must be a list of strings")
    if not _is_string_list(row.get("reviewer_groups")):
        return QueueValidationIssue(row_id=row_id, reason="reviewer_groups must be a list of strings")
    return None


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    for key in (
        "row_id",
        "process_id",
        "permit_type",
        "process_stage",
        "change_type",
        "requirement_id",
        "requirement_type",
        "proposed_text",
        "evidence_status",
        "rollback_note",
    ):
        normalized[key] = str(normalized[key]).strip()
    normalized["source_evidence_ids"] = sorted(set(normalized["source_evidence_ids"]))
    normalized["guardrail_bundle_refs"] = sorted(set(normalized["guardrail_bundle_refs"]))
    normalized["reviewer_groups"] = sorted(set(normalized["reviewer_groups"]))
    return normalized


def _placeholder(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "delta_id": f"inactive-delta::{row['row_id']}",
        "status": INACTIVE_STATUS,
        "process_id": row["process_id"],
        "permit_type": row["permit_type"],
        "process_stage": row["process_stage"],
        "requirement_id": row["requirement_id"],
        "requirement_type": row["requirement_type"],
        "change_type": row["change_type"],
        "proposed_text": row["proposed_text"],
        "source_evidence_ids": row["source_evidence_ids"],
        "activation_gate": "human_review_and_separate_guardrail_compile_required",
    }


def _stage_eligibility_change(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "process_id": row["process_id"],
        "process_stage": row["process_stage"],
        "eligibility_rule_placeholder": row["proposed_text"],
        "source_evidence_ids": row["source_evidence_ids"],
        "status": INACTIVE_STATUS,
    }


def _document_requirement_change(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "process_id": row["process_id"],
        "process_stage": row["process_stage"],
        "document_requirement_placeholder": row["proposed_text"],
        "source_evidence_ids": row["source_evidence_ids"],
        "status": INACTIVE_STATUS,
    }


def _unsupported_path_note(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "process_id": row["process_id"],
        "process_stage": row["process_stage"],
        "unsupported_path_note": row["proposed_text"],
        "source_evidence_ids": row["source_evidence_ids"],
        "status": INACTIVE_STATUS,
    }


def _evidence_hold(row: dict[str, Any], hold_type: str) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "process_id": row["process_id"],
        "requirement_id": row["requirement_id"],
        "hold_type": hold_type,
        "source_evidence_ids": row["source_evidence_ids"],
        "resolution_required_before_activation": True,
    }


def _routing_reason(row: dict[str, Any]) -> str:
    if row["evidence_status"] in _HOLD_STATUSES:
        return f"{row['evidence_status']}_evidence_requires_review"
    if row["change_type"] == "guardrail_reference":
        return "guardrail_bundle_reference_requires_review"
    return f"{row['change_type']}_requires_review"


def _dedupe_plan(plan: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "affected_guardrail_bundle_refs",
        "reviewer_routing",
        "rollback_notes",
    ):
        plan[key] = _dedupe_dicts(plan[key])
    return plan


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        fingerprint = tuple(sorted((key, repr(value)) for key, value in item.items()))
        if fingerprint not in seen:
            seen.add(fingerprint)
            deduped.append(item)
    return deduped
