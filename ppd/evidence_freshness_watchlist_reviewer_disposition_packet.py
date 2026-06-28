"""Fixture-first PP&D evidence freshness watchlist reviewer dispositions.

This module consumes already-built fixture packets: the PP&D evidence freshness
watchlist packet, the release acceptance review packet, and the public source
refresh operator dry-run transcript. It produces reviewer-owned disposition
metadata only. It performs no URL fetch, processor invocation, registry update,
guardrail update, or release-state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from ppd.agent_readiness.release_acceptance_review_packet import assert_valid_release_acceptance_review_packet
from ppd.evidence_freshness_watchlist_packet import assert_valid_evidence_freshness_watchlist_packet
from ppd.public_source_refresh_operator_dry_run import assert_valid_public_source_refresh_operator_dry_run_transcript


PACKET_TYPE = "fixture_first_ppd_evidence_freshness_watchlist_reviewer_disposition_packet"
PACKET_MODE = "offline_reviewer_disposition_only_no_active_mutation"

_REQUIRED_INPUTS = (
    "evidence_freshness_watchlist_packet",
    "release_acceptance_review_packet",
    "public_source_refresh_operator_dry_run_transcript",
)

_REQUIRED_ATTESTATIONS = (
    "fixture_first_inputs_only",
    "no_fetch",
    "no_processor",
    "no_registry_mutation",
    "no_guardrail_mutation",
    "no_release_mutation",
)

_REQUIRED_OWNER_FIELDS = (
    "primary_reviewer",
    "watchlist_owner",
    "release_acceptance_owner",
    "refresh_operator_owner",
    "disposition_owner",
)


@dataclass(frozen=True)
class ReviewerDispositionValidationResult:
    """Deterministic validation result for reviewer disposition packets."""

    valid: bool
    problems: tuple[str, ...]

    def codes(self) -> tuple[str, ...]:
        return tuple(problem.split(":", 1)[0] for problem in self.problems)


class ReviewerDispositionPacketError(ValueError):
    """Raised when a reviewer disposition packet is incomplete or unsafe."""


def build_evidence_freshness_watchlist_reviewer_disposition_packet(
    evidence_freshness_watchlist_packet: Mapping[str, Any],
    release_acceptance_review_packet: Mapping[str, Any],
    public_source_refresh_operator_dry_run_transcript: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build cited approve/defer/escalate decisions from fixture packets."""

    watchlist = dict(evidence_freshness_watchlist_packet)
    release = dict(release_acceptance_review_packet)
    dry_run = dict(public_source_refresh_operator_dry_run_transcript)

    assert_valid_evidence_freshness_watchlist_packet(watchlist)
    assert_valid_release_acceptance_review_packet(release)
    assert_valid_public_source_refresh_operator_dry_run_transcript(dry_run)

    validation_commands = _offline_validation_commands(release)
    reviewer_owner_fields = _reviewer_owner_fields(watchlist, release, dry_run)
    decisions = [
        _decision_for_watchlist_item(row, release, dry_run, validation_commands, reviewer_owner_fields)
        for row in _mapping_sequence(watchlist.get("watchlist_sources"))
    ]

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_mode": PACKET_MODE,
        "packet_id": "ppd-evidence-freshness-reviewer-disposition-" + _stable_hash(
            {
                "generated_at": generated_at,
                "source_ids": [decision["source_id"] for decision in decisions],
                "decisions": [decision["decision"] for decision in decisions],
            }
        ),
        "generated_at": generated_at,
        "fixture_first": True,
        "consumed_packets": {
            "evidence_freshness_watchlist_packet": _consumed_packet(watchlist, "evidence_freshness_watchlist_packet"),
            "release_acceptance_review_packet": _consumed_packet(release, "release_acceptance_review_packet"),
            "public_source_refresh_operator_dry_run_transcript": _consumed_packet(dry_run, "public_source_refresh_operator_dry_run_transcript"),
        },
        "reviewer_owner_fields": reviewer_owner_fields,
        "watchlist_item_dispositions": decisions,
        "next_offline_validation_commands": validation_commands,
        "allowed_reviewer_dispositions": ["approve", "defer", "escalate"],
        "attestations": {
            "fixture_first_inputs_only": True,
            "no_fetch": True,
            "no_processor": True,
            "no_registry_mutation": True,
            "no_guardrail_mutation": True,
            "no_release_mutation": True,
            "attestation_basis": "reviewer disposition packet assembled from committed fixture packet metadata only",
        },
        "active_mutation_effects": {
            "fetched_urls": False,
            "processor_invoked": False,
            "registry_mutated": False,
            "guardrails_mutated": False,
            "release_state_mutated": False,
        },
    }
    assert_valid_evidence_freshness_watchlist_reviewer_disposition_packet(packet)
    return packet


