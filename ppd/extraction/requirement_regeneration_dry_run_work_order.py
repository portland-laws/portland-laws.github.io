"""Fixture-first requirement regeneration dry-run work orders.

This module consumes already-produced public source change impact triage and
requirement regeneration promotion decision packets. It emits cited offline
inputs, expected requirement IDs, reviewer checkpoints, stale-source handling,
rollback references, and no-promotion attestations for a later human-owned
regeneration review.

It does not fetch URLs, invoke processors, regenerate active requirements, or
promote any candidate artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


_REQUIRED_PREREQUISITE_ROLES = {
    "public_source_change_impact_triage_packet",
    "requirement_regeneration_promotion_decision_packet",
}

_FORBIDDEN_TRUE_KEYS = {
    "active_requirement_mutated",
    "active_requirement_regeneration_allowed",
    "active_requirements_mutated",
    "active_requirements_regenerated",
    "apply_to_active",
    "calls_llm",
    "crawl_attempted",
    "execute_live_devhub",
    "fetch_attempted",
    "fetched_live",
    "invoke_processors",
    "launch_devhub",
    "live_crawl_performed",
    "live_fetch_performed",
    "live_network_performed",
    "mutates_active_requirements",
    "network_action_performed",
    "network_actions_performed",
    "open_browser",
    "processor_invocation_allowed",
    "processor_invoked",
    "processors_invoked",
    "promote_to_active",
    "promotion_allowed",
    "regenerate_active_requirements",
    "regeneration_allowed_before_acknowledgement",
    "urls_fetched",
    "uses_authenticated_session",
}

_FORBIDDEN_VALUE_KEY_PARTS = {
    "archive_artifact",
    "archive_ref",
    "auth_state",
    "cookie",
    "credential",
    "download_path",
    "download_ref",
    "download_url",
    "downloaded_document",
    "har_path",
    "local_path",
    "password",
    "payment",
    "private_case",
    "raw_archive",
    "raw_body",
    "raw_crawl",
    "raw_download",
    "raw_html",
    "raw_pdf",
    "screenshot",
    "session_state",
    "token",
    "trace_path",
    "warc",
}

_PRODUCTION_READY_LABELS = {
    "approved-for-production",
    "approved_for_production",
    "production ready",
    "production-ready",
    "production_ready",
    "ready for production",
    "ready-for-production",
    "ready_for_production",
    "release ready",
    "release-ready",
    "release_ready",
}

_STALE_STATUSES = {"changed", "expired", "needs_review", "outdated", "stale", "unknown"}


@dataclass(frozen=True)
class RequirementRegenerationDryRunFinding:
    code: str
    path: str
    message: str


class RequirementRegenerationDryRunWorkOrderError(ValueError):
    """Raised when a dry-run work order input or output is unsafe."""

    def __init__(self, findings: Sequence[RequirementRegenerationDryRunFinding]) -> None:
        self.findings = tuple(findings)
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in self.findings)
        super().__init__(detail)


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def build_requirement_regeneration_dry_run_work_order(packet_input: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic offline work order from prerequisite packets."""

    if not isinstance(packet_input, Mapping):
        raise RequirementRegenerationDryRunWorkOrderError([
            RequirementRegenerationDryRunFinding("invalid_input", "$", "input must be an object")
        ])

    input_findings = _safety_findings(packet_input)
    if input_findings:
        raise RequirementRegenerationDryRunWorkOrderError(input_findings)

    triage = _mapping(packet_input.get("public_source_change_impact_triage_packet"))
    promotion = _mapping(packet_input.get("requirement_regeneration_promotion_decision_packet"))
    if not triage or not promotion:
        raise RequirementRegenerationDryRunWorkOrderError([
            RequirementRegenerationDryRunFinding(
                "missing_prerequisite_packet",
                "$",
                "input must include public_source_change_impact_triage_packet and requirement_regeneration_promotion_decision_packet",
            )
        ])

    impact_records = list(_mapping_sequence(triage.get("impact_records")))
    promotion_decisions = list(_mapping_sequence(promotion.get("reviewer_selected_decisions")))
    rollback_notes = list(_mapping_sequence(promotion.get("rollback_notes")))

    offline_inputs = _offline_regeneration_inputs(impact_records)
    expected_requirement_ids = sorted({item["requirement_id"] for item in offline_inputs})
    known_source_ids = sorted({_text(record.get("source_id")) for record in impact_records if _text(record.get("source_id"))})
    known_requirement_ids = expected_requirement_ids[:]
    stale_handling = _stale_source_handling(impact_records)
    reviewer_checkpoints = _reviewer_checkpoints(offline_inputs, promotion_decisions, stale_handling)
    rollback_references = _rollback_references(rollback_notes)
    source_packets = {
        "public_source_change_impact_triage_packet_id": str(triage.get("packet_id") or "public-source-change-impact-triage-fixture"),
        "requirement_regeneration_promotion_decision_packet_id": str(promotion.get("packet_id") or "requirement-regeneration-promotion-decision-fixture"),
    }

    work_order = {
        "packet_type": "requirement_regeneration_dry_run_work_order",
        "packet_id": str(packet_input.get("packet_id") or "requirement-regeneration-dry-run-work-order-" + _stable_hash(packet_input)),
        "mode": "fixture_first_offline_dry_run",
        "source_packets": source_packets,
        "prerequisite_links": [
            {
                "packet_role": "public_source_change_impact_triage_packet",
                "packet_id": source_packets["public_source_change_impact_triage_packet_id"],
                "citation_path": "$.public_source_change_impact_triage_packet",
                "review_required_before_regeneration": True,
            },
            {
                "packet_role": "requirement_regeneration_promotion_decision_packet",
                "packet_id": source_packets["requirement_regeneration_promotion_decision_packet_id"],
                "citation_path": "$.requirement_regeneration_promotion_decision_packet",
                "review_required_before_regeneration": True,
            },
        ],
        "known_source_ids": known_source_ids,
        "known_requirement_ids": known_requirement_ids,
        "offline_regeneration_inputs": offline_inputs,
        "expected_requirement_ids": expected_requirement_ids,
        "reviewer_checkpoints": reviewer_checkpoints,
        "stale_source_handling": stale_handling,
        "rollback_references": rollback_references,
        "no_promotion_attestations": {
            "active_requirements_regenerated": False,
            "active_requirements_mutated": False,
            "promotion_allowed": False,
            "processors_invoked": False,
            "urls_fetched": False,
            "devhub_launched": False,
            "requires_separate_human_promotion_packet": True,
        },
        "execution_boundaries": {
            "fixture_only": True,
            "network_actions_performed": False,
            "processor_invoked": False,
            "regenerate_active_requirements": False,
            "mutates_active_requirements": False,
            "promotion_allowed": False,
        },
    }

    findings = validate_requirement_regeneration_dry_run_work_order(work_order)
    if findings:
        raise RequirementRegenerationDryRunWorkOrderError(findings)
    return work_order


