"""Fixture-first PP&D evidence freshness watchlist packets.

This module consumes already-captured schedule update, source refresh dry-run,
and requirement-to-guardrail traceability review packets. It performs no live
fetching, processor invocation, registry update, requirement update, or guardrail
mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


PACKET_TYPE = "fixture_first_ppd_evidence_freshness_watchlist_packet"
PACKET_MODE = "offline_review_only_no_active_mutation"

_REQUIRED_INPUTS = (
    "source_registry_schedule_update_candidate",
    "public_source_refresh_operator_dry_run_transcript",
    "requirement_guardrail_traceability_review_packet",
)

_REQUIRED_ATTESTATIONS = (
    "no_fetch",
    "no_processor",
    "no_registry_mutation",
    "no_guardrail_mutation",
    "no_requirement_mutation",
    "no_devhub_execution",
    "fixture_first_inputs_only",
)

_REQUIRED_OWNER_FIELDS = (
    "primary_reviewer",
    "source_registry_owner",
    "refresh_operator_owner",
    "traceability_owner",
    "watchlist_owner",
)

_RAW_OR_PRIVATE_RE = re.compile(
    r"(auth[_-]?state|cookie|credential|password|secret|token|\.har\b|trace\.zip|screenshot|raw[_-]?(?:body|crawl|archive|download)|warc://|/downloads?/|/home/[^\s]+/(?:Desktop|Documents|Downloads)|C:\\\\Users\\\\)",
    re.IGNORECASE,
)

_LIVE_EXECUTION_RE = re.compile(
    r"\b(?:live\s+)?(?:fetch|crawl|crawler|processor|devhub|browser|network)\s+(?:executed|performed|invoked|opened|queried|ran|used)\b|\b(?:executed|performed|invoked|opened|queried|ran|used)\s+(?:the\s+)?(?:live\s+)?(?:fetch|crawl|crawler|processor|devhub|browser|network)\b",
    re.IGNORECASE,
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\b(?:guarantee[sd]?|assure[sd]?|promise[sd]?|will\s+be)\b[^.\n]{0,80}\b(?:approved|approval|issued|accepted|legal|compliant|permitted)\b|\b(?:approval|permit|issuance|legal|permitting)\s+(?:is\s+)?guaranteed\b",
    re.IGNORECASE,
)

_MUTATION_KEY_RE = re.compile(
    r"active_.*mutation|mutate_.*active|apply_.*update|registry_mutation_allowed|guardrail_mutation_allowed|requirement_mutation_allowed|schedule_mutation_allowed",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EvidenceFreshnessWatchlistFinding:
    """A deterministic validation finding for watchlist packets."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class EvidenceFreshnessWatchlistValidationResult:
    """Validation result for a PP&D evidence freshness watchlist packet."""

    valid: bool
    findings: tuple[EvidenceFreshnessWatchlistFinding, ...]

    def codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


class EvidenceFreshnessWatchlistPacketError(ValueError):
    """Raised when a freshness watchlist packet fails validation."""

    def __init__(self, findings: Sequence[EvidenceFreshnessWatchlistFinding]) -> None:
        self.findings = tuple(findings)
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in self.findings)
        super().__init__("invalid PP&D evidence freshness watchlist packet: " + detail)


