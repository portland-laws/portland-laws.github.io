"""Fixture-first PP&D post-decision release readiness digest.

The digest produced here is metadata-only. It consumes committed decision and
reconciliation packets, summarizes what is still blocked, records the offline
capabilities reviewers may use, and keeps every live or authenticated action
deferred until a later attended review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


PACKET_TYPE = "ppd.post_decision_release_readiness_digest.v1"
REQUIRED_INPUTS = {
    "public_source_registry_promotion_decision",
    "guardrail_activation_decision",
    "source_freshness_drift_digest",
    "devhub_read_only_pilot_readiness_reconciliation",
}
DECISION_INPUTS = {
    "public_source_registry_promotion_decision",
    "guardrail_activation_decision",
}
RECONCILIATION_INPUTS = {
    "devhub_read_only_pilot_readiness_reconciliation",
}
FORBIDDEN_KEYS = {
    "archive_artifact_ref",
    "auth_state",
    "browser_session",
    "cookie",
    "credentials",
    "download_archive_ref",
    "downloaded_document_path",
    "field_value",
    "har",
    "known_facts",
    "local_path",
    "password",
    "private_case_fact",
    "raw_archive_ref",
    "raw_body",
    "raw_crawl_output",
    "raw_download_ref",
    "raw_html",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
    "value",
    "warc_path",
}
FORBIDDEN_KEY_FRAGMENTS = (
    "archive_artifact",
    "browser_trace",
    "download_path",
    "downloaded_document",
    "raw_archive",
    "raw_body",
    "raw_crawl",
    "raw_download",
    "raw_html",
    "session_artifact",
)
FORBIDDEN_TEXT = (
    "/home/",
    "/Users/",
    "auth-state",
    "cookie=",
    "password=",
    "session=",
    "storage_state",
    "trace.zip",
    ".har",
    ".warc",
    "raw-crawl/",
    "raw-download/",
)
LIVE_ACTION_MARKERS = (
    "apply_live_registry_write",
    "enable_live_enforcement",
    "execute_live_crawl",
    "open_authenticated_devhub",
)
LIVE_EXECUTION_KEYS = {
    "authenticated_devhub_automation_performed",
    "devhub_execution_performed",
    "devhub_session_opened",
    "live_crawl_executed",
    "live_devhub_executed",
    "live_network_called",
    "live_network_executed",
}
CONSEQUENTIAL_CAPABILITY_FRAGMENTS = (
    "cancel",
    "cancellation",
    "certification",
    "certify",
    "payment",
    "schedule",
    "scheduling",
    "submission",
    "submit",
    "upload",
)
PRODUCTION_READY_LABELS = {
    "production-ready",
    "production_ready",
    "ready_for_production",
    "release_ready",
    "production ready",
}


class PostDecisionReleaseReadinessDigestError(ValueError):
    """Raised when a post-decision release readiness digest is unsafe."""


def load_fixture(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise PostDecisionReleaseReadinessDigestError("post-decision fixture must be a JSON object")
    return value


def build_post_decision_release_readiness_digest(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic metadata-only release readiness digest."""

    input_map = _mapping(inputs.get("inputs")) if "inputs" in inputs else _mapping(inputs)
    missing = sorted(REQUIRED_INPUTS - set(input_map))
    if missing:
        raise PostDecisionReleaseReadinessDigestError("missing required inputs: " + ", ".join(missing))
    input_errors = _input_packet_errors(input_map)
    if input_errors:
        raise PostDecisionReleaseReadinessDigestError("invalid post-decision inputs: " + "; ".join(input_errors))

    source_decision = _mapping(input_map["public_source_registry_promotion_decision"])
    guardrail_decision = _mapping(input_map["guardrail_activation_decision"])
    drift_digest = _mapping(input_map["source_freshness_drift_digest"])
    devhub_reconciliation = _mapping(input_map["devhub_read_only_pilot_readiness_reconciliation"])

    blockers = _remaining_blockers(source_decision, guardrail_decision, drift_digest, devhub_reconciliation)
    digest = {
        "packet_type": PACKET_TYPE,
        "packet_id": "ppd-post-decision-release-readiness-2026-05-28",
        "fixture_first": True,
        "metadata_only": True,
        "generated_from_fixtures": True,
        "live_actions_performed": False,
        "private_artifacts_included": False,
        "release_status": "blocked" if blockers else "offline_ready",
        "inputs_consumed": _inputs_consumed(input_map),
        "remaining_blockers": blockers,
        "approved_offline_only_capabilities": _approved_offline_only_capabilities(),
        "deferred_live_actions": _deferred_live_actions(),
        "readiness_claims": _readiness_claims(input_map),
        "reviewer_prompts": _reviewer_prompts(blockers),
        "rollback_references": _rollback_references(source_decision, guardrail_decision, drift_digest, devhub_reconciliation),
        "next_safe_daemon_work": _next_safe_daemon_work(blockers),
        "safety_summary": {
            "source_registry_mutation_allowed": False,
            "live_guardrail_enforcement_allowed": False,
            "live_network_crawl_allowed": False,
            "authenticated_devhub_automation_allowed": False,
            "offline_fixture_validation_allowed": True,
        },
    }
    assert_valid_digest(digest)
    return digest


