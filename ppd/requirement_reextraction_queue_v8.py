"""Fixture-first downstream requirement re-extraction queue v8.

This module intentionally consumes committed JSON fixtures only. It does not crawl,
download, authenticate, submit, upload, schedule, pay, certify, mutate active
records, or provide legal or permitting assurances.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

OFFLINE_VALIDATION_COMMANDS: List[List[str]] = [
    ["python3", "-m", "py_compile", "ppd/requirement_reextraction_queue_v8.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_queue_v8.py"],
]

CHANGED_STATUSES = {"changed", "new", "removed", "stale"}
HOLD_STATUSES = {"ambiguous", "conflict", "missing_inventory", "manual_review"}

FORBIDDEN_POPULATED_KEYS = {
    "active_guardrail_mutation",
    "active_mutation",
    "active_mutation_flags",
    "active_process_model_mutation",
    "active_requirement_mutation",
    "auth_artifacts",
    "auth_state_path",
    "certification_completed",
    "crawl_output_path",
    "crawl_run_id",
    "crawled_live",
    "devhub_session_path",
    "downloaded_artifacts",
    "downloaded_document_path",
    "guaranteed_approval",
    "legal_guarantee",
    "live_crawl_executed",
    "live_crawl_execution_claims",
    "mutation_enabled",
    "official_action_completed",
    "payment_completed",
    "permit_submitted",
    "permitting_guarantee",
    "private_artifacts",
    "raw_crawl_artifacts",
    "raw_html_path",
    "scheduled_inspection",
    "session_artifacts",
    "session_cookie_path",
    "storage_state_path",
    "submission_completed",
    "submit_enabled",
    "trace_path",
    "upload_completed",
    "writes_enabled",
}

FORBIDDEN_TEXT = (
    "active mutation",
    "auth artifact",
    "downloaded artifact",
    "guaranteed approval",
    "legal guarantee",
    "live crawl executed",
    "official action completed",
    "permit submitted",
    "permitting guarantee",
    "private session",
    "raw crawl artifact",
)


@dataclass(frozen=True)
class SourceDiff:
    source_id: str
    freshness_status: str
    evidence_ref: str
    changed_sections: Sequence[str]
    reviewer_note: str = ""


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    source_id: str
    permit_type: str
    process_stage: str
    title: str
    last_verified: str


@dataclass(frozen=True)
class QueueValidationError:
    path: str
    message: str


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_string(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing string field {key!r} in {row!r}")
    return value


def _load_source_diffs(path: Path) -> List[SourceDiff]:
    payload = _read_json(path)
    rows = payload.get("source_freshness_diffs") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("source freshness fixture must contain source_freshness_diffs list")

    diffs: List[SourceDiff] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("source freshness diff rows must be objects")
        sections = row.get("changed_sections", [])
        if not isinstance(sections, list) or not all(isinstance(item, str) for item in sections):
            raise ValueError("changed_sections must be a list of strings")
        diffs.append(
            SourceDiff(
                source_id=_require_string(row, "source_id"),
                freshness_status=_require_string(row, "freshness_status"),
                evidence_ref=_require_string(row, "evidence_ref"),
                changed_sections=tuple(sections),
                reviewer_note=str(row.get("reviewer_note", "")),
            )
        )
    return diffs


def _load_requirements(path: Path) -> List[Requirement]:
    payload = _read_json(path)
    rows = payload.get("requirements") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("requirement inventory fixture must contain requirements list")

    requirements: List[Requirement] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("requirement inventory rows must be objects")
        requirements.append(
            Requirement(
                requirement_id=_require_string(row, "requirement_id"),
                source_id=_require_string(row, "source_id"),
                permit_type=_require_string(row, "permit_type"),
                process_stage=_require_string(row, "process_stage"),
                title=_require_string(row, "title"),
                last_verified=_require_string(row, "last_verified"),
            )
        )
    return requirements


def _group_requirements(requirements: Iterable[Requirement]) -> Dict[str, List[Requirement]]:
    grouped: Dict[str, List[Requirement]] = {}
    for requirement in requirements:
        grouped.setdefault(requirement.source_id, []).append(requirement)
    for rows in grouped.values():
        rows.sort(key=lambda item: (item.permit_type, item.process_stage, item.requirement_id))
    return grouped


def _candidate_priority(status: str) -> int:
    if status == "removed":
        return 0
    if status == "changed":
        return 1
    if status == "new":
        return 2
    if status == "stale":
        return 3
    return 9


def build_reextraction_queue(source_freshness_diff_fixture: Path, requirement_inventory_fixture: Path) -> Dict[str, Any]:
    diffs = _load_source_diffs(source_freshness_diff_fixture)
    requirements = _load_requirements(requirement_inventory_fixture)
    requirements_by_source = _group_requirements(requirements)

    candidates: List[Dict[str, Any]] = []
    evidence_refs: List[Dict[str, str]] = []
    grouping_rows: List[Dict[str, str]] = []
    carry_forward_rows: List[Dict[str, str]] = []
    reviewer_hold_reasons: List[Dict[str, str]] = []

    for diff in sorted(diffs, key=lambda item: (_candidate_priority(item.freshness_status), item.source_id)):
        source_requirements = requirements_by_source.get(diff.source_id, [])
        evidence_refs.append(
            {
                "source_id": diff.source_id,
                "evidence_ref": diff.evidence_ref,
                "freshness_status": diff.freshness_status,
            }
        )

        if diff.freshness_status in HOLD_STATUSES:
            reviewer_hold_reasons.append(
                {
                    "source_id": diff.source_id,
                    "hold_reason": diff.reviewer_note or f"requires reviewer decision for {diff.freshness_status}",
                    "evidence_ref": diff.evidence_ref,
                }
            )
            continue

        if diff.freshness_status in CHANGED_STATUSES:
            if not source_requirements:
                reviewer_hold_reasons.append(
                    {
                        "source_id": diff.source_id,
                        "hold_reason": "source freshness changed but no existing requirement inventory row was available",
                        "evidence_ref": diff.evidence_ref,
                    }
                )
                continue
            for requirement in source_requirements:
                candidates.append(
                    {
                        "candidate_id": f"reextract::{requirement.requirement_id}",
                        "requirement_id": requirement.requirement_id,
                        "source_id": requirement.source_id,
                        "permit_type": requirement.permit_type,
                        "process_stage": requirement.process_stage,
                        "freshness_status": diff.freshness_status,
                        "changed_sections": list(diff.changed_sections),
                        "evidence_ref": diff.evidence_ref,
                    }
                )
                grouping_rows.append(
                    {
                        "permit_type": requirement.permit_type,
                        "process_stage": requirement.process_stage,
                        "requirement_id": requirement.requirement_id,
                        "source_id": requirement.source_id,
                    }
                )
            continue

        for requirement in source_requirements:
            carry_forward_rows.append(
                {
                    "requirement_id": requirement.requirement_id,
                    "source_id": requirement.source_id,
                    "permit_type": requirement.permit_type,
                    "process_stage": requirement.process_stage,
                    "carry_forward_reason": "source freshness unchanged in fixture intake v8",
                    "last_verified": requirement.last_verified,
                }
            )

    candidates.sort(key=lambda item: (item["permit_type"], item["process_stage"], item["source_id"], item["requirement_id"]))
    grouping_rows.sort(key=lambda item: (item["permit_type"], item["process_stage"], item["requirement_id"]))
    carry_forward_rows.sort(key=lambda item: (item["permit_type"], item["process_stage"], item["requirement_id"]))
    reviewer_hold_reasons.sort(key=lambda item: item["source_id"])

    queue = {
        "queue_version": "v8",
        "fixture_only": True,
        "source_freshness_diff_ref": str(source_freshness_diff_fixture),
        "requirement_inventory_ref": str(requirement_inventory_fixture),
        "live_actions_performed": [],
        "reextraction_candidates": candidates,
        "affected_source_evidence_refs": evidence_refs,
        "permit_type_process_stage_grouping_rows": grouping_rows,
        "unchanged_requirement_carry_forward_rows": carry_forward_rows,
        "reviewer_hold_reasons": reviewer_hold_reasons,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "scope_note": "Fixture assembly only; no official action or advice is represented.",
    }
    assert_valid_reextraction_queue(queue)
    return queue


def validate_reextraction_queue(payload: Mapping[str, Any]) -> List[QueueValidationError]:
    errors: List[QueueValidationError] = []

    if payload.get("queue_version") != "v8":
        errors.append(QueueValidationError("queue_version", "queue must declare v8"))
    if payload.get("fixture_only") is not True:
        errors.append(QueueValidationError("fixture_only", "queue must be fixture-only"))
    if payload.get("live_actions_performed") != []:
        errors.append(QueueValidationError("live_actions_performed", "queue must not claim live actions"))

    for field in ("source_freshness_diff_ref", "requirement_inventory_ref"):
        if _is_missing(payload.get(field)):
            errors.append(QueueValidationError(field, "required fixture reference is missing or empty"))

    candidates = payload.get("reextraction_candidates")
    grouping_rows = payload.get("permit_type_process_stage_grouping_rows")
    carry_forward_rows = payload.get("unchanged_requirement_carry_forward_rows")
    evidence_refs = payload.get("affected_source_evidence_refs")
    reviewer_hold_reasons = payload.get("reviewer_hold_reasons")

    if not _is_non_empty_list(candidates):
        errors.append(QueueValidationError("reextraction_candidates", "ordered re-extraction candidates are required"))
    elif not _has_required_strings(candidates, "reextraction_candidates", ("candidate_id", "requirement_id", "source_id", "permit_type", "process_stage", "freshness_status", "evidence_ref"), errors):
        pass
    else:
        expected = sorted(candidates, key=lambda item: (item["permit_type"], item["process_stage"], item["source_id"], item["requirement_id"]))
        if list(candidates) != expected:
            errors.append(QueueValidationError("reextraction_candidates", "candidates must be deterministically ordered"))

    if not _is_non_empty_list(evidence_refs):
        errors.append(QueueValidationError("affected_source_evidence_refs", "affected source evidence references are required"))
    else:
        _has_required_strings(evidence_refs, "affected_source_evidence_refs", ("source_id", "evidence_ref", "freshness_status"), errors)

    if not _is_non_empty_list(grouping_rows):
        errors.append(QueueValidationError("permit_type_process_stage_grouping_rows", "permit-type and process-stage grouping rows are required"))
    else:
        _has_required_strings(grouping_rows, "permit_type_process_stage_grouping_rows", ("permit_type", "process_stage", "requirement_id", "source_id"), errors)

    if not _is_non_empty_list(carry_forward_rows):
        errors.append(QueueValidationError("unchanged_requirement_carry_forward_rows", "unchanged requirement carry-forward rows are required"))
    else:
        _has_required_strings(carry_forward_rows, "unchanged_requirement_carry_forward_rows", ("requirement_id", "source_id", "permit_type", "process_stage", "carry_forward_reason", "last_verified"), errors)

    if not _is_non_empty_list(reviewer_hold_reasons):
        errors.append(QueueValidationError("reviewer_hold_reasons", "reviewer hold reasons are required"))
    else:
        _has_required_strings(reviewer_hold_reasons, "reviewer_hold_reasons", ("source_id", "hold_reason", "evidence_ref"), errors)

    if not _is_validation_commands(payload.get("offline_validation_commands")):
        errors.append(QueueValidationError("offline_validation_commands", "validation commands must be non-empty argv lists"))

    if _is_non_empty_list(candidates) and _is_non_empty_list(grouping_rows):
        candidate_keys = {(row.get("requirement_id"), row.get("source_id"), row.get("permit_type"), row.get("process_stage")) for row in candidates if isinstance(row, Mapping)}
        grouping_keys = {(row.get("requirement_id"), row.get("source_id"), row.get("permit_type"), row.get("process_stage")) for row in grouping_rows if isinstance(row, Mapping)}
        if candidate_keys != grouping_keys:
            errors.append(QueueValidationError("permit_type_process_stage_grouping_rows", "grouping rows must exactly cover re-extraction candidates"))

    if _is_non_empty_list(evidence_refs):
        evidence_sources = {row.get("source_id") for row in evidence_refs if isinstance(row, Mapping)}
        referenced_sources = set()
        for section in (candidates, carry_forward_rows, reviewer_hold_reasons):
            if isinstance(section, Sequence) and not isinstance(section, (str, bytes)):
                referenced_sources.update(row.get("source_id") for row in section if isinstance(row, Mapping))
        if referenced_sources and not referenced_sources.issubset(evidence_sources):
            errors.append(QueueValidationError("affected_source_evidence_refs", "evidence rows must cover every candidate, carry-forward, and hold source"))

    errors.extend(_find_forbidden_values(payload, "queue"))
    return errors


def assert_valid_reextraction_queue(payload: Mapping[str, Any]) -> None:
    errors = validate_reextraction_queue(payload)
    if errors:
        details = "; ".join(f"{error.path}: {error.message}" for error in errors)
        raise ValueError(details)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return len(value) == 0
    return False


def _is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _has_required_strings(rows: Any, path: str, fields: Sequence[str], errors: List[QueueValidationError]) -> bool:
    valid = True
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        errors.append(QueueValidationError(path, "section must be a list"))
        return False
    for index, row in enumerate(rows):
        row_path = f"{path}[{index}]"
        if not isinstance(row, Mapping):
            errors.append(QueueValidationError(row_path, "row must be an object"))
            valid = False
            continue
        for field in fields:
            if _is_missing(row.get(field)):
                errors.append(QueueValidationError(f"{row_path}.{field}", "required field is missing or empty"))
                valid = False
    return valid


def _is_validation_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)) or not command:
            return False
        if not all(isinstance(part, str) and part.strip() for part in command):
            return False
    return True


def _find_forbidden_values(value: Any, path: str) -> List[QueueValidationError]:
    errors: List[QueueValidationError] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_text = str(key).strip().lower()
            if key_text in FORBIDDEN_POPULATED_KEYS and not _is_missing(child):
                errors.append(QueueValidationError(child_path, "forbidden crawl/session/action/guarantee/mutation field is populated"))
            errors.extend(_find_forbidden_values(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            errors.extend(_find_forbidden_values(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in FORBIDDEN_TEXT:
            if phrase in lowered:
                errors.append(QueueValidationError(path, f"forbidden claim text: {phrase}"))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PP&D fixture-only requirement re-extraction queue v8.")
    parser.add_argument("source_freshness_diff_fixture", type=Path)
    parser.add_argument("requirement_inventory_fixture", type=Path)
    args = parser.parse_args()
    result = build_reextraction_queue(args.source_freshness_diff_fixture, args.requirement_inventory_fixture)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