def validate_evidence_freshness_watchlist_reviewer_disposition_packet(packet: Mapping[str, Any]) -> ReviewerDispositionValidationResult:
    """Validate the reviewer disposition packet shape without side effects."""

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("invalid_packet_type: unexpected packet_type")
    if packet.get("packet_mode") != PACKET_MODE:
        problems.append("invalid_packet_mode: packet must remain offline disposition only")
    if packet.get("fixture_first") is not True:
        problems.append("not_fixture_first: fixture_first must be true")

    consumed = _mapping(packet.get("consumed_packets"))
    for name in _REQUIRED_INPUTS:
        item = _mapping(consumed.get(name))
        if not _text(item.get("packet_id")):
            problems.append(f"missing_consumed_packet: consumed_packets.{name}.packet_id is required")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"uncited_consumed_packet: consumed_packets.{name}.source_evidence_ids is required")

    owners = _mapping(packet.get("reviewer_owner_fields"))
    for key in _REQUIRED_OWNER_FIELDS:
        if not _text(owners.get(key)):
            problems.append(f"missing_reviewer_owner: reviewer_owner_fields.{key} is required")

    decisions = _mapping_sequence(packet.get("watchlist_item_dispositions"))
    if not decisions:
        problems.append("missing_dispositions: watchlist_item_dispositions must be non-empty")
    for index, decision in enumerate(decisions):
        path = f"watchlist_item_dispositions[{index}]"
        if decision.get("decision") not in {"approve", "defer", "escalate"}:
            problems.append(f"invalid_decision: {path}.decision must be approve, defer, or escalate")
        if not _text(decision.get("source_id")):
            problems.append(f"missing_source_id: {path}.source_id is required")
        if not _string_list(decision.get("source_evidence_ids")):
            problems.append(f"uncited_decision: {path}.source_evidence_ids is required")
        if not _mapping(decision.get("reviewer_owner_fields")):
            problems.append(f"missing_decision_owner_fields: {path}.reviewer_owner_fields is required")
        if not _command_sequence(decision.get("next_offline_validation_commands")):
            problems.append(f"missing_offline_validation_commands: {path}.next_offline_validation_commands is required")

    if not _command_sequence(packet.get("next_offline_validation_commands")):
        problems.append("missing_offline_validation_commands: top-level next_offline_validation_commands is required")

    attestations = _mapping(packet.get("attestations"))
    for key in _REQUIRED_ATTESTATIONS:
        if attestations.get(key) is not True:
            problems.append(f"missing_attestation: attestations.{key} must be true")

    effects = _mapping(packet.get("active_mutation_effects"))
    for key, value in effects.items():
        if value is not False:
            problems.append(f"active_mutation_effect: active_mutation_effects.{key} must be false")

    return ReviewerDispositionValidationResult(valid=not problems, problems=tuple(dict.fromkeys(problems)))


def assert_valid_evidence_freshness_watchlist_reviewer_disposition_packet(packet: Mapping[str, Any]) -> None:
    result = validate_evidence_freshness_watchlist_reviewer_disposition_packet(packet)
    if not result.valid:
        raise ReviewerDispositionPacketError("invalid reviewer disposition packet: " + "; ".join(result.problems))


def _decision_for_watchlist_item(
    row: Mapping[str, Any],
    release: Mapping[str, Any],
    dry_run: Mapping[str, Any],
    validation_commands: list[list[str]],
    reviewer_owner_fields: Mapping[str, str],
) -> dict[str, Any]:
    source_id = _text(row.get("source_id"))
    dry_run_sources = set(_strings(dry_run.get("sources")))
    blocker_ids = _matching_release_blocker_ids(source_id, release)
    affected_requirement_ids = _strings(row.get("affected_requirement_ids"))
    affected_guardrail_ids = _strings(row.get("affected_guardrail_ids"))

    if source_id not in dry_run_sources:
        decision = "escalate"
        rationale = "Source is absent from the operator dry-run transcript source list."
    elif _has_consequential_devhub_impact(source_id, affected_requirement_ids, affected_guardrail_ids):
        decision = "escalate"
        rationale = "Watchlist item affects DevHub upload, submission, or exact-confirmation guardrails."
    elif blocker_ids:
        decision = "defer"
        rationale = "Release acceptance blocker disposition remains open for this watchlist source."
    else:
        decision = "approve"
        rationale = "Fixture evidence supports offline freshness review with no matched release blocker."

    evidence_ids = _ordered_unique(
        _strings(row.get("source_evidence_ids"))
        + _strings(dry_run.get("allowlist_evidence_refs"))
        + _strings(dry_run.get("robots_evidence_refs"))
        + _packet_evidence_ids(release, "release_acceptance_review_packet")
    )

    return {
        "disposition_id": "watchlist-disposition-" + _slug(source_id),
        "source_id": source_id,
        "decision": decision,
        "rationale": rationale,
        "matched_release_blocker_ids": blocker_ids,
        "affected_requirement_ids": affected_requirement_ids,
        "affected_guardrail_ids": affected_guardrail_ids,
        "source_evidence_ids": evidence_ids,
        "next_offline_validation_commands": validation_commands,
        "reviewer_owner_fields": dict(reviewer_owner_fields),
    }


