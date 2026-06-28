"""Fixture-first public refresh authorization packet v6.

This module assembles a public refresh authorization packet from committed
public source freshness watchlist v6 fixtures and post-promotion smoke replay
v6 fixtures only. It does not crawl, download, persist raw bodies, open DevHub,
read private documents, upload, submit, certify, pay, schedule, or provide legal
or permitting guarantees.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.post_promotion_smoke_replay_v6 import (
    build_post_promotion_smoke_replay_v6_from_fixture,
    assert_valid_post_promotion_smoke_replay_v6,
)
from ppd.agent_readiness.public_source_freshness_watchlist_v6 import (
    build_watchlist_from_files,
    validate_watchlist,
)

PACKET_TYPE = "ppd.public_refresh_authorization_packet.v6"
PACKET_VERSION = "v6"
MODE = "fixture_first_public_refresh_authorization_packet_v6"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_authorization_packet_v6.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_refresh_authorization_packet_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_authorization_packet_v6.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "public_source_freshness_watchlist_v6_fixtures_only": True,
    "post_promotion_smoke_replay_v6_fixtures_only": True,
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

ABORT_THRESHOLDS = {
    "robots_disallow_count": 1,
    "outside_allowlist_count": 1,
    "policy_preflight_failure_count": 1,
    "raw_body_persistence_attempt_count": 1,
    "auth_or_private_boundary_hit_count": 1,
    "official_action_attempt_count": 1,
    "reviewer_authorization_missing_count": 1,
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
PRIVATE_KEY_RE = re.compile(r"(^|_)(auth|browser|cookie|credential|download|har|password|payment|private|raw|screenshot|secret|session|storage_state|token|trace)(_|$)", re.IGNORECASE)
ALLOWED_RAW_KEYS = {"no_raw_body_persistence_reminders", "no_raw_body_policy"}


@dataclass(frozen=True)
class PublicRefreshAuthorizationPacketV6Result:
    valid: bool
    problems: tuple[str, ...]


class PublicRefreshAuthorizationPacketV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid public refresh authorization packet v6: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("public refresh authorization fixture must be a JSON object")
    return payload


def build_public_refresh_authorization_packet_v6_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = load_json(fixture_path)
    return build_public_refresh_authorization_packet_v6(
        build_watchlist_from_files(
            _resolve(fixture_path, _text(fixture.get("public_source_registry_fixture"))),
            _resolve(fixture_path, _text(fixture.get("prior_refresh_fixture"))),
        ),
        build_post_promotion_smoke_replay_v6_from_fixture(_resolve(fixture_path, _text(fixture.get("post_promotion_smoke_replay_fixture")))),
        source_fixture_refs=_source_refs_from_fixture(fixture),
    )


def build_public_refresh_authorization_packet_v6(
    freshness_watchlist: Mapping[str, Any],
    post_promotion_smoke_replay: Mapping[str, Any],
    *,
    source_fixture_refs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_watchlist(freshness_watchlist)
    assert_valid_post_promotion_smoke_replay_v6(post_promotion_smoke_replay)
    watch_rows = _mapping_sequence(freshness_watchlist.get("watchlist_rows"))
    smoke_refs = _mapping_sequence(post_promotion_smoke_replay.get("source_fixture_refs"))
    refs = list(source_fixture_refs or []) or [
        {"fixture_role": "public_source_freshness_watchlist_v6", "path": "fixture://public_source_freshness_watchlist_v6"},
        {"fixture_role": "post_promotion_smoke_replay_v6", "path": "fixture://post_promotion_smoke_replay_v6"},
    ]
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "public-refresh-authorization-v6-fixture",
        "mode": MODE,
        "consumes_only": {
            "public_source_freshness_watchlist_v6_fixtures": True,
            "post_promotion_smoke_replay_v6_fixtures": True,
        },
        "source_fixture_refs": refs,
        "boundaries": copy.deepcopy(REQUIRED_BOUNDARIES),
        "live_crawl_deferral_criteria": [_deferral_row(row) for row in watch_rows],
        "allowlisted_source_groups": _allowlisted_groups(freshness_watchlist),
        "robots_and_policy_preflight_checklist_rows": [_preflight_row(row) for row in watch_rows],
        "no_raw_body_persistence_reminders": list(freshness_watchlist.get("no_raw_body_capture_policy_reminders", [])),
        "processor_handoff_manifest_expectations": [_processor_row(row) for row in watch_rows],
        "reviewer_authorization_placeholders": [_reviewer_placeholder(row) for row in watch_rows],
        "abort_thresholds": copy.deepcopy(ABORT_THRESHOLDS),
        "processor_handoff_smoke_refs": _smoke_handoff_refs(smoke_refs),
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_public_refresh_authorization_packet_v6(packet)
    return packet


def assert_valid_public_refresh_authorization_packet_v6(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_authorization_packet_v6(packet)
    if not result.valid:
        raise PublicRefreshAuthorizationPacketV6Error(result.problems)


def validate_public_refresh_authorization_packet_v6(packet: Mapping[str, Any]) -> PublicRefreshAuthorizationPacketV6Result:
    if not isinstance(packet, Mapping):
        return PublicRefreshAuthorizationPacketV6Result(False, ("packet must be an object",))
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v6")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != {"public_source_freshness_watchlist_v6_fixtures": True, "post_promotion_smoke_replay_v6_fixtures": True}:
        problems.append("consumes_only must allow only public source freshness watchlist v6 and post-promotion smoke replay v6 fixtures")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        problems.append("boundaries must deny live crawling, downloads, raw body persistence, DevHub, private documents, official actions, guarantees, and mutation")
    if packet.get("abort_thresholds") != ABORT_THRESHOLDS:
        problems.append("abort_thresholds must exactly match v6 fail-closed thresholds")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must exactly match public refresh authorization v6 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")
    for key in (
        "source_fixture_refs",
        "live_crawl_deferral_criteria",
        "allowlisted_source_groups",
        "robots_and_policy_preflight_checklist_rows",
        "no_raw_body_persistence_reminders",
        "processor_handoff_manifest_expectations",
        "reviewer_authorization_placeholders",
        "processor_handoff_smoke_refs",
    ):
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")
    _validate_refs(packet.get("source_fixture_refs"), problems)
    _validate_deferrals(packet.get("live_crawl_deferral_criteria"), problems)
    _validate_preflight(packet.get("robots_and_policy_preflight_checklist_rows"), problems)
    _validate_processor(packet.get("processor_handoff_manifest_expectations"), problems)
    _validate_reviewers(packet.get("reviewer_authorization_placeholders"), problems)
    _scan_for_forbidden_payload(packet, "packet", problems)
    return PublicRefreshAuthorizationPacketV6Result(not problems, tuple(dict.fromkeys(problems)))


def _deferral_row(row: Mapping[str, Any]) -> dict[str, Any]:
    hold = _mapping(row.get("stale_source_hold_trigger"))
    return {
        "deferral_id": f"defer-live-crawl::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "deferral_required": True,
        "deferral_reasons": list(hold.get("reasons", [])),
        "reviewer_disposition_required": True,
        "live_crawl_authorized": False,
    }


def _allowlisted_groups(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups = _mapping(packet.get("priority_source_groups"))
    rows = []
    for group_id, group in groups.items():
        if isinstance(group, Mapping):
            rows.append({"group_id": str(group_id), "priority": group.get("priority"), "reviewer_owner": _text(group.get("reviewer_owner")), "allowlist_scope": "public_official_sources_only"})
    return sorted(rows, key=lambda row: (row["priority"], row["group_id"]))


def _preflight_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "preflight_id": f"robots-policy::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "canonical_url": _text(row.get("canonical_url")),
        "allowlist_check_required": True,
        "robots_check_required": True,
        "policy_check_required": True,
        "no_raw_body_policy": "metadata_normalized_text_checksums_and_citations_only",
        "preflight_completed": False,
        "crawl_authorized": False,
    }


def _processor_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "manifest_expectation_id": f"processor-handoff::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "expected_manifest_fields": ["source_id", "canonical_url", "requested_url", "redirect_chain", "http_status", "content_type", "content_hash", "processor_name", "processor_version", "normalized_document_id", "skipped_reason", "no_raw_body_persisted"],
        "no_raw_body_persisted_required": True,
        "raw_artifact_ref_allowed": False,
        "handoff_executed": False,
    }


def _reviewer_placeholder(row: Mapping[str, Any]) -> dict[str, Any]:
    escalation = _mapping(row.get("reviewer_escalation"))
    return {
        "placeholder_id": f"reviewer-auth::{_text(row.get('source_id'))}",
        "source_id": _text(row.get("source_id")),
        "reviewer_owner": _text(escalation.get("reviewer_owner")),
        "authorization_status": "pending_manual_review",
        "authorized_by": "",
        "authorized_at": "",
        "crawl_authorized": False,
    }


def _smoke_handoff_refs(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, ref in enumerate(refs):
        rows.append({"smoke_ref_id": f"post-promotion-smoke-ref::{index + 1}", "fixture_role": _text(ref.get("fixture_role")), "path": _text(ref.get("path")), "handoff_expectation": "review_before_processor_handoff"})
    return rows


def _validate_refs(value: Any, problems: list[str]) -> None:
    roles = {_text(row.get("fixture_role")) for row in _mapping_sequence(value)}
    if "public_source_freshness_watchlist_v6" not in roles:
        problems.append("source_fixture_refs must include public_source_freshness_watchlist_v6")
    if "post_promotion_smoke_replay_v6" not in roles:
        problems.append("source_fixture_refs must include post_promotion_smoke_replay_v6")


def _validate_deferrals(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"live_crawl_deferral_criteria[{index}]"
        if row.get("deferral_required") is not True:
            problems.append(f"{prefix}.deferral_required must be true")
        if row.get("live_crawl_authorized") is not False:
            problems.append(f"{prefix}.live_crawl_authorized must be false")
        if row.get("reviewer_disposition_required") is not True:
            problems.append(f"{prefix}.reviewer_disposition_required must be true")


def _validate_preflight(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"robots_and_policy_preflight_checklist_rows[{index}]"
        for key in ("allowlist_check_required", "robots_check_required", "policy_check_required"):
            if row.get(key) is not True:
                problems.append(f"{prefix}.{key} must be true")
        if row.get("preflight_completed") is not False or row.get("crawl_authorized") is not False:
            problems.append(f"{prefix} must remain incomplete and unauthorized")


def _validate_processor(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"processor_handoff_manifest_expectations[{index}]"
        fields = row.get("expected_manifest_fields")
        if not isinstance(fields, list) or "no_raw_body_persisted" not in fields:
            problems.append(f"{prefix}.expected_manifest_fields must include no_raw_body_persisted")
        if row.get("no_raw_body_persisted_required") is not True:
            problems.append(f"{prefix}.no_raw_body_persisted_required must be true")
        if row.get("raw_artifact_ref_allowed") is not False or row.get("handoff_executed") is not False:
            problems.append(f"{prefix} must not allow raw artifact refs or executed handoff")


def _validate_reviewers(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"reviewer_authorization_placeholders[{index}]"
        if row.get("authorization_status") != "pending_manual_review":
            problems.append(f"{prefix}.authorization_status must be pending_manual_review")
        if row.get("crawl_authorized") is not False:
            problems.append(f"{prefix}.crawl_authorized must be false")


def _source_refs_from_fixture(fixture: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"fixture_role": "public_source_freshness_watchlist_v6", "path": _text(fixture.get("public_source_registry_fixture"))},
        {"fixture_role": "public_source_freshness_watchlist_v6", "path": _text(fixture.get("prior_refresh_fixture"))},
        {"fixture_role": "post_promotion_smoke_replay_v6", "path": _text(fixture.get("post_promotion_smoke_replay_fixture"))},
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
            if normalized not in ALLOWED_RAW_KEYS and PRIVATE_KEY_RE.search(normalized) and _truthy(child):
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