def build_requirement_regeneration_dry_run_work_order_from_file(path: Path) -> dict[str, Any]:
    return build_requirement_regeneration_dry_run_work_order(load_json_object(path))


def validate_requirement_regeneration_dry_run_work_order(packet: Mapping[str, Any]) -> list[RequirementRegenerationDryRunFinding]:
    """Return deterministic validation findings without performing side effects."""

    if not isinstance(packet, Mapping):
        return [RequirementRegenerationDryRunFinding("invalid_packet", "$", "packet must be an object")]

    findings = _safety_findings(packet)
    if packet.get("packet_type") != "requirement_regeneration_dry_run_work_order":
        findings.append(RequirementRegenerationDryRunFinding("invalid_packet_type", "$.packet_type", "unexpected packet type"))
    if packet.get("mode") != "fixture_first_offline_dry_run":
        findings.append(RequirementRegenerationDryRunFinding("not_fixture_first", "$.mode", "work order must be fixture-first offline dry-run"))

    _validate_prerequisite_links(packet, findings)

    known_source_ids = _strings(packet.get("known_source_ids"))
    known_requirement_ids = _strings(packet.get("known_requirement_ids"))
    inputs = list(_mapping_sequence(packet.get("offline_regeneration_inputs")))
    if not inputs:
        findings.append(RequirementRegenerationDryRunFinding("missing_offline_regeneration_inputs", "$.offline_regeneration_inputs", "offline inputs are required"))

    cited_requirement_ids = set()
    for index, item in enumerate(inputs):
        path = f"$.offline_regeneration_inputs[{index}]"
        requirement_id = _text(item.get("requirement_id"))
        source_id = _text(item.get("source_id"))
        cited_requirement_ids.add(requirement_id)
        if not requirement_id:
            findings.append(RequirementRegenerationDryRunFinding("missing_requirement_id", path + ".requirement_id", "requirement ID is required"))
        elif known_requirement_ids and requirement_id not in known_requirement_ids:
            findings.append(RequirementRegenerationDryRunFinding("unknown_requirement_id", path + ".requirement_id", "requirement ID must be declared by the work order prerequisites"))
        if not source_id:
            findings.append(RequirementRegenerationDryRunFinding("missing_source_id", path + ".source_id", "source ID is required"))
        elif known_source_ids and source_id not in known_source_ids:
            findings.append(RequirementRegenerationDryRunFinding("unknown_source_id", path + ".source_id", "source ID must be declared by the work order prerequisites"))
        if not _strings(item.get("citation_ids")):
            findings.append(RequirementRegenerationDryRunFinding("uncited_regeneration_input", path + ".citation_ids", "offline input must cite source evidence"))
        if item.get("offline_only") is not True:
            findings.append(RequirementRegenerationDryRunFinding("input_not_offline_only", path + ".offline_only", "input must be offline only"))
        if item.get("processor_invocation_allowed") is not False:
            findings.append(RequirementRegenerationDryRunFinding("processor_invocation_not_blocked", path + ".processor_invocation_allowed", "processor invocation must be blocked in dry-run inputs"))
        if item.get("active_requirement_regeneration_allowed") is not False:
            findings.append(RequirementRegenerationDryRunFinding("active_requirement_regeneration_not_blocked", path + ".active_requirement_regeneration_allowed", "active requirement regeneration must be blocked"))

    expected_ids = set(_strings(packet.get("expected_requirement_ids")))
    if not expected_ids:
        findings.append(RequirementRegenerationDryRunFinding("missing_expected_requirement_ids", "$.expected_requirement_ids", "expected requirement IDs are required"))
    if expected_ids != {item for item in cited_requirement_ids if item}:
        findings.append(RequirementRegenerationDryRunFinding("expected_requirement_id_mismatch", "$.expected_requirement_ids", "expected IDs must match cited offline inputs"))
    for requirement_id in expected_ids:
        if known_requirement_ids and requirement_id not in known_requirement_ids:
            findings.append(RequirementRegenerationDryRunFinding("unknown_requirement_id", "$.expected_requirement_ids", "expected requirement IDs must be declared by the work order prerequisites"))

    checkpoints = list(_mapping_sequence(packet.get("reviewer_checkpoints")))
    if not checkpoints:
        findings.append(RequirementRegenerationDryRunFinding("missing_reviewer_checkpoints", "$.reviewer_checkpoints", "reviewer checkpoints are required"))
    for index, checkpoint in enumerate(checkpoints):
        path = f"$.reviewer_checkpoints[{index}]"
        if not _text(checkpoint.get("reviewer_owner")):
            findings.append(RequirementRegenerationDryRunFinding("missing_reviewer_owner", path + ".reviewer_owner", "checkpoint must name a reviewer owner"))
        requirement_id = _text(checkpoint.get("requirement_id"))
        if requirement_id and known_requirement_ids and requirement_id not in known_requirement_ids:
            findings.append(RequirementRegenerationDryRunFinding("unknown_requirement_id", path + ".requirement_id", "checkpoint requirement ID must be known"))
        if checkpoint.get("blocks_promotion") is not True:
            findings.append(RequirementRegenerationDryRunFinding("checkpoint_does_not_block_promotion", path + ".blocks_promotion", "checkpoint must block promotion"))
        if checkpoint.get("blocks_processor_invocation") is not True:
            findings.append(RequirementRegenerationDryRunFinding("checkpoint_does_not_block_processor_invocation", path + ".blocks_processor_invocation", "checkpoint must block processor invocation"))

    stale_rows = list(_mapping_sequence(packet.get("stale_source_handling")))
    for index, row in enumerate(stale_rows):
        path = f"$.stale_source_handling[{index}]"
        source_id = _text(row.get("source_id"))
        if source_id and known_source_ids and source_id not in known_source_ids:
            findings.append(RequirementRegenerationDryRunFinding("unknown_source_id", path + ".source_id", "stale source ID must be known"))
        if row.get("regeneration_allowed_before_acknowledgement") is not False:
            findings.append(RequirementRegenerationDryRunFinding("stale_source_not_blocked", path + ".regeneration_allowed_before_acknowledgement", "stale sources must block regeneration until acknowledged"))
        if row.get("promotion_allowed_before_acknowledgement") is not False:
            findings.append(RequirementRegenerationDryRunFinding("stale_source_promotion_not_blocked", path + ".promotion_allowed_before_acknowledgement", "stale sources must block promotion until acknowledged"))
        if not _text(row.get("acknowledgement")):
            findings.append(RequirementRegenerationDryRunFinding("missing_stale_source_acknowledgement", path + ".acknowledgement", "stale source handling requires acknowledgement text"))

    rollback_refs = list(_mapping_sequence(packet.get("rollback_references")))
    if not rollback_refs:
        findings.append(RequirementRegenerationDryRunFinding("missing_rollback_references", "$.rollback_references", "rollback references are required"))
    for index, ref in enumerate(rollback_refs):
        path = f"$.rollback_references[{index}]"
        if not _text(ref.get("rollback_ref_id")):
            findings.append(RequirementRegenerationDryRunFinding("missing_rollback_ref_id", path + ".rollback_ref_id", "rollback reference ID is required"))
        if ref.get("local_discard_only") is not True:
            findings.append(RequirementRegenerationDryRunFinding("rollback_not_local_discard_only", path + ".local_discard_only", "rollback must be local discard only"))
        if ref.get("active_artifact_restore_required") is not False:
            findings.append(RequirementRegenerationDryRunFinding("active_restore_required", path + ".active_artifact_restore_required", "active artifacts must not require restore because they were not mutated"))

    attestations = packet.get("no_promotion_attestations")
    if not isinstance(attestations, Mapping):
        findings.append(RequirementRegenerationDryRunFinding("missing_no_promotion_attestations", "$.no_promotion_attestations", "no-promotion attestations are required"))
    else:
        required_false = (
            "active_requirements_regenerated",
            "active_requirements_mutated",
            "promotion_allowed",
            "processors_invoked",
            "urls_fetched",
            "devhub_launched",
        )
        for key in required_false:
            if attestations.get(key) is not False:
                findings.append(RequirementRegenerationDryRunFinding("invalid_no_promotion_attestation", f"$.no_promotion_attestations.{key}", "attestation must be false"))
        if attestations.get("requires_separate_human_promotion_packet") is not True:
            findings.append(RequirementRegenerationDryRunFinding("missing_human_promotion_gate", "$.no_promotion_attestations.requires_separate_human_promotion_packet", "separate human promotion gate is required"))

    return findings