def _has_consequential_devhub_impact(source_id: str, requirement_ids: Sequence[str], guardrail_ids: Sequence[str]) -> bool:
    haystack = " ".join([source_id, *requirement_ids, *guardrail_ids]).lower()
    return any(token in haystack for token in ("devhub", "upload", "submit", "exact-confirmation", "payment"))


def _matching_release_blocker_ids(source_id: str, release: Mapping[str, Any]) -> list[str]:
    source_tokens = {token for token in _slug(source_id).split("-") if token and token not in {"ppd", "online"}}
    matches: list[str] = []
    for blocker in _mapping_sequence(release.get("open_blocker_dispositions")):
        text = _slug(" ".join(str(value) for value in blocker.values()))
        if any(token in text for token in source_tokens):
            matches.append(_text(blocker.get("blocker_id")) or "release-blocker")
    return _ordered_unique(matches)


def _offline_validation_commands(release: Mapping[str, Any]) -> list[list[str]]:
    commands: list[list[str]] = []
    for item in _mapping_sequence(release.get("validation_rerun_expectations")):
        command = item.get("command")
        if isinstance(command, list) and all(isinstance(part, str) and part for part in command):
            commands.append(list(command))
    commands.append(["python3", "-m", "unittest", "ppd.tests.test_evidence_freshness_watchlist_reviewer_disposition_packet"])
    return _unique_commands(commands)


def _reviewer_owner_fields(watchlist: Mapping[str, Any], release: Mapping[str, Any], dry_run: Mapping[str, Any]) -> dict[str, str]:
    watchlist_owners = _mapping(watchlist.get("reviewer_owner_fields"))
    release_slots = _mapping_sequence(release.get("reviewer_owner_signoff_slots"))
    release_owner = _text(release_slots[0].get("owner")) if release_slots else "ppd-release-acceptance-owner"
    return {
        "primary_reviewer": _text(watchlist_owners.get("primary_reviewer")) or "ppd-evidence-freshness-reviewer",
        "watchlist_owner": _text(watchlist_owners.get("watchlist_owner")) or "ppd-evidence-freshness-watchlist-owner",
        "release_acceptance_owner": release_owner,
        "refresh_operator_owner": _text(dry_run.get("owner")) or "ppd-source-refresh-owner",
        "disposition_owner": "ppd-evidence-freshness-disposition-owner",
    }


def _consumed_packet(packet: Mapping[str, Any], fallback_name: str) -> dict[str, Any]:
    return {
        "packet_id": _packet_id(packet, fallback_name),
        "packet_type": _text(packet.get("packet_type")) or fallback_name,
        "source_evidence_ids": _packet_evidence_ids(packet, fallback_name),
    }


def _packet_id(packet: Mapping[str, Any], fallback_name: str) -> str:
    return _text(packet.get("packet_id")) or _text(packet.get("id")) or fallback_name + "-" + _stable_hash(packet)


def _packet_evidence_ids(packet: Mapping[str, Any], fallback_name: str) -> list[str]:
    evidence = _ordered_unique(
        _extract_strings_by_key(
            packet,
            {"source_evidence_ids", "evidence_ids", "citation_ids", "citations", "allowlist_evidence_refs", "robots_evidence_refs"},
        )
    )
    if evidence:
        return evidence
    return [fallback_name + "#packet"]


def _extract_strings_by_key(value: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in keys:
                found.extend(_strings(item))
            found.extend(_extract_strings_by_key(item, keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(_extract_strings_by_key(item, keys))
    return found


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


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
    return []


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _command_sequence(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(command, list) and bool(command) and all(isinstance(part, str) and part for part in command)
        for command in value
    )


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ordered_unique(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in result:
            result.append(text)
    return result


def _unique_commands(commands: Sequence[Sequence[str]]) -> list[list[str]]:
    result: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for command in commands:
        key = tuple(command)
        if key not in seen:
            seen.add(key)
            result.append(list(command))
    return result


def _slug(value: str) -> str:
    return "-".join(part for part in "".join(char.lower() if char.isalnum() else "-" for char in value).split("-") if part)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
