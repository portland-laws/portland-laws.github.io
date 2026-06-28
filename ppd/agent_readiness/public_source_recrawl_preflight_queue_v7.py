"""Fixture-first public source recrawl preflight queue v7.

This module consumes only public refresh authorization packet v7 fixtures,
the committed public crawler allowlist fixture, and committed robots-policy
fixtures. It assembles offline canonical URL queue rows, redirect expectation
placeholders, skip-reason rows, host policy decisions, rate-limit reminders,
processor handoff eligibility notes, and exact offline validation commands.
It does not crawl, download raw artifacts, open DevHub, read private documents,
upload, submit, certify, pay, schedule, or make legal or permitting guarantees.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ppd.agent_readiness.public_refresh_authorization_packet_v7 import (
    build_public_refresh_authorization_packet_v7_from_fixture,
    validate_public_refresh_authorization_packet_v7,
)

PACKET_TYPE = "ppd.public_source_recrawl_preflight_queue.v7"
PACKET_VERSION = "v7"
MODE = "fixture_first_public_source_recrawl_preflight_queue_v7"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/public_source_recrawl_preflight_queue_v7.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_source_recrawl_preflight_queue_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_source_recrawl_preflight_queue_v7.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

BOUNDARIES = {
    "fixture_first": True,
    "public_refresh_authorization_packet_v7_fixtures_only": True,
    "committed_allowlist_fixture_only": True,
    "committed_robots_policy_fixture_only": True,
    "live_crawl_executed": False,
    "network_requests_performed": False,
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
        "network_requests_performed",
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

PROHIBITED_TEXT = (
    "live crawl completed",
    "fetched live",
    "opened devhub",
    "logged in to devhub",
    "raw body persisted",
    "downloaded document",
    "uploaded correction",
    "submitted permit",
    "certified acknowledgement",
    "paid fee",
    "scheduled inspection",
    "legal advice",
    "permit will be approved",
)


@dataclass(frozen=True)
class PublicSourceRecrawlPreflightQueueV7Result:
    valid: bool
    problems: tuple[str, ...]


class PublicSourceRecrawlPreflightQueueV7Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid public source recrawl preflight queue v7: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    return payload


def build_public_source_recrawl_preflight_queue_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = load_json(fixture_path)
    authorization_packet = build_public_refresh_authorization_packet_v7_from_fixture(
        _resolve(fixture_path, _text(fixture.get("public_refresh_authorization_fixture")))
    )
    allowlist = load_json(_resolve(fixture_path, _text(fixture.get("allowlist_fixture"))))
    robots_policy = load_json(_resolve(fixture_path, _text(fixture.get("robots_policy_fixture"))))
    return build_public_source_recrawl_preflight_queue_v7(
        authorization_packet,
        allowlist,
        robots_policy,
        source_fixture_refs=_source_refs_from_fixture(fixture),
    )


def build_public_source_recrawl_preflight_queue_v7(
    authorization_packet: Mapping[str, Any],
    allowlist: Mapping[str, Any],
    robots_policy: Mapping[str, Any],
    *,
    source_fixture_refs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    auth_result = validate_public_refresh_authorization_packet_v7(authorization_packet)
    if not auth_result.valid:
        raise PublicSourceRecrawlPreflightQueueV7Error(auth_result.problems)

    refs = list(source_fixture_refs or []) or [
        {"fixture_role": "public_refresh_authorization_packet_v7", "path": "fixture://public-refresh-authorization-v7"},
        {"fixture_role": "committed_allowlist", "path": "fixture://ppd-crawler-allowlist"},
        {"fixture_role": "committed_robots_policy", "path": "fixture://robots-policy"},
    ]
    preconditions = _mapping_sequence(authorization_packet.get("source_freshness_preconditions"))
    auth_by_source = {_text(row.get("source_id")): row for row in preconditions}

    host_policy_decisions: list[dict[str, Any]] = []
    queue_rows: list[dict[str, Any]] = []
    skip_rows: list[dict[str, Any]] = []
    redirect_placeholders: list[dict[str, Any]] = []
    handoff_notes: list[dict[str, Any]] = []

    for row in preconditions:
        source_id = _text(row.get("source_id"))
        canonical_url = _text(row.get("canonical_url"))
        host_decision = _host_policy_decision(source_id, canonical_url, allowlist, robots_policy)
        host_policy_decisions.append(host_decision)
        redirect_placeholders.append(_redirect_placeholder(source_id, canonical_url))
        skip_reason = _skip_reason(row, host_decision)
        if skip_reason:
            skip_rows.append(_skip_row(source_id, canonical_url, skip_reason, host_decision))
            handoff_notes.append(_processor_handoff_note(source_id, canonical_url, False, skip_reason))
            continue
        queue_rows.append(_queue_row(row, host_decision, len(queue_rows) + 1))
        handoff_notes.append(_processor_handoff_note(source_id, canonical_url, True, "eligible_after_separate_approved_offline_preflight_review"))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "public-source-recrawl-preflight-queue-v7-fixture",
        "mode": MODE,
        "consumes_only": {
            "public_refresh_authorization_packet_v7_fixtures": True,
            "committed_allowlist_fixtures": True,
            "committed_robots_policy_fixtures": True,
        },
        "source_fixture_refs": refs,
        "boundaries": copy.deepcopy(BOUNDARIES),
        "canonical_url_queue_rows": queue_rows,
        "redirect_expectation_placeholders": redirect_placeholders,
        "skip_reason_rows": skip_rows,
        "host_policy_decisions": host_policy_decisions,
        "rate_limit_reminders": _rate_limit_reminders(host_policy_decisions, robots_policy),
        "processor_handoff_eligibility_notes": handoff_notes,
        "authorization_source_count": len(auth_by_source),
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_public_source_recrawl_preflight_queue_v7(packet)
    return packet


def assert_valid_public_source_recrawl_preflight_queue_v7(packet: Mapping[str, Any]) -> None:
    result = validate_public_source_recrawl_preflight_queue_v7(packet)
    if not result.valid:
        raise PublicSourceRecrawlPreflightQueueV7Error(result.problems)


def validate_public_source_recrawl_preflight_queue_v7(packet: Mapping[str, Any]) -> PublicSourceRecrawlPreflightQueueV7Result:
    if not isinstance(packet, Mapping):
        return PublicSourceRecrawlPreflightQueueV7Result(False, ("packet must be an object",))
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v7")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != {
        "public_refresh_authorization_packet_v7_fixtures": True,
        "committed_allowlist_fixtures": True,
        "committed_robots_policy_fixtures": True,
    }:
        problems.append("consumes_only must name only public refresh authorization v7, allowlist, and robots-policy fixtures")
    if packet.get("boundaries") != BOUNDARIES:
        problems.append("boundaries must deny live crawl, network, raw artifacts, DevHub, private documents, official actions, guarantees, and mutation")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must exactly match public source recrawl preflight queue v7 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")
    _validate_refs(packet.get("source_fixture_refs"), problems)
    _validate_queue_rows(packet.get("canonical_url_queue_rows"), problems)
    _validate_redirects(packet.get("redirect_expectation_placeholders"), problems)
    _validate_skip_rows(packet.get("skip_reason_rows"), problems)
    _validate_host_decisions(packet.get("host_policy_decisions"), problems)
    _validate_rate_limits(packet.get("rate_limit_reminders"), problems)
    _validate_handoff_notes(packet.get("processor_handoff_eligibility_notes"), problems)
    _scan_for_forbidden_payload(packet, "packet", problems)
    return PublicSourceRecrawlPreflightQueueV7Result(not problems, tuple(dict.fromkeys(problems)))


def _queue_row(row: Mapping[str, Any], host_decision: Mapping[str, Any], ordinal: int) -> dict[str, Any]:
    source_id = _text(row.get("source_id"))
    return {
        "queue_row_id": f"recrawl-queue-v7::{ordinal:03d}::{source_id}",
        "source_id": source_id,
        "canonical_url": _text(row.get("canonical_url")),
        "request_method": "GET",
        "queue_state": "queued_for_future_separately_authorized_public_metadata_recrawl",
        "metadata_only": True,
        "no_raw_body_persisted": True,
        "live_network_invoked": False,
        "raw_download_invoked": False,
        "robots_policy_decision_id": _text(host_decision.get("decision_id")),
        "allowlist_decision_id": _text(host_decision.get("decision_id")),
        "processor_policy": "metadata_and_normalized_text_only_no_raw_artifacts",
        "rate_limit_reminder_id": f"rate-limit::{_text(host_decision.get('host'))}",
    }


def _redirect_placeholder(source_id: str, canonical_url: str) -> dict[str, Any]:
    return {
        "redirect_expectation_id": f"redirect-placeholder::{source_id}",
        "source_id": source_id,
        "requested_url": canonical_url,
        "canonical_url": canonical_url,
        "expected_redirect_chain_placeholder": [],
        "live_redirect_resolution_performed": False,
        "final_url_must_remain_official_public_anchor": True,
    }


def _skip_row(source_id: str, canonical_url: str, skip_reason: str, host_decision: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "skip_row_id": f"recrawl-skip-v7::{source_id}",
        "source_id": source_id,
        "canonical_url": canonical_url,
        "skip_reason": skip_reason,
        "host_policy_decision_id": _text(host_decision.get("decision_id")),
        "metadata_capture_allowed": False,
        "processor_handoff_allowed": False,
        "live_network_invoked": False,
        "raw_download_invoked": False,
    }


def _processor_handoff_note(source_id: str, canonical_url: str, eligible: bool, reason: str) -> dict[str, Any]:
    return {
        "handoff_note_id": f"processor-handoff::{source_id}",
        "source_id": source_id,
        "canonical_url": canonical_url,
        "processor_handoff_eligible": eligible,
        "eligibility_note": reason,
        "metadata_only_manifest_required": True,
        "raw_artifact_ref_allowed": False,
        "requires_separate_operator_approval_before_live_processor_run": True,
    }


def _host_policy_decision(source_id: str, canonical_url: str, allowlist: Mapping[str, Any], robots_policy: Mapping[str, Any]) -> dict[str, Any]:
    parsed = urlparse(canonical_url)
    host = parsed.netloc.lower()
    path = parsed.path or "/"
    allow = _allowlist_entry(host, allowlist)
    allowlist_allowed = bool(allow) and parsed.scheme == _text(allow.get("scheme"))
    if allowlist_allowed:
        prefixes = _string_list(allow.get("allowed_path_prefixes"))
        fragments = _string_list(allow.get("disallowed_path_fragments"))
        allowlist_allowed = any(path.startswith(prefix) for prefix in prefixes) and not any(fragment in canonical_url.lower() for fragment in fragments)
    robots = _mapping(_mapping(robots_policy.get("hosts")).get(host))
    disallowed_paths = _string_list(robots.get("disallowed_path_prefixes"))
    robots_allowed = _text(robots.get("default_decision")) == "allowed" and not any(path.startswith(prefix) for prefix in disallowed_paths)
    status = "allowed" if allowlist_allowed and robots_allowed else "blocked"
    reasons: list[str] = []
    if not allowlist_allowed:
        reasons.append("allowlist_denied_or_out_of_scope")
    if not robots_allowed:
        reasons.append("robots_policy_denied_or_missing")
    return {
        "decision_id": f"host-policy::{source_id}",
        "source_id": source_id,
        "canonical_url": canonical_url,
        "host": host,
        "scheme": parsed.scheme,
        "allowlist_allowed": allowlist_allowed,
        "robots_allowed": robots_allowed,
        "decision": status,
        "decision_reasons": reasons or ["allowlist_and_robots_policy_fixture_allow_public_metadata_preflight"],
        "crawl_delay_seconds": robots.get("crawl_delay_seconds"),
        "live_network_invoked": False,
    }


def _rate_limit_reminders(host_policy_decisions: Sequence[Mapping[str, Any]], robots_policy: Mapping[str, Any]) -> list[dict[str, Any]]:
    hosts = sorted({_text(row.get("host")) for row in host_policy_decisions if _text(row.get("host"))})
    rows: list[dict[str, Any]] = []
    for host in hosts:
        robots = _mapping(_mapping(robots_policy.get("hosts")).get(host))
        rows.append(
            {
                "rate_limit_reminder_id": f"rate-limit::{host}",
                "host": host,
                "crawl_delay_seconds": robots.get("crawl_delay_seconds"),
                "reminder": "Honor committed robots-policy crawl delay and operator-approved rate limits before any future live public recrawl.",
                "live_crawl_authorized": False,
            }
        )
    return rows


def _skip_reason(row: Mapping[str, Any], host_decision: Mapping[str, Any]) -> str:
    if host_decision.get("allowlist_allowed") is not True:
        return "host_or_path_not_allowlisted"
    if host_decision.get("robots_allowed") is not True:
        return "robots_policy_disallowed"
    if row.get("is_stale_by_age") is not True:
        return "source_not_stale_in_authorization_fixture"
    if row.get("live_crawl_authorized") is not False:
        return "authorization_fixture_did_not_deny_live_crawl"
    return ""


def _validate_refs(value: Any, problems: list[str]) -> None:
    roles = {_text(row.get("fixture_role")) for row in _mapping_sequence(value)}
    expected = {"public_refresh_authorization_packet_v7", "committed_allowlist", "committed_robots_policy"}
    if roles != expected:
        problems.append("source_fixture_refs must include only public_refresh_authorization_packet_v7, committed_allowlist, and committed_robots_policy roles")


def _validate_queue_rows(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append("canonical_url_queue_rows must be a non-empty list")
    for index, row in enumerate(rows):
        prefix = f"canonical_url_queue_rows[{index}]"
        if row.get("request_method") != "GET":
            problems.append(f"{prefix}.request_method must be GET")
        for key in ("metadata_only", "no_raw_body_persisted"):
            if row.get(key) is not True:
                problems.append(f"{prefix}.{key} must be true")
        for key in ("live_network_invoked", "raw_download_invoked"):
            if row.get(key) is not False:
                problems.append(f"{prefix}.{key} must be false")
        if not _official_url(_text(row.get("canonical_url"))):
            problems.append(f"{prefix}.canonical_url must be an official public PP&D anchor")


def _validate_redirects(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append("redirect_expectation_placeholders must be a non-empty list")
    for index, row in enumerate(rows):
        prefix = f"redirect_expectation_placeholders[{index}]"
        if row.get("live_redirect_resolution_performed") is not False:
            problems.append(f"{prefix}.live_redirect_resolution_performed must be false")
        if row.get("final_url_must_remain_official_public_anchor") is not True:
            problems.append(f"{prefix}.final_url_must_remain_official_public_anchor must be true")
        if not isinstance(row.get("expected_redirect_chain_placeholder"), list):
            problems.append(f"{prefix}.expected_redirect_chain_placeholder must be a list")


def _validate_skip_rows(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append("skip_reason_rows must be a non-empty list")
    for index, row in enumerate(rows):
        prefix = f"skip_reason_rows[{index}]"
        if not _text(row.get("skip_reason")):
            problems.append(f"{prefix}.skip_reason is required")
        if row.get("metadata_capture_allowed") is not False or row.get("processor_handoff_allowed") is not False:
            problems.append(f"{prefix} must deny metadata capture and processor handoff")
        if row.get("live_network_invoked") is not False or row.get("raw_download_invoked") is not False:
            problems.append(f"{prefix} must deny live network and raw download invocation")


def _validate_host_decisions(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append("host_policy_decisions must be a non-empty list")
    for index, row in enumerate(rows):
        prefix = f"host_policy_decisions[{index}]"
        if row.get("decision") not in {"allowed", "blocked"}:
            problems.append(f"{prefix}.decision must be allowed or blocked")
        if not isinstance(row.get("allowlist_allowed"), bool) or not isinstance(row.get("robots_allowed"), bool):
            problems.append(f"{prefix} must include boolean allowlist_allowed and robots_allowed")
        if row.get("live_network_invoked") is not False:
            problems.append(f"{prefix}.live_network_invoked must be false")


def _validate_rate_limits(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append("rate_limit_reminders must be a non-empty list")
    for index, row in enumerate(rows):
        if row.get("live_crawl_authorized") is not False:
            problems.append(f"rate_limit_reminders[{index}].live_crawl_authorized must be false")


def _validate_handoff_notes(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append("processor_handoff_eligibility_notes must be a non-empty list")
    for index, row in enumerate(rows):
        prefix = f"processor_handoff_eligibility_notes[{index}]"
        if not isinstance(row.get("processor_handoff_eligible"), bool):
            problems.append(f"{prefix}.processor_handoff_eligible must be boolean")
        if row.get("metadata_only_manifest_required") is not True:
            problems.append(f"{prefix}.metadata_only_manifest_required must be true")
        if row.get("raw_artifact_ref_allowed") is not False:
            problems.append(f"{prefix}.raw_artifact_ref_allowed must be false")
        if row.get("requires_separate_operator_approval_before_live_processor_run") is not True:
            problems.append(f"{prefix}.requires_separate_operator_approval_before_live_processor_run must be true")


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized in FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f"{child_path} must not be true")
            _scan_for_forbidden_payload(child, child_path, problems)
    elif isinstance(value, str):
        lower = value.lower()
        for fragment in PROHIBITED_TEXT:
            if fragment in lower:
                problems.append(f"{path} must not claim live crawl, DevHub, raw artifact, official action, or legal outcome completion")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", problems)


def _allowlist_entry(host: str, allowlist: Mapping[str, Any]) -> Mapping[str, Any]:
    for entry in _mapping_sequence(allowlist.get("allowed_hosts")):
        if _text(entry.get("host")).lower() == host:
            return entry
    return {}


def _source_refs_from_fixture(fixture: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"fixture_role": "public_refresh_authorization_packet_v7", "path": _text(fixture.get("public_refresh_authorization_fixture"))},
        {"fixture_role": "committed_allowlist", "path": _text(fixture.get("allowlist_fixture"))},
        {"fixture_role": "committed_robots_policy", "path": _text(fixture.get("robots_policy_fixture"))},
    ]


def _resolve(base: Path, value: str) -> Path:
    if not value:
        raise ValueError("fixture path is required")
    path = Path(value)
    if path.exists():
        return path
    return (base.parent / path).resolve()


def _official_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.netloc.lower() in {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
