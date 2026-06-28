"""Fixture-first combined public and DevHub stale-readiness packet v1.

The builder in this module only consumes committed fixtures. It does not crawl
public sources, open DevHub, store browser state, download documents, fill forms,
submit anything, or mutate active prompt, guardrail, process, source, release, or
daemon state.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PACKET_VERSION = "combined-public-devhub-stale-readiness-packet-v1"

_FORBIDDEN_KEYS = {
    "auth_state",
    "browser_context",
    "cookies",
    "credential",
    "credentials",
    "devhub_session",
    "downloaded_document",
    "downloaded_document_path",
    "file_path",
    "form_submission",
    "har",
    "local_private_path",
    "password",
    "payment_data",
    "private_file",
    "raw_body",
    "raw_crawl_output",
    "raw_html",
    "response_body",
    "screenshot",
    "session_cookie",
    "session_state",
    "token",
    "trace",
    "upload_payload",
}

_FALSE_FLAGS = (
    "live_crawl_performed",
    "devhub_opened",
    "auth_state_stored",
    "private_files_stored",
    "form_filling_performed",
    "upload_performed",
    "submission_performed",
    "certification_performed",
    "payment_performed",
    "inspection_scheduling_performed",
    "release_promotion_performed",
    "active_prompt_mutated",
    "active_guardrail_mutated",
    "active_process_model_mutated",
    "active_requirement_mutated",
    "active_contract_mutated",
    "active_source_mutated",
    "active_archive_mutated",
    "active_document_mutated",
    "active_devhub_surface_mutated",
    "active_crawler_mutated",
    "active_release_mutated",
    "active_daemon_state_mutated",
)

_REJECT_PUBLIC_OUTCOMES = {"failed", "missing", "blocked_by_policy", "invalid"}
_HOLD_PUBLIC_OUTCOMES = {"changed", "stale", "needs_review"}
_REJECT_SURFACE_DELTAS = {"broken", "removed", "unsafe"}
_HOLD_SURFACE_DELTAS = {"changed", "new_read_only_delta", "selector_drift"}
_REJECT_IMPACTS = {"blocking", "unsafe"}
_HOLD_IMPACTS = {"limited", "needs_review", "caution"}

_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/stale_readiness_packet_v1.py", "ppd/tests/test_stale_readiness_packet_v1.py"],
    ["python3", "ppd/tests/test_stale_readiness_packet_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]


def load_json_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed JSON fixture as an object."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("stale-readiness fixture must be a JSON object")
    return data


def offline_validation_commands() -> list[list[str]]:
    """Return exact offline validation commands for this packet."""

    return [list(command) for command in _OFFLINE_VALIDATION_COMMANDS]


def build_stale_readiness_packet_v1(fixture: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    """Build the combined stale-readiness packet from offline fixtures only."""

    source = _load_fixture(fixture)
    _reject_forbidden_or_active_state(source)

    public_rows = _rows_by_target(source.get("synthetic_public_monitoring_outcomes", []), "source_id")
    hold_rows = _rows_by_target(source.get("stale_source_agent_holds", []), "target_id")
    surface_rows = _rows_by_target(source.get("devhub_read_only_surface_deltas", []), "surface_id")
    impact_rows = _rows_by_target(source.get("devhub_agent_impacts", []), "target_id")

    target_ids = sorted(set(public_rows) | set(hold_rows) | set(surface_rows) | set(impact_rows))
    recommendations = [_recommendation_for_target(target_id, public_rows, hold_rows, surface_rows, impact_rows) for target_id in target_ids]
    dependency_order = _dependency_order(source.get("dependency_edges", []), target_ids)
    order_index = {target_id: index + 1 for index, target_id in enumerate(dependency_order)}

    ordered_recommendations = sorted(
        (
            dict(recommendation, dependency_order=order_index.get(str(recommendation["target_id"]), len(order_index) + 1))
            for recommendation in recommendations
        ),
        key=lambda row: (int(row["dependency_order"]), str(row["target_id"])),
    )

    packet = {
        "packet_version": PACKET_VERSION,
        "packet_id": str(source.get("packet_id", "fixture-combined-public-devhub-stale-readiness-v1")),
        "generation_mode": "fixture_first_offline_synthetic_reconciliation",
        "source_fixture_id": str(source.get("fixture_id", "unknown-fixture")),
        "live_crawl_performed": False,
        "devhub_opened": False,
        "auth_state_stored": False,
        "private_files_stored": False,
        "form_filling_performed": False,
        "upload_performed": False,
        "submission_performed": False,
        "certification_performed": False,
        "payment_performed": False,
        "inspection_scheduling_performed": False,
        "release_promotion_performed": False,
        "active_prompt_mutated": False,
        "active_guardrail_mutated": False,
        "active_process_model_mutated": False,
        "active_requirement_mutated": False,
        "active_contract_mutated": False,
        "active_source_mutated": False,
        "active_archive_mutated": False,
        "active_document_mutated": False,
        "active_devhub_surface_mutated": False,
        "active_crawler_mutated": False,
        "active_release_mutated": False,
        "active_daemon_state_mutated": False,
        "dependency_edges": _dependency_edges(source.get("dependency_edges", [])),
        "dependency_order": dependency_order,
        "readiness_recommendations": ordered_recommendations,
        "reviewer_routing": _reviewer_routing(ordered_recommendations),
        "rollback_notes": _rollback_notes(ordered_recommendations),
        "exact_offline_validation_commands": offline_validation_commands(),
    }
    require_valid_stale_readiness_packet_v1(packet)
    return packet


def validate_stale_readiness_packet_v1(packet: Mapping[str, Any]) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return ValidationResult(False, ("packet must be a JSON object",))
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be combined-public-devhub-stale-readiness-packet-v1")
    _collect_forbidden(packet, "packet", errors)
    for flag in _FALSE_FLAGS:
        if _truthy(packet.get(flag)):
            errors.append(f"{flag} must be false or absent")
    recommendations = packet.get("readiness_recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        errors.append("readiness_recommendations must be a non-empty list")
        recommendations = []
    seen = set()
    decision_values = set()
    for index, row in enumerate(recommendations):
        path = f"readiness_recommendations[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{path} must be a JSON object")
            continue
        target_id = row.get("target_id")
        decision = row.get("recommendation")
        if not isinstance(target_id, str) or not target_id:
            errors.append(f"{path}.target_id must be a non-empty string")
        elif target_id in seen:
            errors.append(f"duplicate target_id {target_id}")
        else:
            seen.add(target_id)
        if decision not in {"proceed", "hold", "reject"}:
            errors.append(f"{path}.recommendation must be proceed, hold, or reject")
        else:
            decision_values.add(str(decision))
        for key in ("reasons", "reviewer_routing", "rollback_notes", "exact_offline_validation_commands"):
            if not isinstance(row.get(key), list) or not row.get(key):
                errors.append(f"{path}.{key} must be a non-empty list")
    if not {"proceed", "hold", "reject"}.issubset(decision_values):
        errors.append("readiness_recommendations must include proceed, hold, and reject outcomes")
    if packet.get("exact_offline_validation_commands") != offline_validation_commands():
        errors.append("exact_offline_validation_commands must match the module offline validation commands")
    return ValidationResult(not errors, tuple(errors))


def require_valid_stale_readiness_packet_v1(packet: Mapping[str, Any]) -> None:
    result = validate_stale_readiness_packet_v1(packet)
    if not result.ok:
        raise ValueError("invalid stale-readiness packet v1: " + "; ".join(result.errors))


def _load_fixture(value: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(value, (str, Path)):
        return load_json_fixture(value)
    if not isinstance(value, Mapping):
        raise ValueError("fixture must be a JSON object or fixture path")
    return value


def _rows_by_target(value: Any, target_key: str) -> dict[str, list[Mapping[str, Any]]]:
    if value is None:
        return {}
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{target_key} rows must be a list")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{target_key} row must be a JSON object")
        target_id = str(item.get(target_key) or item.get("source_id") or item.get("surface_id") or item.get("target_id") or "").strip()
        if not target_id:
            raise ValueError(f"{target_key} row is missing target identifier")
        grouped.setdefault(target_id, []).append(item)
    return grouped


def _recommendation_for_target(
    target_id: str,
    public_rows: Mapping[str, list[Mapping[str, Any]]],
    hold_rows: Mapping[str, list[Mapping[str, Any]]],
    surface_rows: Mapping[str, list[Mapping[str, Any]]],
    impact_rows: Mapping[str, list[Mapping[str, Any]]],
) -> dict[str, Any]:
    reasons: list[str] = []
    reviewers: set[str] = set()
    rollback: list[str] = []
    decision = "proceed"

    for row in public_rows.get(target_id, []):
        outcome = str(row.get("outcome", "unknown"))
        if outcome in _REJECT_PUBLIC_OUTCOMES:
            decision = "reject"
            reasons.append(f"public monitoring outcome is {outcome}")
            reviewers.add("public-source-monitor-reviewer")
        elif outcome in _HOLD_PUBLIC_OUTCOMES and decision != "reject":
            decision = "hold"
            reasons.append(f"public monitoring outcome is {outcome}")
            reviewers.add("public-source-monitor-reviewer")
    for row in hold_rows.get(target_id, []):
        status = str(row.get("hold_status", "active"))
        if status == "active" and decision != "reject":
            decision = "hold"
            reasons.append(f"stale-source agent hold is active: {row.get('hold_id', 'unidentified-hold')}")
            reviewers.add("agent-safety-reviewer")
    for row in surface_rows.get(target_id, []):
        delta = str(row.get("delta_status", "unknown"))
        if row.get("read_only") is not True:
            decision = "reject"
            reasons.append("DevHub surface delta is not marked read-only")
            reviewers.add("devhub-surface-reviewer")
        elif delta in _REJECT_SURFACE_DELTAS:
            decision = "reject"
            reasons.append(f"DevHub read-only surface delta is {delta}")
            reviewers.add("devhub-surface-reviewer")
        elif delta in _HOLD_SURFACE_DELTAS and decision != "reject":
            decision = "hold"
            reasons.append(f"DevHub read-only surface delta is {delta}")
            reviewers.add("devhub-surface-reviewer")
    for row in impact_rows.get(target_id, []):
        impact = str(row.get("impact_level", "unknown"))
        if impact in _REJECT_IMPACTS:
            decision = "reject"
            reasons.append(f"DevHub agent impact is {impact}")
            reviewers.add("agent-safety-reviewer")
        elif impact in _HOLD_IMPACTS and decision != "reject":
            decision = "hold"
            reasons.append(f"DevHub agent impact is {impact}")
            reviewers.add("agent-safety-reviewer")

    if not reasons:
        reasons.append("public monitoring, stale-source holds, DevHub read-only deltas, and agent impacts are all fixture-cleared")
    if not reviewers:
        reviewers.add("release-readiness-reviewer")
    rollback.append("Keep this fixture packet out of active release promotion until reviewer disposition is recorded.")
    rollback.append("If the recommendation is disputed, discard the generated packet and rerun only the listed offline validation commands after fixture correction.")

    return {
        "target_id": target_id,
        "recommendation": decision,
        "reasons": reasons,
        "reviewer_routing": sorted(reviewers),
        "rollback_notes": rollback,
        "exact_offline_validation_commands": offline_validation_commands(),
    }


def _dependency_edges(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("dependency_edges must be a list")
    edges: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("dependency edge must be a JSON object")
        before = str(item.get("before", "")).strip()
        after = str(item.get("after", "")).strip()
        reason = str(item.get("reason", "fixture dependency ordering"))
        if not before or not after:
            raise ValueError("dependency edge requires before and after")
        edges.append({"before": before, "after": after, "reason": reason})
    return edges


def _dependency_order(value: Any, target_ids: Sequence[str]) -> list[str]:
    edges = _dependency_edges(value)
    ordered: list[str] = []
    remaining = set(str(target_id) for target_id in target_ids)
    before_map: dict[str, set[str]] = {target_id: set() for target_id in remaining}
    for edge in edges:
        if edge["after"] in remaining and edge["before"] in remaining:
            before_map[edge["after"]].add(edge["before"])
    while remaining:
        ready = sorted(target_id for target_id in remaining if not before_map[target_id] - set(ordered))
        if not ready:
            raise ValueError("dependency_edges contain a cycle")
        ordered.extend(ready)
        remaining.difference_update(ready)
    return ordered


def _reviewer_routing(recommendations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in recommendations:
        for reviewer in row.get("reviewer_routing", []):
            rows.append({
                "target_id": str(row.get("target_id")),
                "reviewer": str(reviewer),
                "recommendation": str(row.get("recommendation")),
                "routing_status": "pending_human_review",
            })
    return rows


def _rollback_notes(recommendations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "target_id": str(row.get("target_id")),
            "recommendation": str(row.get("recommendation")),
            "rollback_note": "This packet is fixture-only; rollback means discarding the generated packet and retaining the prior active release state unchanged.",
        }
        for row in recommendations
    ]


def _reject_forbidden_or_active_state(value: Any) -> None:
    errors: list[str] = []
    _collect_forbidden(value, "fixture", errors)
    if isinstance(value, Mapping):
        for flag in _FALSE_FLAGS:
            if _truthy(value.get(flag)):
                errors.append(f"fixture.{flag} must be false or absent")
    if errors:
        raise ValueError("unsafe stale-readiness fixture: " + "; ".join(errors))


def _collect_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in _FORBIDDEN_KEYS:
                errors.append(f"forbidden key present at {child_path}")
            _collect_forbidden(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden(child, f"{path}[{index}]", errors)


def _truthy(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


if __name__ == "__main__":
    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "stale_readiness_packet_v1" / "combined_public_devhub_stale_readiness_fixture.json"
    print(json.dumps(build_stale_readiness_packet_v1(fixture_path), indent=2, sort_keys=True))