def build_evidence_freshness_watchlist_packet(
    source_registry_schedule_update_candidate: Mapping[str, Any],
    public_source_refresh_operator_dry_run_transcript: Mapping[str, Any],
    requirement_guardrail_traceability_review_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a deterministic offline freshness watchlist from fixture packets."""

    inputs = {
        "source_registry_schedule_update_candidate": _require_mapping(
            source_registry_schedule_update_candidate,
            "source registry schedule update candidate",
        ),
        "public_source_refresh_operator_dry_run_transcript": _require_mapping(
            public_source_refresh_operator_dry_run_transcript,
            "public source refresh operator dry-run transcript",
        ),
        "requirement_guardrail_traceability_review_packet": _require_mapping(
            requirement_guardrail_traceability_review_packet,
            "requirement-to-guardrail traceability review packet",
        ),
    }

    source_ids = _ordered_unique(
        _extract_strings_by_key(inputs.values(), {"source_id", "source_ids", "affected_source_ids", "sources"})
    )
    source_evidence_ids = _ordered_unique(
        _extract_strings_by_key(
            inputs.values(),
            {"source_evidence_ids", "evidence_ids", "citation_ids", "citations", "evidence_refs", "allowlist_evidence_refs", "robots_evidence_refs"},
        )
    )
    requirement_ids = _ordered_unique(
        _extract_strings_by_key(inputs.values(), {"requirement_id", "requirement_ids", "affected_requirement_ids", "impacted_requirement_ids"})
    )
    guardrail_ids = _ordered_unique(
        _extract_strings_by_key(inputs.values(), {"guardrail_id", "guardrail_ids", "affected_guardrail_ids", "impacted_guardrail_ids", "predicate_ids"})
    )

    triggers = _offline_review_triggers(
        source_registry_schedule_update_candidate,
        public_source_refresh_operator_dry_run_transcript,
        requirement_guardrail_traceability_review_packet,
        source_evidence_ids,
    )
    reviewer_owner_fields = _reviewer_owner_fields(
        source_registry_schedule_update_candidate,
        public_source_refresh_operator_dry_run_transcript,
        requirement_guardrail_traceability_review_packet,
    )

    watchlist_sources = [
        {
            "source_id": source_id,
            "source_evidence_ids": source_evidence_ids,
            "affected_requirement_ids": requirement_ids,
            "affected_guardrail_ids": guardrail_ids,
            "next_offline_review_triggers": triggers,
            "review_status": "pending_offline_reviewer_triage",
            "reviewer_owner_fields": reviewer_owner_fields,
        }
        for source_id in source_ids
    ]

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_mode": PACKET_MODE,
        "packet_id": "ppd-evidence-freshness-watchlist-" + _stable_hash(
            {
                "generated_at": generated_at,
                "source_ids": source_ids,
                "requirement_ids": requirement_ids,
                "guardrail_ids": guardrail_ids,
            }
        ),
        "generated_at": generated_at,
        "fixture_first": True,
        "consumed_packets": {
            name: {
                "packet_id": _packet_id(packet),
                "source_evidence_ids": _packet_evidence_ids(packet),
            }
            for name, packet in inputs.items()
        },
        "watchlist_sources": watchlist_sources,
        "affected_requirement_ids": requirement_ids,
        "affected_guardrail_ids": guardrail_ids,
        "next_offline_review_triggers": triggers,
        "reviewer_owner_fields": reviewer_owner_fields,
        "attestations": {
            "no_fetch": True,
            "no_processor": True,
            "no_registry_mutation": True,
            "no_guardrail_mutation": True,
            "no_requirement_mutation": True,
            "no_devhub_execution": True,
            "fixture_first_inputs_only": True,
            "attestation_basis": "committed fixture packets only",
        },
        "active_mutation_effects": {
            "registry_mutated": False,
            "source_schedule_mutated": False,
            "requirements_mutated": False,
            "guardrails_mutated": False,
            "processor_invoked": False,
            "live_fetch_performed": False,
            "devhub_executed": False,
        },
    }
    assert_valid_evidence_freshness_watchlist_packet(packet)
    return packet


def validate_evidence_freshness_watchlist_packet(packet: Mapping[str, Any]) -> EvidenceFreshnessWatchlistValidationResult:
    """Validate a fixture-first PP&D evidence freshness watchlist packet."""

    findings: list[EvidenceFreshnessWatchlistFinding] = []
    if not isinstance(packet, Mapping):
        return EvidenceFreshnessWatchlistValidationResult(
            False,
            (EvidenceFreshnessWatchlistFinding("invalid_packet", "$", "Packet must be an object."),),
        )

    if packet.get("packet_type") != PACKET_TYPE:
        findings.append(EvidenceFreshnessWatchlistFinding("invalid_packet_type", "$.packet_type", "Unexpected packet type."))
    if packet.get("packet_mode") != PACKET_MODE:
        findings.append(EvidenceFreshnessWatchlistFinding("invalid_packet_mode", "$.packet_mode", "Packet must remain offline review only."))
    if packet.get("fixture_first") is not True:
        findings.append(EvidenceFreshnessWatchlistFinding("not_fixture_first", "$.fixture_first", "Packet must declare fixture_first=true."))

    _validate_consumed_packets(packet.get("consumed_packets"), findings)
    _validate_watchlist_sources(packet.get("watchlist_sources"), findings)
    _validate_top_level_impacts(packet, findings)
    _validate_reviewer_owners(packet.get("reviewer_owner_fields"), findings)
    _validate_attestations(packet.get("attestations"), packet.get("active_mutation_effects"), findings)
    _scan_for_unsafe_content(packet, "$", findings)
    return EvidenceFreshnessWatchlistValidationResult(not findings, tuple(findings))


def assert_valid_evidence_freshness_watchlist_packet(packet: Mapping[str, Any]) -> None:
    """Raise when a freshness watchlist packet is incomplete or unsafe."""

    result = validate_evidence_freshness_watchlist_packet(packet)
    if not result.valid:
        raise EvidenceFreshnessWatchlistPacketError(result.findings)


def _validate_consumed_packets(value: Any, findings: list[EvidenceFreshnessWatchlistFinding]) -> None:
    if not isinstance(value, Mapping):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_consumed_packets", "$.consumed_packets", "Consumed packet references are required."))
        return
    for name in _REQUIRED_INPUTS:
        row = value.get(name)
        if not isinstance(row, Mapping):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_consumed_packet", f"$.consumed_packets.{name}", "Required source packet was not consumed."))
            continue
        if not _text(row.get("packet_id")):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_consumed_packet_id", f"$.consumed_packets.{name}.packet_id", "Consumed packet must include packet_id."))
        if not _strings(row.get("source_evidence_ids")):
            findings.append(EvidenceFreshnessWatchlistFinding("uncited_consumed_packet", f"$.consumed_packets.{name}.source_evidence_ids", "Consumed packet must cite source evidence."))


def _validate_watchlist_sources(value: Any, findings: list[EvidenceFreshnessWatchlistFinding]) -> None:
    if not isinstance(value, list) or not value:
        findings.append(EvidenceFreshnessWatchlistFinding("missing_watchlist_sources", "$.watchlist_sources", "At least one watchlist source is required."))
        return
    for index, row in enumerate(value):
        path = f"$.watchlist_sources[{index}]"
        if not isinstance(row, Mapping):
            findings.append(EvidenceFreshnessWatchlistFinding("invalid_watchlist_source", path, "Watchlist source must be an object."))
            continue
        if not _text(row.get("source_id")):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_watchlist_source_id", f"{path}.source_id", "Watchlist source must include source_id."))
        if not _strings(row.get("source_evidence_ids")):
            findings.append(EvidenceFreshnessWatchlistFinding("uncited_watchlist_source", f"{path}.source_evidence_ids", "Watchlist source must cite source evidence."))
        if not _strings(row.get("affected_requirement_ids")):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_affected_requirement_ids", f"{path}.affected_requirement_ids", "Affected requirement IDs are required."))
        if not _strings(row.get("affected_guardrail_ids")):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_affected_guardrail_ids", f"{path}.affected_guardrail_ids", "Affected guardrail IDs are required."))
        if not _valid_trigger_list(row.get("next_offline_review_triggers")):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_next_offline_review_triggers", f"{path}.next_offline_review_triggers", "Next offline review triggers are required."))
        _validate_reviewer_owners(row.get("reviewer_owner_fields"), findings, path=f"{path}.reviewer_owner_fields")


def _validate_top_level_impacts(packet: Mapping[str, Any], findings: list[EvidenceFreshnessWatchlistFinding]) -> None:
    if not _strings(packet.get("affected_requirement_ids")):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_affected_requirement_ids", "$.affected_requirement_ids", "Top-level affected requirement IDs are required."))
    if not _strings(packet.get("affected_guardrail_ids")):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_affected_guardrail_ids", "$.affected_guardrail_ids", "Top-level affected guardrail IDs are required."))
    if not _valid_trigger_list(packet.get("next_offline_review_triggers")):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_next_offline_review_triggers", "$.next_offline_review_triggers", "Top-level offline triggers are required."))


def _validate_reviewer_owners(value: Any, findings: list[EvidenceFreshnessWatchlistFinding], *, path: str = "$.reviewer_owner_fields") -> None:
    if not isinstance(value, Mapping):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_reviewer_owner_fields", path, "Reviewer-owner fields are required."))
        return
    for key in _REQUIRED_OWNER_FIELDS:
        if not _text(value.get(key)):
            findings.append(EvidenceFreshnessWatchlistFinding("missing_reviewer_owner", f"{path}.{key}", "Reviewer-owner value is required."))


def _validate_attestations(value: Any, effects: Any, findings: list[EvidenceFreshnessWatchlistFinding]) -> None:
    if not isinstance(value, Mapping):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_attestations", "$.attestations", "Attestations are required."))
        return
    for key in _REQUIRED_ATTESTATIONS:
        if value.get(key) is not True:
            findings.append(EvidenceFreshnessWatchlistFinding("missing_no_mutation_attestation", f"$.attestations.{key}", "Required safety attestation must be true."))
    if not isinstance(effects, Mapping):
        findings.append(EvidenceFreshnessWatchlistFinding("missing_active_mutation_effects", "$.active_mutation_effects", "Active mutation effects map is required."))
        return
    for key, item in effects.items():
        if item is not False:
            findings.append(EvidenceFreshnessWatchlistFinding("active_mutation_effect_enabled", f"$.active_mutation_effects.{key}", "Active mutation effects must remain false."))


def _valid_trigger_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for item in value:
        if not isinstance(item, Mapping):
            return False
        if not _text(item.get("trigger_id")) or not _text(item.get("review_action")):
            return False
        if not _strings(item.get("source_evidence_ids")):
            return False
    return True


def _offline_review_triggers(
    schedule_packet: Mapping[str, Any],
    dry_run_packet: Mapping[str, Any],
    traceability_packet: Mapping[str, Any],
    fallback_evidence_ids: Sequence[str],
) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []

    for index, adjustment in enumerate(_list(schedule_packet.get("source_adjustments") or schedule_packet.get("schedule_adjustments") or schedule_packet.get("update_candidates"))):
        if isinstance(adjustment, Mapping):
            source_ids = _ordered_unique(_extract_strings_by_key((adjustment,), {"source_id", "source_ids", "affected_source_ids"}))
            evidence_ids = _packet_evidence_ids(adjustment) or list(fallback_evidence_ids)
            triggers.append(
                {
                    "trigger_id": f"schedule-candidate-{index + 1}",
                    "source_ids": source_ids,
                    "review_action": "Review proposed source registry schedule cadence before any registry update is applied.",
                    "source_evidence_ids": evidence_ids,
                }
            )

    for index, checkpoint in enumerate(_list(dry_run_packet.get("abort_or_rollback_checkpoints"))):
        if isinstance(checkpoint, Mapping):
            evidence_ids = _packet_evidence_ids(dry_run_packet) or list(fallback_evidence_ids)
            triggers.append(
                {
                    "trigger_id": f"operator-dry-run-checkpoint-{index + 1}",
                    "checkpoint": _text(checkpoint.get("checkpoint")) or f"checkpoint-{index + 1}",
                    "review_action": _text(checkpoint.get("operator_action")) or "Pause for offline reviewer before any live source interaction.",
                    "source_evidence_ids": evidence_ids,
                }
            )

    for index, action in enumerate(_list(traceability_packet.get("blocked_action_carryovers"))):
        if isinstance(action, Mapping):
            evidence_ids = _packet_evidence_ids(action) or _packet_evidence_ids(traceability_packet) or list(fallback_evidence_ids)
            triggers.append(
                {
                    "trigger_id": f"traceability-blocked-action-{index + 1}",
                    "action_id": _text(action.get("action_id")) or f"blocked-action-{index + 1}",
                    "review_action": "Confirm freshness impact before changing requirement or guardrail treatment for this blocked action.",
                    "source_evidence_ids": evidence_ids,
                }
            )

    return triggers


def _reviewer_owner_fields(schedule_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], traceability_packet: Mapping[str, Any]) -> dict[str, str]:
    schedule_owners = schedule_packet.get("reviewer_owners") or schedule_packet.get("reviewer_owner_fields") or {}
    traceability_owners = traceability_packet.get("reviewer_owner_fields") or {}
    return {
        "primary_reviewer": _owner_value(schedule_owners, "primary_reviewer") or _owner_value(traceability_owners, "traceability_review_owner") or "ppd-evidence-freshness-reviewer",
        "source_registry_owner": _owner_value(schedule_owners, "review_queue") or _owner_value(schedule_owners, "primary_reviewer") or "ppd-source-registry-review",
        "refresh_operator_owner": _text(dry_run_packet.get("owner")) or "ppd-source-refresh-owner",
        "traceability_owner": _owner_value(traceability_owners, "traceability_review_owner") or "ppd-traceability-reviewer",
        "watchlist_owner": "ppd-evidence-freshness-watchlist-owner",
    }


def _owner_value(mapping: Any, key: str) -> str:
    return _text(mapping.get(key)) if isinstance(mapping, Mapping) else ""


def _packet_id(packet: Mapping[str, Any]) -> str:
    explicit = _text(packet.get("packet_id")) or _text(packet.get("id"))
    if explicit:
        return explicit
    packet_type = _text(packet.get("packet_type")) or "packet"
    return packet_type + "-" + _stable_hash(packet)


def _packet_evidence_ids(packet: Mapping[str, Any]) -> list[str]:
    return _ordered_unique(
        _extract_strings_by_key(
            (packet,),
            {"source_evidence_ids", "evidence_ids", "citation_ids", "citations", "source_ids", "affected_source_ids", "allowlist_evidence_refs", "robots_evidence_refs"},
        )
    )


def _require_mapping(value: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _extract_strings_by_key(values: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(values, Mapping):
        for key, value in values.items():
            if key in keys:
                found.extend(_strings(value))
            found.extend(_extract_strings_by_key(value, keys))
    elif isinstance(values, list):
        for value in values:
            found.extend(_extract_strings_by_key(value, keys))
    elif isinstance(values, tuple):
        for value in values:
            found.extend(_extract_strings_by_key(value, keys))
    return found


def _scan_for_unsafe_content(value: Any, path: str, findings: list[EvidenceFreshnessWatchlistFinding]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and _MUTATION_KEY_RE.search(key) and item is True:
                findings.append(EvidenceFreshnessWatchlistFinding("active_mutation_flag_present", child_path, "Active mutation flags must not be enabled."))
            _scan_for_unsafe_content(item, child_path, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_for_unsafe_content(item, f"{path}[{index}]", findings)
    elif isinstance(value, str):
        if _RAW_OR_PRIVATE_RE.search(value):
            findings.append(EvidenceFreshnessWatchlistFinding("raw_or_private_artifact_reference", path, "Raw, private, credential, browser, or download artifact references are not allowed."))
        if _LIVE_EXECUTION_RE.search(value):
            findings.append(EvidenceFreshnessWatchlistFinding("live_execution_claim", path, "Live fetch, processor, DevHub, or browser execution claims are not allowed."))
        if _OUTCOME_GUARANTEE_RE.search(value):
            findings.append(EvidenceFreshnessWatchlistFinding("legal_or_permitting_outcome_guarantee", path, "Legal or permitting outcome guarantees are not allowed."))


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Mapping):
        result: list[str] = []
        for key in ("source_id", "id", "ref", "url", "requirement_id", "guardrail_id"):
            result.extend(_strings(value.get(key)))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_strings(item))
        return result
    if isinstance(value, tuple):
        result = []
        for item in value:
            result.extend(_strings(item))
        return result
    return []


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ordered_unique(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in result:
            result.append(text)
    return result


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