def validate_digest(digest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if digest.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    for key in ("fixture_first", "metadata_only", "generated_from_fixtures"):
        if digest.get(key) is not True:
            errors.append(f"{key} must be true")
    if digest.get("live_actions_performed") is not False:
        errors.append("live_actions_performed must be false")
    if digest.get("private_artifacts_included") is not False:
        errors.append("private_artifacts_included must be false")

    consumed = [_mapping(item) for item in _sequence(digest.get("inputs_consumed"))]
    consumed_roles = {item.get("input_role") for item in consumed}
    for role in sorted(REQUIRED_INPUTS - consumed_roles):
        errors.append(f"inputs_consumed missing {role}")
    for index, item in enumerate(consumed):
        role = _text(item.get("input_role"))
        if role in DECISION_INPUTS and not _text(item.get("decision_link_id")):
            errors.append(f"inputs_consumed[{index}] missing decision_link_id")
        if role in RECONCILIATION_INPUTS and not _text(item.get("reconciliation_link_id")):
            errors.append(f"inputs_consumed[{index}] missing reconciliation_link_id")

    if not _sequence(digest.get("approved_offline_only_capabilities")):
        errors.append("approved_offline_only_capabilities must be non-empty")
    if not _sequence(digest.get("deferred_live_actions")):
        errors.append("deferred_live_actions must be non-empty")
    if not _sequence(digest.get("reviewer_prompts")):
        errors.append("reviewer_prompts must be non-empty")
    if not _sequence(digest.get("rollback_references")):
        errors.append("rollback_references must be non-empty")
    if not _sequence(digest.get("next_safe_daemon_work")):
        errors.append("next_safe_daemon_work must be non-empty")

    blockers = _sequence(digest.get("remaining_blockers"))
    if blockers and _is_production_ready_text(digest.get("release_status")):
        errors.append("release_status must not be production-ready while blockers remain")

    for index, action in enumerate(_sequence(digest.get("deferred_live_actions"))):
        record = _mapping(action)
        if record.get("deferred") is not True:
            errors.append(f"deferred_live_actions[{index}].deferred must be true")
        if record.get("allowed_now") is not False:
            errors.append(f"deferred_live_actions[{index}].allowed_now must be false")

    for index, capability in enumerate(_sequence(digest.get("approved_offline_only_capabilities"))):
        record = _mapping(capability)
        if record.get("allowed_now") is not True:
            errors.append(f"approved_offline_only_capabilities[{index}].allowed_now must be true")
        if record.get("requires_live_network") is not False:
            errors.append(f"approved_offline_only_capabilities[{index}].requires_live_network must be false")
        if _capability_is_consequential(record) and record.get("allowed_now") is not False:
            errors.append(f"approved_offline_only_capabilities[{index}] enables a consequential capability")

    _validate_readiness_claims(digest.get("readiness_claims"), "$.readiness_claims", errors)
    _validate_rollback_references(digest, consumed, errors)

    safety = _mapping(digest.get("safety_summary"))
    for key in (
        "source_registry_mutation_allowed",
        "live_guardrail_enforcement_allowed",
        "live_network_crawl_allowed",
        "authenticated_devhub_automation_allowed",
    ):
        if safety.get(key) is not False:
            errors.append(f"safety_summary.{key} must be false")

    errors.extend(_private_artifact_errors(digest, "$"))
    errors.extend(_live_action_marker_errors(digest, "$"))
    errors.extend(_live_execution_claim_errors(digest, "$"))
    errors.extend(_production_ready_text_errors(digest, "$", bool(blockers)))
    return _dedupe(errors)


def assert_valid_digest(digest: Mapping[str, Any]) -> None:
    errors = validate_digest(digest)
    if errors:
        raise PostDecisionReleaseReadinessDigestError("invalid post-decision release readiness digest: " + "; ".join(errors))


def _input_packet_errors(input_map: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for role in sorted(REQUIRED_INPUTS):
        packet = _mapping(input_map.get(role))
        if not _text(packet.get("packet_id")):
            errors.append(f"{role} missing packet_id")
        if role in DECISION_INPUTS and not _text(packet.get("decision_link_id")):
            errors.append(f"{role} missing decision_link_id")
        if role in RECONCILIATION_INPUTS and not _text(packet.get("reconciliation_link_id")):
            errors.append(f"{role} missing reconciliation_link_id")
    errors.extend(_private_artifact_errors(input_map, "inputs"))
    errors.extend(_live_execution_claim_errors(input_map, "inputs"))
    return _dedupe(errors)


def _inputs_consumed(input_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    consumed = []
    for role in sorted(REQUIRED_INPUTS):
        packet = _mapping(input_map[role])
        record = {
            "input_role": role,
            "packet_id": _text(packet.get("packet_id"), role),
            "fixture_path": _text(packet.get("fixture_path"), "ppd/tests/fixtures/post_decision_release_readiness_digest/input_packets.json"),
            "metadata_only": packet.get("metadata_only", True) is True,
        }
        if role in DECISION_INPUTS:
            record["decision_link_id"] = _text(packet.get("decision_link_id"))
        if role in RECONCILIATION_INPUTS:
            record["reconciliation_link_id"] = _text(packet.get("reconciliation_link_id"))
        consumed.append(record)
    return consumed


def _remaining_blockers(source_decision: Mapping[str, Any], guardrail_decision: Mapping[str, Any], drift_digest: Mapping[str, Any], devhub_reconciliation: Mapping[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    blockers.extend(_named_blockers("source_registry", source_decision.get("remaining_blockers") or source_decision.get("unresolved_blockers")))
    blockers.extend(_named_blockers("guardrail_activation", guardrail_decision.get("remaining_blockers") or guardrail_decision.get("release_gate_blockers_acknowledged")))
    blockers.extend(_named_blockers("source_freshness", drift_digest.get("remaining_blockers") or drift_digest.get("stale_sources")))
    blockers.extend(_named_blockers("devhub_read_only_pilot", devhub_reconciliation.get("remaining_blockers") or devhub_reconciliation.get("blocked_findings")))
    return blockers


def _named_blockers(source: str, value: Any) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for index, item in enumerate(_sequence(value)):
        record = _mapping(item)
        status = _text(record.get("status") or record.get("state"), "blocked").lower()
        if status in {"resolved", "closed", "cleared", "not_blocking"}:
            continue
        blockers.append(
            {
                "blocker_id": _text(record.get("blocker_id") or record.get("id"), f"{source}.blocker.{index}"),
                "source_packet": source,
                "status": status or "blocked",
                "summary": _text(record.get("summary") or record.get("description") or record.get("reason"), "review required before release"),
            }
        )
    return blockers


def _approved_offline_only_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "capability_id": "offline.metadata_packet_review",
            "summary": "Review metadata-only source registry, guardrail, freshness, and DevHub readiness packets.",
            "allowed_now": True,
            "requires_live_network": False,
        },
        {
            "capability_id": "offline.fixture_validation",
            "summary": "Run deterministic fixture validation and schema checks without live crawl or authentication.",
            "allowed_now": True,
            "requires_live_network": False,
        },
        {
            "capability_id": "offline.reviewer_prompt_preparation",
            "summary": "Prepare reviewer prompts and rollback notes for the next attended decision checkpoint.",
            "allowed_now": True,
            "requires_live_network": False,
        },
    ]


def _deferred_live_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": "source_registry.live_write", "summary": "Write promoted records into the live SourceRegistry.", "deferred": True, "allowed_now": False},
        {"action_id": "guardrails.enable_live_enforcement", "summary": "Enable active guardrail bundle enforcement for agent traffic.", "deferred": True, "allowed_now": False},
        {"action_id": "freshness.execute_live_recrawl", "summary": "Run live public recrawl or fetch operations for drift verification.", "deferred": True, "allowed_now": False},
        {"action_id": "devhub.authenticated_read_only_pilot", "summary": "Open or automate an authenticated DevHub read-only browser session.", "deferred": True, "allowed_now": False},
    ]


def _readiness_claims(input_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for role in sorted(REQUIRED_INPUTS):
        packet = _mapping(input_map[role])
        for index, item in enumerate(_sequence(packet.get("readiness_claims"))):
            claim = _mapping(item)
            claims.append(
                {
                    "claim_id": _text(claim.get("claim_id"), f"{role}.claim.{index}"),
                    "source_packet_id": _text(packet.get("packet_id"), role),
                    "claim": _text(claim.get("claim"), "metadata-only readiness claim"),
                    "citation_ids": list(_text_sequence(claim.get("citation_ids") or claim.get("source_evidence_ids"))),
                }
            )
    return claims


def _reviewer_prompts(blockers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    prompts = [
        {
            "prompt_id": "review.release_status",
            "question": "Do the listed blockers still prevent post-decision release, or can any be closed with fixture evidence?",
            "required_before_live_action": True,
        },
        {
            "prompt_id": "review.offline_capabilities",
            "question": "Are the approved capabilities still limited to metadata review, fixture validation, and prompt preparation?",
            "required_before_live_action": True,
        },
    ]
    if blockers:
        prompts.append(
            {
                "prompt_id": "review.blocker_resolution_order",
                "question": "Which blocker should the daemon resolve first using only committed fixtures and validation code?",
                "required_before_live_action": True,
            }
        )
    return prompts


def _rollback_references(source_decision: Mapping[str, Any], guardrail_decision: Mapping[str, Any], drift_digest: Mapping[str, Any], devhub_reconciliation: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "rollback_id": "rollback.source_registry_candidate_only",
            "source_packet_id": _text(source_decision.get("packet_id"), "public_source_registry_promotion_decision"),
            "summary": "Discard staged source-registry candidate metadata; no live registry rollback is required.",
        },
        {
            "rollback_id": "rollback.keep_guardrails_disabled",
            "source_packet_id": _text(guardrail_decision.get("packet_id"), "guardrail_activation_decision"),
            "summary": "Keep active guardrail bundles unchanged and live enforcement disabled.",
        },
        {
            "rollback_id": "rollback.source_freshness_metadata_only",
            "source_packet_id": _text(drift_digest.get("packet_id"), "source_freshness_drift_digest"),
            "summary": "Discard staged drift metadata; no live crawl, download, or archive cleanup is required.",
        },
        {
            "rollback_id": "rollback.devhub_no_session_artifacts",
            "source_packet_id": _text(devhub_reconciliation.get("packet_id"), "devhub_read_only_pilot_readiness_reconciliation"),
            "summary": "No DevHub browser state, trace, screenshot, or authenticated artifact exists to clean up.",
        },
    ]


def _next_safe_daemon_work(blockers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if blockers:
        first = blockers[0]
        return [
            {
                "work_id": "daemon.resolve_first_release_blocker_with_fixture",
                "summary": "Add or update the smallest fixture-backed validator needed to close the first remaining blocker.",
                "blocked_by": first.get("blocker_id", "unknown_blocker"),
                "live_actions_allowed": False,
            }
        ]
    return [
        {
            "work_id": "daemon.prepare_attended_release_review_packet",
            "summary": "Prepare the next metadata-only attended release review packet; do not perform live actions.",
            "blocked_by": None,
            "live_actions_allowed": False,
        }
    ]


def _validate_readiness_claims(value: Any, path: str, errors: list[str]) -> None:
    claims = _sequence(value)
    if not claims:
        errors.append(f"{path} must include cited readiness claims")
        return
    for index, item in enumerate(claims):
        claim = _mapping(item)
        if not _text(claim.get("claim")):
            errors.append(f"{path}[{index}] missing claim")
        if not _text_sequence(claim.get("citation_ids") or claim.get("source_evidence_ids")):
            errors.append(f"{path}[{index}] has uncited readiness claim")


def _validate_rollback_references(digest: Mapping[str, Any], consumed: Sequence[Mapping[str, Any]], errors: list[str]) -> None:
    refs = [_mapping(item) for item in _sequence(digest.get("rollback_references"))]
    if not refs:
        errors.append("rollback_references must be non-empty")
        return
    covered_packet_ids = {_text(item.get("source_packet_id")) for item in refs if _text(item.get("source_packet_id"))}
    for index, item in enumerate(refs):
        if not _text(item.get("rollback_id")):
            errors.append(f"rollback_references[{index}] missing rollback_id")
        if not _text(item.get("source_packet_id")):
            errors.append(f"rollback_references[{index}] missing source_packet_id")
        if not _text(item.get("summary")):
            errors.append(f"rollback_references[{index}] missing summary")
    for item in consumed:
        packet_id = _text(item.get("packet_id"))
        if packet_id and packet_id not in covered_packet_ids:
            errors.append(f"rollback_references missing source packet {packet_id}")


def _private_artifact_errors(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_lower in FORBIDDEN_KEYS and child not in (None, "", [], {}):
                errors.append(f"{child_path} uses forbidden private artifact field")
            if any(fragment in key_lower for fragment in FORBIDDEN_KEY_FRAGMENTS) and child not in (None, "", [], {}):
                errors.append(f"{child_path} references forbidden raw/download/archive artifact field")
            errors.extend(_private_artifact_errors(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_private_artifact_errors(child, f"{path}[{index}]"))
    elif isinstance(value, str) and any(marker in value for marker in FORBIDDEN_TEXT):
        errors.append(f"{path} references forbidden private artifact text")
    return errors


def _live_action_marker_errors(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            errors.extend(_live_action_marker_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_live_action_marker_errors(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value in LIVE_ACTION_MARKERS:
        errors.append(f"{path} contains an executable live action marker")
    return errors


def _live_execution_claim_errors(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in LIVE_EXECUTION_KEYS and child is True:
                errors.append(f"{child_path} claims live network or DevHub execution")
            errors.extend(_live_execution_claim_errors(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_live_execution_claim_errors(child, f"{path}[{index}]"))
    return errors


def _production_ready_text_errors(value: Any, path: str, blockers_remain: bool) -> list[str]:
    if not blockers_remain:
        return []
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            errors.extend(_production_ready_text_errors(child, f"{path}.{key}", blockers_remain))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_production_ready_text_errors(child, f"{path}[{index}]", blockers_remain))
    elif _is_production_ready_text(value):
        errors.append(f"{path} must not use production-ready labels while blockers remain")
    return errors


def _capability_is_consequential(capability: Mapping[str, Any]) -> bool:
    text = " ".join(
        _text(capability.get(key)).lower()
        for key in ("capability_id", "summary", "capability", "action_id")
    )
    return any(fragment in text for fragment in CONSEQUENTIAL_CAPABILITY_FRAGMENTS)


def _is_production_ready_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower().replace("_", " ").replace("-", " ")
    return normalized in {label.replace("_", " ").replace("-", " ") for label in PRODUCTION_READY_LABELS}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, list):
        return tuple(value)
    return ()


def _text_sequence(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in _sequence(value) if isinstance(item, str) and item.strip())


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
