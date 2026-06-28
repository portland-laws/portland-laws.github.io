"""Fixture validation for PP&D daemon circuit-breaker pause states.

The validator is intentionally side-effect-free. It proves that a paused daemon
status record carries enough information for quarantine, supervised restart
eligibility, and source-safe recovery before autonomous work can resume.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


_FORBIDDEN_ARTIFACT_PREFIXES = (
    "src/lib/logic/",
    "public/corpus/portland-or/current/",
    "ipfs_datasets_py/.daemon/",
    "ppd/data/private/",
    "ppd/data/raw/",
    "ppd/devhub/sessions/",
    "ppd/devhub/traces/",
)

_REQUIRED_FORBIDDEN_BOUNDARIES = frozenset(
    {
        "src/lib/logic/",
        "public/corpus/portland-or/current/",
        "ipfs_datasets_py/.daemon/",
    }
)

_SAFE_RECOVERY_STEPS = frozenset(
    {
        "operator_review",
        "fixture_validation",
        "source_evidence_refresh",
    }
)


@dataclass(frozen=True)
class CircuitBreakerStatusValidation:
    """Result of validating a paused circuit-breaker status fixture."""

    task_id: str
    quarantine_id: str
    restart_mode: str
    source_evidence_ids: tuple[str, ...]


def load_status_fixture(path: Path) -> Mapping[str, Any]:
    """Load a deterministic circuit-breaker status fixture."""

    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, Mapping):
        raise ValueError("status fixture must be a JSON object")
    return loaded


def validate_paused_circuit_breaker_status(
    status: Mapping[str, Any],
) -> CircuitBreakerStatusValidation:
    """Validate the paused-daemon circuit-breaker recovery contract.

    The record is valid only when autonomous work remains paused, the selected
    task is quarantined, restart eligibility is constrained to supervised
    fixture validation, and recovery boundaries rule out private or live-source
    side effects.
    """

    if _required_text(status, "daemon_state") != "paused":
        raise ValueError("daemon_state must be paused")
    if _required_bool(status, "autonomous_work_allowed") is not False:
        raise ValueError("autonomous work must remain disallowed while paused")

    circuit_breaker = _required_mapping(status, "circuit_breaker")
    if _required_text(circuit_breaker, "status") != "open":
        raise ValueError("circuit breaker must be open")
    _required_text(circuit_breaker, "opened_at")
    _required_text(circuit_breaker, "reason")

    quarantine = _required_mapping(status, "quarantine")
    if _required_bool(quarantine, "enabled") is not True:
        raise ValueError("quarantine must be enabled")
    task_id = _required_text(quarantine, "task_id")
    quarantine_id = _required_text(quarantine, "quarantine_id")
    _required_text(quarantine, "failure_kind")
    _required_text(quarantine, "quarantined_at")

    restart = _required_mapping(status, "restart_eligibility")
    if _required_bool(restart, "eligible") is not True:
        raise ValueError("fixture must record supervised restart eligibility")
    restart_mode = _required_text(restart, "mode")
    if restart_mode != "supervised_fixture_only_restart":
        raise ValueError("restart mode must be supervised fixture-only restart")
    if _required_bool(restart, "requires_operator_review") is not True:
        raise ValueError("restart eligibility must require operator review")
    if _required_bool(restart, "requires_self_test") is not True:
        raise ValueError("restart eligibility must require self-test validation")
    if _required_bool(restart, "may_resume_autonomous_work") is not False:
        raise ValueError("restart eligibility must not resume autonomous work")

    recovery = _required_mapping(status, "source_safe_recovery")
    if _required_bool(recovery, "no_live_network") is not True:
        raise ValueError("source-safe recovery must disable live network")
    if _required_bool(recovery, "no_authenticated_devhub") is not True:
        raise ValueError("source-safe recovery must disable authenticated DevHub")
    if _required_bool(recovery, "no_raw_document_persistence") is not True:
        raise ValueError("source-safe recovery must forbid raw document persistence")
    if _required_bool(recovery, "no_private_artifacts") is not True:
        raise ValueError("source-safe recovery must forbid private artifacts")

    steps = set(_required_text_sequence(recovery, "required_steps_before_resume"))
    missing_steps = _SAFE_RECOVERY_STEPS.difference(steps)
    if missing_steps:
        raise ValueError("missing recovery steps: " + ", ".join(sorted(missing_steps)))

    forbidden_boundaries = set(_required_text_sequence(recovery, "forbidden_write_prefixes"))
    missing_boundaries = _REQUIRED_FORBIDDEN_BOUNDARIES.difference(forbidden_boundaries)
    if missing_boundaries:
        raise ValueError(
            "missing forbidden write boundaries: " + ", ".join(sorted(missing_boundaries))
        )

    source_evidence_ids = tuple(_required_text_sequence(status, "source_evidence_ids"))
    if not source_evidence_ids:
        raise ValueError("at least one source evidence id is required")

    for artifact_path in _required_text_sequence(status, "recorded_artifact_paths"):
        _assert_commit_safe_artifact_path(artifact_path)

    return CircuitBreakerStatusValidation(
        task_id=task_id,
        quarantine_id=quarantine_id,
        restart_mode=restart_mode,
        source_evidence_ids=source_evidence_ids,
    )


def _required_mapping(record: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = record.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(key + " must be an object")
    return value


def _required_text(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key + " must be a non-empty string")
    return value


def _required_bool(record: Mapping[str, Any], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        raise ValueError(key + " must be a boolean")
    return value


def _required_text_sequence(record: Mapping[str, Any], key: str) -> Sequence[str]:
    value = record.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(key + " must be a list of strings")
    return value


def _assert_commit_safe_artifact_path(path: str) -> None:
    if path.startswith("/") or ".." in Path(path).parts:
        raise ValueError("artifact paths must be relative and local to the repository")
    for forbidden_prefix in _FORBIDDEN_ARTIFACT_PREFIXES:
        if path.startswith(forbidden_prefix):
            raise ValueError("artifact path crosses forbidden boundary: " + path)