def _validate_prerequisite_links(packet: Mapping[str, Any], findings: list[RequirementRegenerationDryRunFinding]) -> None:
    source_packets = _mapping(packet.get("source_packets"))
    if not _text(source_packets.get("public_source_change_impact_triage_packet_id")):
        findings.append(RequirementRegenerationDryRunFinding("missing_prerequisite_link", "$.source_packets.public_source_change_impact_triage_packet_id", "triage prerequisite packet ID is required"))
    if not _text(source_packets.get("requirement_regeneration_promotion_decision_packet_id")):
        findings.append(RequirementRegenerationDryRunFinding("missing_prerequisite_link", "$.source_packets.requirement_regeneration_promotion_decision_packet_id", "promotion prerequisite packet ID is required"))

    links = list(_mapping_sequence(packet.get("prerequisite_links")))
    roles = {_text(link.get("packet_role")) for link in links}
    for role in sorted(_REQUIRED_PREREQUISITE_ROLES):
        if role not in roles:
            findings.append(RequirementRegenerationDryRunFinding("missing_prerequisite_link", "$.prerequisite_links", f"missing prerequisite link for {role}"))
    for index, link in enumerate(links):
        path = f"$.prerequisite_links[{index}]"
        if not _text(link.get("packet_id")):
            findings.append(RequirementRegenerationDryRunFinding("missing_prerequisite_link", path + ".packet_id", "prerequisite packet ID is required"))
        if not _text(link.get("citation_path")):
            findings.append(RequirementRegenerationDryRunFinding("missing_prerequisite_link", path + ".citation_path", "prerequisite citation path is required"))
        if link.get("review_required_before_regeneration") is not True:
            findings.append(RequirementRegenerationDryRunFinding("missing_prerequisite_review_gate", path + ".review_required_before_regeneration", "prerequisite review gate is required"))


