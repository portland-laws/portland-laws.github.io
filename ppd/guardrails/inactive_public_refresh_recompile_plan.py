"""Fixture-first inactive public refresh guardrail recompile planner.

This module intentionally consumes only caller-provided synthetic rows. It does not
crawl, download, open DevHub, mutate active guardrails, or perform official
actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

DEFAULT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/guardrails/inactive_public_refresh_recompile_plan.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_inactive_public_refresh_recompile_plan.py"),
)

_BLOCKED_LIVE_ACTION_TERMS = (
    "crawl",
    "download",
    "devhub",
    "submit",
    "certify",
    "cancel",
    "upload",
    "live extraction",
    "official action",
)


@dataclass(frozen=True)
class RecompileInputs:
    """Synthetic input rows for inactive candidate planning."""

    process_model_delta_plan_rows: tuple[dict[str, Any], ...]
    requirement_reextraction_queue_rows: tuple[dict[str, Any], ...]


def _as_tuple_of_dicts(rows: Iterable[dict[str, Any]], label: str) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"{label}[{index}] must be a dict")
        normalized.append(dict(row))
    return tuple(normalized)


def _text_value(row: dict[str, Any], key: str, fallback: str) -> str:
    value = row.get(key)
    if value is None or value == "":
        return fallback
    return str(value)


def _stable_candidate_id(delta_row: dict[str, Any], queue_row: dict[str, Any], index: int) -> str:
    process_id = _text_value(delta_row, "process_model_id", "synthetic-process")
    requirement_id = _text_value(queue_row, "requirement_id", "synthetic-requirement")
    return f"inactive-public-refresh-{process_id}-{requirement_id}-{index:03d}"


def _detect_blocked_terms(rows: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    found: set[str] = set()
    for row in rows:
        text = " ".join(str(value).lower() for value in row.values())
        for term in _BLOCKED_LIVE_ACTION_TERMS:
            if term in text:
                found.add(term)
    return tuple(sorted(found))


def _candidate(delta_row: dict[str, Any], queue_row: dict[str, Any], index: int) -> dict[str, Any]:
    candidate_id = _stable_candidate_id(delta_row, queue_row, index)
    process_id = _text_value(delta_row, "process_model_id", "synthetic-process")
    requirement_id = _text_value(queue_row, "requirement_id", "synthetic-requirement")
    delta_kind = _text_value(delta_row, "delta_kind", "synthetic_delta")
    queue_reason = _text_value(queue_row, "queue_reason", "synthetic_reextraction")

    return {
        "candidate_id": candidate_id,
        "bundle_state": "inactive",
        "source_mode": "fixture_only",
        "source_rows": {
            "process_model_delta_plan_row_id": _text_value(delta_row, "row_id", f"delta-{index:03d}"),
            "requirement_reextraction_queue_row_id": _text_value(queue_row, "row_id", f"queue-{index:03d}"),
        },
        "guardrail_bundle": {
            "bundle_id": f"guardrail-bundle-{candidate_id}",
            "process_model_id": process_id,
            "requirement_id": requirement_id,
            "activation_status": "inactive_hold",
        },
        "deterministic_predicate_placeholder_changes": [
            {
                "predicate_key": f"{process_id}.{requirement_id}.public_refresh_required",
                "placeholder_value": "fixture_recompile_candidate_only",
                "change_reason": f"{delta_kind}:{queue_reason}",
            }
        ],
        "reversible_action_predicate_impacts": [
            {
                "predicate_key": "reversible_action_allowed",
                "impact": "hold_until_offline_validation_passes",
                "exact_confirmation_required": True,
            }
        ],
        "exact_confirmation_predicate_impacts": [
            {
                "predicate_key": "exact_confirmation_text_matches_fixture",
                "impact": "requires_fixture_exact_match_before_activation_review",
            }
        ],
        "refused_action_predicate_impacts": [
            {
                "predicate_key": "live_public_refresh_action_refused",
                "impact": "refuse_live_extraction_crawling_download_devhub_and_official_actions",
            }
        ],
        "explanation_template_refresh_notes": [
            "Refresh explanation templates from synthetic fixture deltas only.",
            "Do not represent this inactive candidate as an active public guardrail.",
        ],
        "validation_status_holds": [
            "inactive_until_fixture_schema_validation_passes",
            "inactive_until_predicate_diff_review_passes",
            "inactive_until_rollback_note_review_passes",
        ],
        "rollback_notes": [
            "Remove the inactive candidate bundle and placeholder predicates.",
            "No active guardrail, process model, or requirement rows are mutated by this plan.",
        ],
    }


def assemble_inactive_public_refresh_recompile_plan(
    process_model_delta_plan_rows: Iterable[dict[str, Any]],
    requirement_reextraction_queue_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Build an inactive recompile plan from synthetic rows only."""

    delta_rows = _as_tuple_of_dicts(process_model_delta_plan_rows, "process_model_delta_plan_rows")
    queue_rows = _as_tuple_of_dicts(requirement_reextraction_queue_rows, "requirement_reextraction_queue_rows")
    blocked_terms = _detect_blocked_terms((*delta_rows, *queue_rows))

    pair_count = min(len(delta_rows), len(queue_rows))
    candidates = [_candidate(delta_rows[index], queue_rows[index], index + 1) for index in range(pair_count)]

    return {
        "plan_id": "inactive-public-refresh-guardrail-recompile-plan-v1",
        "plan_version": 1,
        "execution_mode": "offline_fixture_only",
        "mutates_active_guardrails": False,
        "mutates_process_models": False,
        "mutates_requirements": False,
        "performs_live_extraction": False,
        "performs_live_crawling": False,
        "downloads_documents": False,
        "opens_devhub": False,
        "performs_official_actions": False,
        "input_counts": {
            "process_model_delta_plan_rows": len(delta_rows),
            "requirement_reextraction_queue_rows": len(queue_rows),
            "paired_candidate_rows": pair_count,
        },
        "blocked_live_action_terms_observed_in_fixtures": blocked_terms,
        "inactive_guardrail_bundle_recompile_candidates": candidates,
        "validation_status_holds": [
            "hold_all_candidates_inactive",
            "hold_if_input_rows_are_unpaired",
            "hold_if_blocked_live_action_terms_require_review",
        ],
        "rollback_notes": [
            "Discard generated inactive candidates from the fixture workspace.",
            "No rollback of active public guardrails is required because this planner does not mutate them.",
        ],
        "exact_offline_validation_commands": [list(command) for command in DEFAULT_OFFLINE_VALIDATION_COMMANDS],
    }
