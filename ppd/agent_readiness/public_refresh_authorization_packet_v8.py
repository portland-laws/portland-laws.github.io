"""Fixture-first public refresh authorization packet v8.

Consumes only committed v7 public freshness handoff fixtures, agent API
compatibility matrix v7 fixtures, and current source registry fixtures. The
packet is reviewer authorization evidence only: it does not crawl, download raw
artifacts, open DevHub, read private documents, upload, submit, certify, pay,
schedule, or make legal/permitting guarantees.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from ppd.public_freshness_watchlist_handoff_v7 import build_public_freshness_watchlist_handoff_v7

PACKET_TYPE = "ppd.public_refresh_authorization_packet.v8"
PACKET_VERSION = "v8"
MODE = "fixture_first_public_refresh_authorization_packet_v8"

DEFAULT_FIXTURE = Path(__file__).parents[1] / "tests" / "fixtures" / "public_refresh_authorization_packet_v8" / "source_fixture.json"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_authorization_packet_v8.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_refresh_authorization_packet_v8.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_authorization_packet_v8.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

CONSUMES_ONLY = {
    "public_freshness_watchlist_handoff_v7_fixtures": True,
    "agent_api_compatibility_matrix_v7_fixtures": True,
    "current_source_registry_fixtures": True,
}

REQUIRED_SOURCE_FIXTURE_ROLES = frozenset(
    {
        "public_freshness_watchlist_handoff_v7",
        "agent_api_compatibility_matrix_v7",
        "current_source_registry",
    }
)

BOUNDARIES = {
    "fixture_first": True,
    "authorization_packet_only": True,
    "live_crawl_executed": False,
    "raw_artifacts_downloaded": False,
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

PROHIBITED_ACTIONS = [
    "live_crawl",
    "raw_artifact_download",
    "raw_body_persistence",
    "devhub_open",
    "private_document_read",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantee",
]

FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "active_mutation",
        "approved",
        "authorized_live_crawl",
        "certification_complete",
        "certifications_performed",
        "certified",
        "completed",
        "completion_claimed",
        "crawl_executed",
        "crawl_started",
        "documents_downloaded",
        "downloaded",
        "executed",
        "guaranteed",
        "legal_or_permitting_guarantees_made",
        "live_crawl_executed",
        "mutation_active",
        "official_action_complete",
        "official_action_completed",
        "paid",
        "payments_performed",
        "raw_artifacts_downloaded",
        "raw_bodies_persisted",
        "scheduled",
        "scheduling_performed",
        "submitted",
        "submissions_performed",
        "uploaded",
        "uploads_performed",
    }
)

FORBIDDEN_ARTIFACT_KEY_RE = re.compile(
    r"(^|_)(auth|browser_state|cookie|credential|download|downloaded|har|password|payment|private|raw|session|storage_state|token|trace)(_|$)",
    re.IGNORECASE,
)
ALLOWED_SAFETY_KEYS = frozenset(
    {
        "forbidden_persistence",
        "legal_or_permitting_guarantees_made",
        "must_hold_legal_or_permitting_guarantees",
        "no_raw_body_persisted_required",
        "no_raw_body_persistence_requirements",
        "permitted_persistence",
        "private_documents_read",
        "raw_artifacts_downloaded",
        "raw_bodies_persisted",
        "required_reviewer_checks",
    }
)


@dataclass(frozen=True)
class PublicRefreshAuthorizationPacketV8Result:
    valid: bool
    problems: tuple[str, ...]


class PublicRefreshAuthorizationPacketV8Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid public refresh authorization packet v8: " + "; ".join(self.problems))


def build_public_refresh_authorization_packet_v8_from_fixture(path: str | Path = DEFAULT_FIXTURE) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = _read_object(fixture_path)
    handoff_dir = _resolve(fixture_path, _text(fixture.get("public_freshness_watchlist_handoff_v7_fixture_dir")))
    matrix_path = _resolve(fixture_path, _text(fixture.get("agent_api_compatibility_matrix_v7_fixture")))
    registry_path = _resolve(fixture_path, _text(fixture.get("current_source_registry_fixture")))
    return build_public_refresh_authorization_packet_v8(
        build_public_freshness_watchlist_handoff_v7(handoff_dir),
        _read_object(matrix_path),
        _read_object(registry_path),
        source_fixture_refs=[
            {"fixture_role": "public_freshness_watchlist_handoff_v7", "path": str(handoff_dir)},
            {"fixture_role": "agent_api_compatibility_matrix_v7", "path": str(matrix_path)},
            {"fixture_role": "current_source_registry", "path": str(registry_path)},
        ],
    )


def build_public_refresh_authorization_packet_v8(
    handoff: Mapping[str, Any],
    matrix: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    source_fixture_refs: list[Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    _validate_inputs(handoff, matrix, registry)
    handoff_rows = _index_by_source(handoff["next_refresh_watch_rows"])
    risk_notes = _index_by_source(handoff["stale_source_risk_notes"])
    matrix_rows = _index_by_source(matrix["sources"])
    registry_rows = _index_by_source(registry["sources"])

    reviewer_rows = []
    allowlist_rows = []
    no_raw_body_rows = []
    hold_rows = []
    rollback_rows = []

    for source in registry["sources"]:
        source_id = _text(source.get("source_id"))
        handoff_row = handoff_rows[source_id]
        matrix_row = matrix_rows[source_id]
        risk_note = risk_notes[source_id]
        registry_row = registry_rows[source_id]
        public_url = _text(source.get("public_url"))
        rollback_reference = _text(handoff_row.get("rollback_reference"))

        reviewer_rows.append(
            {
                "row_id": f"reviewer-authorization::{source_id}",
                "source_id": source_id,
                "label": _text(source.get("label")),
                "public_url": public_url,
                "watchlist_reference": f"public_freshness_watchlist_handoff_v7::{source_id}",
                "compatibility_reference": f"agent_api_compatibility_matrix_v7::{source_id}",
                "source_registry_reference": f"current_source_registry_v7::{source_id}",
                "authorization_decision": "hold_pending_reviewer_authorization",
                "go_allowed": False,
                "reviewer_required": True,
                "agent_api_compatibility": bool(matrix_row.get("agent_api_compatible")),
                "required_reviewer_checks": [
                    "confirm official public-source scope from committed fixtures",
                    "confirm allowlist entry before any future public fetch",
                    "confirm robots preflight before any future public fetch",
                    "confirm no raw body persistence before any future processor handoff",
                    "confirm stale-source hold disposition before any currentness claim",
                    "confirm rollback reference remains visible before authorization",
                ],
                "prohibited_actions": list(PROHIBITED_ACTIONS),
                "rollback_reference": rollback_reference,
            }
        )
        allowlist_rows.append(
            {
                "requirement_id": f"allowlist-robots-preflight::{source_id}",
                "source_id": source_id,
                "public_url": public_url,
                "allowlist_required": True,
                "robots_preflight_required": True,
                "live_fetch_authorized_by_this_packet": False,
                "required_before": "any_future_public_refresh_fetch_or_processor_handoff",
            }
        )
        no_raw_body_rows.append(
            {
                "requirement_id": f"no-raw-body::{source_id}",
                "source_id": source_id,
                "no_raw_body_persisted_required": True,
                "permitted_persistence": ["metadata", "normalized_public_text_reference", "checksum", "citation_reference"],
                "forbidden_persistence": ["raw_html", "raw_pdf_bytes", "downloaded_document", "screenshot", "har", "trace", "browser_state"],
            }
        )
        hold_rows.append(
            {
                "hold_id": f"source-freshness-hold::{source_id}",
                "source_id": source_id,
                "hold_condition": _text(risk_note.get("stale_source_risk_note")),
                "must_hold_currentness_claims": True,
                "must_hold_legal_or_permitting_guarantees": True,
                "cleared_by_this_packet": False,
            }
        )
        rollback_rows.append(
            {
                "rollback_id": f"rollback-reference::{source_id}",
                "source_id": source_id,
                "rollback_reference": rollback_reference,
                "rollback_visibility_required_before_authorization": True,
                "active_registry_mutation": False,
            }
        )
        if not registry_row:
            raise ValueError(f"registry fixture missing source row for {source_id}")

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "public-refresh-authorization-v8-fixture",
        "mode": MODE,
        "consumes_only": copy.deepcopy(CONSUMES_ONLY),
        "source_fixture_refs": [dict(item) for item in (source_fixture_refs or [])],
        "authorized_source_ids": sorted(registry_rows),
        "boundaries": copy.deepcopy(BOUNDARIES),
        "reviewer_authorization_rows": reviewer_rows,
        "allowlist_and_robots_preflight_requirements": allowlist_rows,
        "no_raw_body_persistence_requirements": no_raw_body_rows,
        "source_freshness_hold_conditions": hold_rows,
        "rollback_references": rollback_rows,
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_public_refresh_authorization_packet_v8(packet)
    return packet


def validate_public_refresh_authorization_packet_v8(packet: Mapping[str, Any]) -> PublicRefreshAuthorizationPacketV8Result:
    if not isinstance(packet, Mapping):
        return PublicRefreshAuthorizationPacketV8Result(False, ("packet must be an object",))
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v8")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != CONSUMES_ONLY:
        problems.append("consumes_only must name only the v8 allowed fixture families")
    if packet.get("boundaries") != BOUNDARIES:
        problems.append("boundaries must deny live crawl, raw artifacts, DevHub, private documents, official actions, guarantees, and mutation")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must exactly match the v8 offline command set")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")
    for key in (
        "source_fixture_refs",
        "authorized_source_ids",
        "reviewer_authorization_rows",
        "allowlist_and_robots_preflight_requirements",
        "no_raw_body_persistence_requirements",
        "source_freshness_hold_conditions",
        "rollback_references",
    ):
        if not _non_empty_list(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")
    _validate_source_fixture_refs(packet.get("source_fixture_refs"), problems)
    _validate_authorized_source_ids(packet.get("authorized_source_ids"), problems)
    _validate_row_alignment(packet, problems)
    _scan_for_forbidden_payload(packet, "packet", problems)
    return PublicRefreshAuthorizationPacketV8Result(not problems, tuple(dict.fromkeys(problems)))


def assert_valid_public_refresh_authorization_packet_v8(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_authorization_packet_v8(packet)
    if not result.valid:
        raise PublicRefreshAuthorizationPacketV8Error(result.problems)


def _validate_inputs(handoff: Mapping[str, Any], matrix: Mapping[str, Any], registry: Mapping[str, Any]) -> None:
    if handoff.get("handoff_id") != "public_freshness_watchlist_handoff_v7":
        raise ValueError("handoff must be public_freshness_watchlist_handoff_v7")
    if handoff.get("mode") != "fixture_first_offline_only":
        raise ValueError("handoff must be fixture_first_offline_only")
    if matrix.get("fixture_id") != "agent_api_compatibility_matrix_v7":
        raise ValueError("matrix fixture must be agent_api_compatibility_matrix_v7")
    if registry.get("fixture_id") != "current_source_registry_v7":
        raise ValueError("registry fixture must be current_source_registry_v7")
    handoff_ids = set(_index_by_source(handoff.get("next_refresh_watch_rows", [])).keys())
    matrix_ids = set(_index_by_source(matrix.get("sources", [])).keys())
    registry_ids = set(_index_by_source(registry.get("sources", [])).keys())
    if handoff_ids != matrix_ids or handoff_ids != registry_ids:
        raise ValueError("handoff, matrix, and registry fixtures must cover the same source_ids")


def _validate_source_fixture_refs(value: Any, problems: list[str]) -> None:
    if not isinstance(value, list):
        return
    roles: set[str] = set()
    for ref in value:
        if not isinstance(ref, Mapping):
            problems.append("source_fixture_refs must contain only objects")
            continue
        role = _text(ref.get("fixture_role"))
        path = _text(ref.get("path"))
        if not role or not path:
            problems.append("source_fixture_refs must include fixture_role and path")
        roles.add(role)
    missing = REQUIRED_SOURCE_FIXTURE_ROLES - roles
    for role in sorted(missing):
        problems.append(f"source_fixture_refs must include {role}")


def _validate_authorized_source_ids(value: Any, problems: list[str]) -> None:
    if not isinstance(value, list) or not value:
        return
    if any(not isinstance(item, str) or not item for item in value):
        problems.append("authorized_source_ids must contain non-empty strings")
    if len(set(value)) != len(value):
        problems.append("authorized_source_ids must not contain duplicate source_ids")


def _validate_row_alignment(packet: Mapping[str, Any], problems: list[str]) -> None:
    expected_ids = set(packet.get("authorized_source_ids", [])) if isinstance(packet.get("authorized_source_ids"), list) else set()
    reviewer_ids = set(_safe_index_by_source(packet.get("reviewer_authorization_rows", []), problems, "reviewer_authorization_rows").keys())
    if expected_ids and reviewer_ids != expected_ids:
        problems.append("reviewer_authorization_rows must cover every authorized_source_id")
    for key in (
        "allowlist_and_robots_preflight_requirements",
        "no_raw_body_persistence_requirements",
        "source_freshness_hold_conditions",
        "rollback_references",
    ):
        row_ids = set(_safe_index_by_source(packet.get(key, []), problems, key).keys())
        if row_ids != reviewer_ids:
            problems.append(f"{key} must align to reviewer_authorization_rows by source_id")
        if expected_ids and row_ids != expected_ids:
            problems.append(f"{key} must cover every authorized_source_id")
    for row in packet.get("reviewer_authorization_rows", []):
        if not isinstance(row, Mapping):
            continue
        source_id = _text(row.get("source_id"))
        if row.get("go_allowed") is not False:
            problems.append("reviewer authorization rows must keep go_allowed false")
        if row.get("authorization_decision") != "hold_pending_reviewer_authorization":
            problems.append("reviewer authorization rows must hold pending reviewer authorization")
        if row.get("reviewer_required") is not True:
            problems.append("reviewer authorization rows must require reviewer authorization")
        if row.get("watchlist_reference") != f"public_freshness_watchlist_handoff_v7::{source_id}":
            problems.append("reviewer authorization rows must include watchlist references")
        if row.get("compatibility_reference") != f"agent_api_compatibility_matrix_v7::{source_id}":
            problems.append("reviewer authorization rows must include compatibility references")
        if row.get("source_registry_reference") != f"current_source_registry_v7::{source_id}":
            problems.append("reviewer authorization rows must include source registry references")
        if not _text(row.get("rollback_reference")):
            problems.append("reviewer authorization rows must include rollback references")
    for row in packet.get("allowlist_and_robots_preflight_requirements", []):
        if not isinstance(row, Mapping):
            continue
        if row.get("allowlist_required") is not True or row.get("robots_preflight_required") is not True:
            problems.append("allowlist and robots preflight requirements must be true")
        if row.get("live_fetch_authorized_by_this_packet") is not False:
            problems.append("v8 packet must not authorize live fetch")
    for row in packet.get("no_raw_body_persistence_requirements", []):
        if not isinstance(row, Mapping):
            continue
        if row.get("no_raw_body_persisted_required") is not True:
            problems.append("no raw body persistence must be required for every source")
    for row in packet.get("source_freshness_hold_conditions", []):
        if not isinstance(row, Mapping):
            continue
        if not _text(row.get("hold_condition")):
            problems.append("source freshness hold rows must include hold conditions")
        if row.get("must_hold_currentness_claims") is not True:
            problems.append("source freshness hold rows must hold currentness claims")
        if row.get("must_hold_legal_or_permitting_guarantees") is not True:
            problems.append("source freshness hold rows must hold legal or permitting guarantees")
        if row.get("cleared_by_this_packet") is not False:
            problems.append("source freshness holds must not be cleared by this packet")
    for row in packet.get("rollback_references", []):
        if not isinstance(row, Mapping):
            continue
        if not _text(row.get("rollback_reference")):
            problems.append("rollback rows must include rollback references")
        if row.get("active_registry_mutation") is not False:
            problems.append("rollback rows must keep active registry mutation false")


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f"forbidden true value at {child_path}")
            if _is_forbidden_artifact_key(key_text, child):
                problems.append(f"forbidden artifact or private payload at {child_path}")
            _scan_for_forbidden_payload(child, child_path, problems)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", problems)


def _is_forbidden_artifact_key(key: str, value: Any) -> bool:
    if key in ALLOWED_SAFETY_KEYS:
        return False
    if not FORBIDDEN_ARTIFACT_KEY_RE.search(key):
        return False
    if value in (False, None, "", [], {}):
        return False
    return True


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"fixture must be a JSON object: {path}")
    return payload


def _resolve(fixture_path: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (fixture_path.parent / path).resolve()


def _index_by_source(rows: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise ValueError("source rows must be a non-empty list")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("source row must be an object")
        source_id = _text(row.get("source_id"))
        if not source_id:
            raise ValueError("source row must include source_id")
        result[source_id] = row
    return result


def _safe_index_by_source(rows: Any, problems: list[str], label: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            problems.append(f"{label} rows must be objects")
            continue
        source_id = _text(row.get("source_id"))
        if not source_id:
            problems.append(f"{label} rows must include source_id")
            continue
        if source_id in result:
            problems.append(f"{label} rows must not duplicate source_id {source_id}")
        result[source_id] = row
    return result


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


__all__ = [
    "BOUNDARIES",
    "CONSUMES_ONLY",
    "EXACT_OFFLINE_VALIDATION_COMMANDS",
    "PACKET_TYPE",
    "PACKET_VERSION",
    "VALIDATION_COMMANDS",
    "PublicRefreshAuthorizationPacketV8Error",
    "assert_valid_public_refresh_authorization_packet_v8",
    "build_public_refresh_authorization_packet_v8",
    "build_public_refresh_authorization_packet_v8_from_fixture",
    "validate_public_refresh_authorization_packet_v8",
]