def _offline_regeneration_inputs(impact_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for record in impact_records:
        source_id = _text(record.get("source_id"), "unknown-source")
        citation_ids = sorted(_strings(record.get("cited_source_ids")))
        reviewer_owners = sorted(_strings(record.get("reviewer_owners"))) or ["unassigned-reviewer"]
        decision = _text(record.get("offline_triage_decision"), "offline_review_required")
        for requirement_id in sorted(_strings(record.get("affected_requirement_ids"))):
            rows[(source_id, requirement_id)] = {
                "input_id": "offline-regeneration-input." + _slug(source_id) + "." + _slug(requirement_id),
                "source_id": source_id,
                "requirement_id": requirement_id,
                "citation_ids": citation_ids,
                "reviewer_owners": reviewer_owners,
                "triage_decision": decision,
                "offline_only": True,
                "processor_invocation_allowed": False,
                "active_requirement_regeneration_allowed": False,
            }
    return [rows[key] for key in sorted(rows)]


def _reviewer_checkpoints(
    offline_inputs: Sequence[Mapping[str, Any]],
    promotion_decisions: Sequence[Mapping[str, Any]],
    stale_handling: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    checkpoints: list[dict[str, Any]] = []
    owners_by_requirement: dict[str, set[str]] = {}
    for item in offline_inputs:
        requirement_id = _text(item.get("requirement_id"))
        owners_by_requirement.setdefault(requirement_id, set()).update(_strings(item.get("reviewer_owners")))
    promoted_targets = {
        _text(decision.get("target_id"))
        for decision in promotion_decisions
        if _text(decision.get("final_decision")) == "promote_candidate_metadata_only"
    }
    stale_sources = sorted(_text(row.get("source_id")) for row in stale_handling)
    for requirement_id in sorted(owners_by_requirement):
        checkpoint_id = "review-checkpoint." + _slug(requirement_id)
        checkpoints.append({
            "checkpoint_id": checkpoint_id,
            "requirement_id": requirement_id,
            "reviewer_owner": sorted(owners_by_requirement[requirement_id])[0],
            "checkpoint_type": "offline_requirement_regeneration_dry_run_review",
            "expected_reviewer_actions": [
                "confirm cited source inputs",
                "confirm stale-source acknowledgement before regeneration",
                "confirm no active requirement mutation or promotion occurred",
            ],
            "promotion_decision_targets_observed": sorted(item for item in promoted_targets if item),
            "stale_source_ids_to_check": stale_sources,
            "blocks_promotion": True,
            "blocks_processor_invocation": True,
        })
    return checkpoints


def _stale_source_handling(impact_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in impact_records:
        source_id = _text(record.get("source_id"), "unknown-source")
        acknowledgements = sorted(_strings(record.get("stale_source_acknowledgements")))
        decision = _text(record.get("offline_triage_decision"))
        if acknowledgements or any(status in decision for status in _STALE_STATUSES):
            rows.append({
                "source_id": source_id,
                "acknowledgement": "; ".join(acknowledgements) or "reviewer acknowledgement required before dry-run regeneration",
                "handling": "defer_regeneration_until_reviewer_acknowledges_stale_source",
                "regeneration_allowed_before_acknowledgement": False,
                "promotion_allowed_before_acknowledgement": False,
            })
    return sorted(rows, key=lambda item: item["source_id"])


def _rollback_references(rollback_notes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for index, note in enumerate(rollback_notes, start=1):
        rollback_id = _text(note.get("rollback_note_id"), f"rollback-note-{index}")
        refs.append({
            "rollback_ref_id": rollback_id,
            "active_guardrail_bundle_id": _text(note.get("active_guardrail_bundle_id"), "active-bundle-not-specified"),
            "active_guardrail_bundle_revision": _text(note.get("active_guardrail_bundle_revision"), "active-revision-not-specified"),
            "rollback_action": "discard_dry_run_work_order_and_metadata_only_candidates",
            "local_discard_only": True,
            "active_artifact_restore_required": False,
        })
    if not refs:
        refs.append({
            "rollback_ref_id": "rollback.discard-dry-run-work-order",
            "active_guardrail_bundle_id": "active-bundle-not-specified",
            "active_guardrail_bundle_revision": "active-revision-not-specified",
            "rollback_action": "discard_dry_run_work_order_only",
            "local_discard_only": True,
            "active_artifact_restore_required": False,
        })
    return sorted(refs, key=lambda item: item["rollback_ref_id"])


def _safety_findings(value: Any) -> list[RequirementRegenerationDryRunFinding]:
    findings: list[RequirementRegenerationDryRunFinding] = []
    for path, key, child in _walk(value):
        key_text = str(key).lower() if key is not None else ""
        if key_text in _FORBIDDEN_TRUE_KEYS and child is True:
            findings.append(RequirementRegenerationDryRunFinding("forbidden_live_or_mutating_claim", path, "live execution, processor invocation, active regeneration, and promotion must be disabled"))
        if any(part in key_text for part in _FORBIDDEN_VALUE_KEY_PARTS) and child not in (None, "", False, [], {}):
            findings.append(RequirementRegenerationDryRunFinding("forbidden_private_or_raw_artifact", path, "private/session/raw/download/archive artifacts are not allowed"))
        if isinstance(child, str) and _is_production_ready_label(child):
            findings.append(RequirementRegenerationDryRunFinding("production_ready_label_before_review", path, "dry-run work orders must not claim production readiness before human review"))
        if key_text == "production_ready" and child is True:
            findings.append(RequirementRegenerationDryRunFinding("production_ready_label_before_review", path, "dry-run work orders must not claim production readiness before human review"))
    return findings


def _is_production_ready_label(value: str) -> bool:
    normalized = value.strip().lower().replace("_", "-")
    spaced = normalized.replace("-", " ")
    return normalized in _PRODUCTION_READY_LABELS or spaced in _PRODUCTION_READY_LABELS


def _walk(value: Any, path: str = "$", key: str | None = None):
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_path = f"{path}.{child_key}" if path != "$" else f"$.{child_key}"
            yield from _walk(child_value, child_path, str(child_key))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", None)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, list):
        return {item.strip() for item in value if isinstance(item, str) and item.strip()}
    if isinstance(value, tuple):
        return {item.strip() for item in value if isinstance(item, str) and item.strip()}
    return set()


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _slug(value: str) -> str:
    chars = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "item"


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]
