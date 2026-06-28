"""Fixture-first public refresh authorization packet v7.

This module consumes only committed public source freshness watchlist v6
fixtures. It assembles human reviewer go/no-go rows, source freshness
preconditions, crawl-scope allowlist reminders, raw-artifact prohibition notes,
citation repair hold carry-forward rows, rollback readiness references, and
exact offline validation commands. It does not crawl, download raw artifacts,
open DevHub, read private documents, upload, submit, certify, pay, schedule, or
make legal or permitting guarantees.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.public_source_freshness_watchlist_v6 import (
    build_watchlist_from_files,
    validate_watchlist,
)

PACKET_TYPE = "ppd.public_refresh_authorization_packet.v7"
PACKET_VERSION = "v7"
MODE = "fixture_first_public_refresh_authorization_packet_v7"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_authorization_packet_v7.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_refresh_authorization_packet_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_authorization_packet_v7.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "public_source_freshness_watchlist_v6_fixtures_only": True,
    "authorization_packet_only": True,
    "live_crawl_executed": False,
    "documents_downloaded": False,
    "raw_bodies_persisted": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "payments_performed": False,
    "scheduling_performed": False,
    "legal_or_permitting_guarantees_made": False,
    "active_mutation": False,
}

FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "live_crawl_executed",
        "documents_downloaded",
        "raw_bodies_persisted",
        "devhub_opened",
        "private_documents_read",
        "uploads_performed",
        "submissions_performed",
        "certifications_performed",
        "payments_performed",
        "scheduling_performed",
        "legal_or_permitting_guarantees_made",
        "active_mutation",
        "crawl_started",
        "downloaded",
        "submitted",
        "uploaded",
        "certified",
        "paid",
        "scheduled",
    }
)
PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|download|har|password|payment|private|raw|screenshot|secret|session|storage_state|token|trace)(_|$)",
    re.IGNORECASE,
)
ALLOWED_SAFETY_NOTE_KEYS = {
    "raw_artifact_prohibition_notes",
    "raw_artifact_prohibition_note",
    "raw_artifact_ref_allowed",
    "no_raw_body_persisted_required",
    "no_raw_body_policy",
}


@dataclass(frozen=True)
class PublicRefreshAuthorizationPacketV7Result:
    valid: bool
    problems: tuple[str, ...]


class PublicRefreshAuthorizationPacketV7Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid public refresh authorization packet v7: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("public refresh authorization fixture must be a JSON object")
    return payload


def build_public_refresh_authorization_packet_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = load_json(fixture_path)
    watchlist = build_watchlist_from_files(
        _resolve(fixture_path, _text(fixture.get("public_source_registry_fixture"))),
        _resolve(fixture_path, _text(fixture.get("prior_refresh_fixture"))),
    )
    return build_public_refresh_authorization_packet_v7(
        watchlist,
        source_fixture_refs=_source_refs_from_fixture(fixture),
    )


def build_public_refresh_authorization_packet_v7(
    freshness_watchlist: Mapping[str, Any],
    *,
    source_fixture_refs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_watchlist(freshness_watchlist)
    watch_rows = _mapping_sequence(freshness_watchlist.get("watchlist_rows"))
    refs = list(source_fixture_refs or []) or [
        {"fixture_role": "public_source_freshness_watchlist_v6", "path": "fixture://public_source_freshness_watchlist_v6"},
    ]
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "public-refresh-authorization-v7-fixture",
        "mode": MODE,
        "consumes_only": {"public_source_freshness_watchlist_v6_fixtures": True},
        "source_fixture_refs": refs,
        "boundaries": copy.deepcopy(REQUIRED_BOUNDARIES),
        "human_reviewer_go_no_go_rows": [_reviewer_go_no_go_row(row) for row in watch_rows],
        "source_freshness_preconditions": [_freshness_precondition(row) for row in watch_rows],
        "crawl_scope_allowlist_reminders": [_allowlist_reminder(row) for row in watch_rows],
        "raw_artifact_prohibition_notes": _raw_artifact_notes(freshness_watchlist),
        "citation_repair_hold_carry_forward_rows": [_citation_hold_row(row) for row in watch_rows],
        "rollback_readiness_references": [_rollback_reference(row) for row in watch_rows],
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_public_refresh_authorization_packet_v7(packet)
    return packet


def assert_valid_public_refresh_authorization_packet_v7(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_authorization_packet_v7(packet)
    if not result.valid:
        raise PublicRefreshAuthorizationPacketV7Error(result.problems)


def validate_public_refresh_authorization_packet_v7(packet: Mapping[str, Any]) -> PublicRefreshAuthorizationPacketV7Result:
    if not isinstance(packet, Mapping):
        return PublicRefreshAuthorizationPacketV7Result(False, ("packet must be an object",))
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v7")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != {"public_source_freshness_watchlist_v6_fixtures": True}:
        problems.append("consumes_only must allow only public source freshness watchlist v6 fixtures")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        problems.append("boundaries must deny live crawling, downloads, raw body persistence, DevHub, private documents, official actions, guarantees, and mutation")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must exactly match public refresh authorization v7 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")
    for key in (
        "source_fixture_refs",
        "human_reviewer_go_no_go_rows",
        "source_freshness_preconditions",
        "crawl_scope_allowlist_reminders",
        "raw_artifact_prohibition_notes",
        "citation_repair_hold_carry_forward_rows",
        "rollback_readiness_references",
    ):
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")
    _validate_refs(packet.get("source_fixture_refs"), problems)
    _validate_review_rows(packet.get("human_reviewer_go_no_go_rows"), problems)
    _validate_preconditions(packet.get("source_freshness_preconditions"), problems)
    _validate_allowlist(packet.get("crawl_scope_allowlist_reminders"), problems)
    _validate_citation_holds(packet.get("citation_repair_hold_carry_forward_rows"), problems)
    _validate_rollback_refs(packet.get("rollback_readiness_references"), problems)
    _scan_for_forbidden_payload(packet, "packet", problems)
    return PublicRefreshAuthorizationPacketV7Result(not problems, tuple(dict.fromkeys(problems)))


def _reviewer_go_no_go_row(row: Mapping[str, Any]) -> dict[str, Any]:
    escalation = _mapping(row.get("reviewer_escalation"))
    hold = _mapping(row.get("stale_source_hold_trigger"))
    return {
        "row_id": f"review-go-no-go::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "reviewer_owner": _text(escalation.get("reviewer_owner")),
        "default_decision": "no_go_hold",
        "go_allowed": False,
        "no_go_reasons": list(hold.get("reasons", [])),
        "required_manual_disposition": ["confirm_fixture", "keep_hold", "approve_future_public_refresh_preflight"],
        "human_reviewer_required": True,
    }


def _freshness_precondition(row: Mapping[str, Any]) -> dict[str, Any]:
    threshold = _mapping(row.get("freshness_threshold"))
    return {
        "precondition_id": f"freshness-precondition::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "canonical_url": _text(row.get("canonical_url")),
        "as_of_date": _text(threshold.get("as_of_date")),
        "last_seen_at": _text(threshold.get("last_seen_at")),
        "crawl_frequency": _text(threshold.get("crawl_frequency")),
        "threshold_days": threshold.get("threshold_days"),
        "days_since_last_seen": threshold.get("days_since_last_seen"),
        "is_stale_by_age": threshold.get("is_stale_by_age"),
        "must_resolve_before_currentness_claim": True,
        "live_crawl_authorized": False,
    }


def _allowlist_reminder(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "allowlist_reminder_id": f"crawl-scope::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "canonical_url": _text(row.get("canonical_url")),
        "priority_source_group": _text(row.get("priority_source_group")),
        "allowed_scope": "official_public_sources_only_after_separate_preflight",
        "robots_check_required": True,
        "policy_check_required": True,
        "devhub_authenticated_scope_allowed": False,
        "private_or_raw_artifact_scope_allowed": False,
    }


def _raw_artifact_notes(watchlist: Mapping[str, Any]) -> list[dict[str, Any]]:
    reminders = watchlist.get("no_raw_body_capture_policy_reminders")
    if not isinstance(reminders, list):
        reminders = []
    return [
        {
            "note_id": f"raw-artifact-prohibition::{index}",
            "prohibition": str(reminder),
            "raw_artifact_ref_allowed": False,
            "no_raw_body_persisted_required": True,
        }
        for index, reminder in enumerate(reminders, start=1)
        if isinstance(reminder, str) and reminder
    ]


def _citation_hold_row(row: Mapping[str, Any]) -> dict[str, Any]:
    hold = _mapping(row.get("stale_source_hold_trigger"))
    return {
        "hold_id": f"citation-repair-hold::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "affected_requirement_ids": list(row.get("affected_requirement_ids", [])),
        "affected_guardrail_bundle_ids": list(row.get("affected_guardrail_bundle_ids", [])),
        "carry_forward_required": bool(hold.get("triggered")),
        "agent_currentness_claims_blocked": True,
        "consequential_action_claims_blocked": True,
    }


def _rollback_reference(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "rollback_reference_id": f"rollback-readiness::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "source_registry_reference": _text(row.get("source_registry_reference")),
        "prior_refresh_fixture_reference": _text(row.get("prior_refresh_fixture_reference")),
        "rollback_ready_before_future_refresh": True,
        "restore_previous_guardrail_bundle_refs": list(row.get("affected_guardrail_bundle_ids", [])),
    }


def _validate_refs(value: Any, problems: list[str]) -> None:
    roles = {_text(row.get("fixture_role")) for row in _mapping_sequence(value)}
    if roles != {"public_source_freshness_watchlist_v6"}:
        problems.append("source_fixture_refs must include only public_source_freshness_watchlist_v6 roles")


def _validate_review_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"human_reviewer_go_no_go_rows[{index}]"
        if row.get("default_decision") != "no_go_hold" or row.get("go_allowed") is not False:
            problems.append(f"{prefix} must default to no_go_hold with go_allowed false")
        if row.get("human_reviewer_required") is not True:
            problems.append(f"{prefix}.human_reviewer_required must be true")
        if not _non_empty_sequence(row.get("required_manual_disposition")):
            problems.append(f"{prefix}.required_manual_disposition must be non-empty")


def _validate_preconditions(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"source_freshness_preconditions[{index}]"
        if row.get("must_resolve_before_currentness_claim") is not True:
            problems.append(f"{prefix}.must_resolve_before_currentness_claim must be true")
        if row.get("live_crawl_authorized") is not False:
            problems.append(f"{prefix}.live_crawl_authorized must be false")


def _validate_allowlist(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"crawl_scope_allowlist_reminders[{index}]"
        if row.get("allowed_scope") != "official_public_sources_only_after_separate_preflight":
            problems.append(f"{prefix}.allowed_scope must remain official public sources only")
        for key in ("robots_check_required", "policy_check_required"):
            if row.get(key) is not True:
                problems.append(f"{prefix}.{key} must be true")
        if row.get("devhub_authenticated_scope_allowed") is not False or row.get("private_or_raw_artifact_scope_allowed") is not False:
            problems.append(f"{prefix} must exclude DevHub authenticated, private, and raw artifact scope")


def _validate_citation_holds(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"citation_repair_hold_carry_forward_rows[{index}]"
        if row.get("agent_currentness_claims_blocked") is not True:
            problems.append(f"{prefix}.agent_currentness_claims_blocked must be true")
        if row.get("consequential_action_claims_blocked") is not True:
            problems.append(f"{prefix}.consequential_action_claims_blocked must be true")
        if not isinstance(row.get("affected_requirement_ids"), list):
            problems.append(f"{prefix}.affected_requirement_ids must be a list")


def _validate_rollback_refs(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"rollback_readiness_references[{index}]"
        if row.get("rollback_ready_before_future_refresh") is not True:
            problems.append(f"{prefix}.rollback_ready_before_future_refresh must be true")
        if not _text(row.get("source_registry_reference")) or not _text(row.get("prior_refresh_fixture_reference")):
            problems.append(f"{prefix} must reference source registry and prior refresh fixtures")


def _source_refs_from_fixture(fixture: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"fixture_role": "public_source_freshness_watchlist_v6", "path": _text(fixture.get("public_source_registry_fixture"))},
        {"fixture_role": "public_source_freshness_watchlist_v6", "path": _text(fixture.get("prior_refresh_fixture"))},
    ]


def _resolve(base: Path, value: str) -> Path:
    if not value:
        raise ValueError("fixture path is required")
    path = Path(value)
    if path.exists():
        return path
    return (base.parent / path).resolve()


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized in FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f"{child_path} must not be true")
            if normalized not in ALLOWED_SAFETY_NOTE_KEYS and PRIVATE_KEY_RE.search(normalized) and _truthy(child):
                problems.append(f"{child_path} must not contain private, auth, browser, trace, raw, payment, session, or downloaded artifacts")
            _scan_for_forbidden_payload(child, child_path, problems)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", problems)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
