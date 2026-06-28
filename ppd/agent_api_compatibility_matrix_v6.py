"""Fixture-first PP&D agent API compatibility matrix v6.

This module is intentionally offline-only. It summarizes agent API behavior from
committed inactive smoke replay and rollback drill fixtures and rejects fixtures
or matrix packets that look active, authenticated, private, live-derived,
officially complete, legally conclusive, or capable of mutating active state.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ALLOWED_FIXTURE_CLASSES = {"inactive_smoke_replay", "inactive_rollback_drill"}
ALLOWED_STATUSES = {"inactive"}
REQUIRED_TOP_LEVEL_KEYS = {
    "fixture_id",
    "fixture_class",
    "status",
    "source_scope",
    "agent_queries",
    "blocked_action_classes",
    "stale_evidence_behavior",
    "missing_information_prompts",
    "reversible_draft_boundaries",
    "local_pdf_preview_boundaries",
    "exact_confirmation_checkpoints",
    "manual_handoff_surfaces",
    "offline_validation_commands",
}
REQUIRED_MATRIX_LISTS = {
    "smoke_replay_fixture_refs": "missing smoke replay references",
    "rollback_drill_fixture_refs": "missing rollback drill references",
    "supported_agent_queries": "missing supported query rows",
    "blocked_action_classes": "missing blocked action classes",
    "stale_evidence_behavior": "missing stale-evidence behavior",
    "missing_information_prompts": "missing missing-information prompts",
    "reversible_draft_boundaries": "missing reversible draft boundaries",
    "local_pdf_preview_boundaries": "missing local PDF preview boundaries",
    "exact_confirmation_checkpoints": "missing exact-confirmation checkpoints",
    "manual_handoff_surfaces": "missing manual handoff surfaces",
    "offline_validation_commands": "missing validation commands",
    "validation_commands": "missing validation commands",
}
FORBIDDEN_PRIVATE_MARKERS = {
    "auth_state",
    "cookie",
    "credential",
    "devhub_session",
    "har",
    "mfa_secret",
    "password",
    "payment_detail",
    "private_document",
    "raw_download",
    "session_storage",
    "screenshot",
    "trace",
    "upload_payload",
}
FORBIDDEN_CLAIM_MARKERS = {
    "active activation complete",
    "active guardrail activated",
    "activated guardrails in production",
    "crawl live sites now",
    "crawled live ppd",
    "executed live crawl",
    "legal guarantee",
    "permit guaranteed",
    "permitting guarantee",
    "official action completed",
    "official submission completed",
    "payment completed",
    "scheduled inspection completed",
    "submitted to devhub",
    "uploaded to official record",
}
ACTIVE_MUTATION_FLAG_KEYS = {
    "active_activation",
    "active_mutation",
    "activate_guardrails",
    "executes_live_crawl",
    "live_crawl_executed",
    "mutates_active_guardrails",
    "official_action_completed",
    "writes_active_state",
}


class CompatibilityMatrixError(ValueError):
    """Raised when a fixture or matrix cannot be used offline."""


@dataclass(frozen=True)
class CompatibilityFixture:
    fixture_id: str
    fixture_class: str
    status: str
    source_scope: str
    agent_queries: tuple[str, ...]
    blocked_action_classes: tuple[str, ...]
    stale_evidence_behavior: tuple[str, ...]
    missing_information_prompts: tuple[str, ...]
    reversible_draft_boundaries: tuple[str, ...]
    local_pdf_preview_boundaries: tuple[str, ...]
    exact_confirmation_checkpoints: tuple[str, ...]
    manual_handoff_surfaces: tuple[str, ...]
    offline_validation_commands: tuple[tuple[str, ...], ...]


def _as_string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise CompatibilityMatrixError(f"{field_name} must be a non-empty list of strings")
    return tuple(value)


def _as_command_tuple(value: Any, field_name: str) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, list) or not value:
        raise CompatibilityMatrixError(f"{field_name} must be a non-empty list of command arrays")
    commands: list[tuple[str, ...]] = []
    for command in value:
        if not isinstance(command, list) or not command:
            raise CompatibilityMatrixError(f"{field_name} entries must be non-empty arrays")
        if not all(isinstance(part, str) and part for part in command):
            raise CompatibilityMatrixError(f"{field_name} entries must contain only non-empty strings")
        commands.append(tuple(command))
    return tuple(commands)


def _truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "active", "complete", "completed", "enabled", "executed", "true", "yes"}
    if isinstance(value, (int, float)):
        return value != 0
    return value is not None


def _forbidden_reasons(value: Any, path: str = "$.") -> list[str]:
    reasons: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered_key = str(key).lower()
            child_path = f"{path}{key}"
            if lowered_key in FORBIDDEN_PRIVATE_MARKERS:
                reasons.append(f"{child_path} contains private/session/auth artifact marker")
            if lowered_key in ACTIVE_MUTATION_FLAG_KEYS and _truthy_flag(item):
                reasons.append(f"{child_path} contains active mutation or activation flag")
            reasons.extend(_forbidden_reasons(item, f"{child_path}."))
        return reasons
    if isinstance(value, list):
        for index, item in enumerate(value):
            reasons.extend(_forbidden_reasons(item, f"{path}[{index}]."))
        return reasons
    if isinstance(value, str):
        lowered = value.lower()
        for marker in sorted(FORBIDDEN_PRIVATE_MARKERS):
            if marker in lowered:
                reasons.append(f"{path.rstrip('.')} contains private/session/auth artifact marker {marker!r}")
        for marker in sorted(FORBIDDEN_CLAIM_MARKERS):
            if marker in lowered:
                reasons.append(f"{path.rstrip('.')} contains prohibited claim {marker!r}")
    return reasons


def _raise_forbidden(value: Any) -> None:
    reasons = _forbidden_reasons(value)
    if reasons:
        raise CompatibilityMatrixError("; ".join(reasons))


def load_fixture(path: Path) -> CompatibilityFixture:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompatibilityMatrixError(f"{path} must contain a JSON object")
    missing = REQUIRED_TOP_LEVEL_KEYS.difference(payload)
    if missing:
        raise CompatibilityMatrixError(f"{path} is missing keys: {', '.join(sorted(missing))}")
    _raise_forbidden(payload)
    fixture_class = payload["fixture_class"]
    status = payload["status"]
    if fixture_class not in ALLOWED_FIXTURE_CLASSES:
        raise CompatibilityMatrixError(f"{path} has unsupported fixture_class {fixture_class!r}")
    if status not in ALLOWED_STATUSES:
        raise CompatibilityMatrixError(f"{path} has unsupported status {status!r}")
    if payload["source_scope"] != "committed_offline_fixture_only":
        raise CompatibilityMatrixError(f"{path} must declare committed_offline_fixture_only source_scope")
    return CompatibilityFixture(
        fixture_id=str(payload["fixture_id"]),
        fixture_class=fixture_class,
        status=status,
        source_scope=payload["source_scope"],
        agent_queries=_as_string_tuple(payload["agent_queries"], "agent_queries"),
        blocked_action_classes=_as_string_tuple(payload["blocked_action_classes"], "blocked_action_classes"),
        stale_evidence_behavior=_as_string_tuple(payload["stale_evidence_behavior"], "stale_evidence_behavior"),
        missing_information_prompts=_as_string_tuple(payload["missing_information_prompts"], "missing_information_prompts"),
        reversible_draft_boundaries=_as_string_tuple(payload["reversible_draft_boundaries"], "reversible_draft_boundaries"),
        local_pdf_preview_boundaries=_as_string_tuple(payload["local_pdf_preview_boundaries"], "local_pdf_preview_boundaries"),
        exact_confirmation_checkpoints=_as_string_tuple(payload["exact_confirmation_checkpoints"], "exact_confirmation_checkpoints"),
        manual_handoff_surfaces=_as_string_tuple(payload["manual_handoff_surfaces"], "manual_handoff_surfaces"),
        offline_validation_commands=_as_command_tuple(payload["offline_validation_commands"], "offline_validation_commands"),
    )


def _sorted_unique(items: Iterable[str]) -> list[str]:
    return sorted(set(items))


def _sorted_unique_commands(items: Iterable[tuple[str, ...]]) -> list[list[str]]:
    return [list(command) for command in sorted(set(items))]


def _require_non_empty_list(matrix: Mapping[str, Any], key: str, message: str) -> None:
    value = matrix.get(key)
    if not isinstance(value, list) or not value:
        raise CompatibilityMatrixError(message)


def _validate_command_rows(value: Any, key: str) -> None:
    commands = _as_command_tuple(value, key)
    forbidden_parts = {"curl", "wget", "playwright", "npx", "node"}
    for command in commands:
        lowered = {part.lower() for part in command}
        if lowered.intersection(forbidden_parts):
            raise CompatibilityMatrixError(f"{key} must contain offline Python validation commands only")


def validate_matrix(matrix: Mapping[str, Any]) -> None:
    """Validate an already assembled compatibility matrix v6 packet."""

    if matrix.get("matrix_id") != "ppd_agent_api_compatibility_matrix_v6":
        raise CompatibilityMatrixError("matrix_id must be ppd_agent_api_compatibility_matrix_v6")
    if matrix.get("version") != 6:
        raise CompatibilityMatrixError("version must be 6")
    if matrix.get("source_policy") != "fixture_first_committed_inactive_replay_only":
        raise CompatibilityMatrixError("source_policy must remain fixture-first and inactive")
    _raise_forbidden(matrix)
    for key, message in REQUIRED_MATRIX_LISTS.items():
        _require_non_empty_list(matrix, key, message)
    _validate_command_rows(matrix["offline_validation_commands"], "offline_validation_commands")
    _validate_command_rows(matrix["validation_commands"], "validation_commands")
    smoke_refs = set(str(item) for item in matrix["smoke_replay_fixture_refs"])
    rollback_refs = set(str(item) for item in matrix["rollback_drill_fixture_refs"])
    fixture_ids = set(str(item) for item in matrix.get("fixture_ids", []))
    if not smoke_refs.issubset(fixture_ids) or not rollback_refs.issubset(fixture_ids):
        raise CompatibilityMatrixError("smoke replay and rollback drill references must be present in fixture_ids")


def build_matrix(fixture_paths: Iterable[Path]) -> dict[str, Any]:
    fixtures = [load_fixture(path) for path in fixture_paths]
    fixture_classes = {fixture.fixture_class for fixture in fixtures}
    missing_classes = ALLOWED_FIXTURE_CLASSES.difference(fixture_classes)
    if missing_classes:
        raise CompatibilityMatrixError(
            "matrix requires inactive smoke replay and rollback drill fixtures; missing "
            + ", ".join(sorted(missing_classes))
        )
    smoke_refs = _sorted_unique(fixture.fixture_id for fixture in fixtures if fixture.fixture_class == "inactive_smoke_replay")
    rollback_refs = _sorted_unique(fixture.fixture_id for fixture in fixtures if fixture.fixture_class == "inactive_rollback_drill")
    validation_commands = _sorted_unique_commands(command for fixture in fixtures for command in fixture.offline_validation_commands)
    matrix = {
        "matrix_id": "ppd_agent_api_compatibility_matrix_v6",
        "version": 6,
        "source_policy": "fixture_first_committed_inactive_replay_only",
        "fixture_ids": _sorted_unique(fixture.fixture_id for fixture in fixtures),
        "smoke_replay_fixture_refs": smoke_refs,
        "rollback_drill_fixture_refs": rollback_refs,
        "supported_agent_queries": _sorted_unique(query for fixture in fixtures for query in fixture.agent_queries),
        "blocked_action_classes": _sorted_unique(action for fixture in fixtures for action in fixture.blocked_action_classes),
        "stale_evidence_behavior": _sorted_unique(item for fixture in fixtures for item in fixture.stale_evidence_behavior),
        "missing_information_prompts": _sorted_unique(item for fixture in fixtures for item in fixture.missing_information_prompts),
        "reversible_draft_boundaries": _sorted_unique(item for fixture in fixtures for item in fixture.reversible_draft_boundaries),
        "local_pdf_preview_boundaries": _sorted_unique(item for fixture in fixtures for item in fixture.local_pdf_preview_boundaries),
        "exact_confirmation_checkpoints": _sorted_unique(item for fixture in fixtures for item in fixture.exact_confirmation_checkpoints),
        "manual_handoff_surfaces": _sorted_unique(item for fixture in fixtures for item in fixture.manual_handoff_surfaces),
        "offline_validation_commands": validation_commands,
        "validation_commands": validation_commands,
        "prohibited_runtime_behaviors": sorted(
            [
                "activate_guardrails",
                "crawl_live_sites",
                "make_legal_or_permitting_guarantees",
                "open_devhub",
                "pay_or_schedule",
                "read_private_documents",
                "submit_certify_or_upload",
            ]
        ),
    }
    validate_matrix(matrix)
    return matrix


def default_fixture_paths() -> list[Path]:
    fixture_dir = Path(__file__).parent / "tests" / "fixtures" / "agent_api_compatibility_matrix_v6"
    return [
        fixture_dir / "inactive_smoke_replay.json",
        fixture_dir / "inactive_rollback_drill.json",
    ]


def default_matrix() -> dict[str, Any]:
    return build_matrix(default_fixture_paths())


if __name__ == "__main__":
    print(json.dumps(default_matrix(), indent=2, sort_keys=True))
