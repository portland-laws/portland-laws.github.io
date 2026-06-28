"""Fixture-first guardrail recompile reviewer packet v5 validation."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.guardrail_bundle_recompile_candidate_v4 import (
    GuardrailBundleRecompileCandidateV4Error,
    REQUIRED_CHANGE_CATEGORIES,
    load_guardrail_bundle_recompile_candidate_v4_manifest,
    require_valid_guardrail_bundle_recompile_candidate_v4,
)

PACKET_TYPE = "ppd.guardrail_recompile_reviewer_packet.v5"
PACKET_VERSION = "v5"
MODE = "fixture_first_guardrail_bundle_recompile_candidate_v5_review_only"
CANDIDATE_TYPE = "ppd.guardrail_bundle_recompile_candidate.v4"

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/guardrail_recompile_reviewer_packet_v5.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_guardrail_recompile_reviewer_packet_v5"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

SUMMARY_CATEGORIES = {
    "reversible_action_predicates": "reversible_action_summaries",
    "exact_confirmation_predicates": "exact_confirmation_checkpoint_summaries",
    "refused_consequential_action_predicates": "refused_action_summaries",
    "stale_evidence_block_predicates": "stale_source_hold_summaries",
}

REQUIRED_ATTESTATIONS = {
    "fixture_first": True,
    "guardrail_bundle_recompile_candidate_v4_fixtures_only": True,
    "review_only": True,
    "inactive_candidate_only": True,
    "deterministic": True,
    "no_active_guardrail_bundle_mutation": True,
    "no_devhub_open": True,
    "no_private_or_session_artifacts": True,
    "no_upload": True,
    "no_submission": True,
    "no_certification": True,
    "no_payment": True,
    "no_scheduling": True,
    "no_legal_or_permitting_guarantee": True,
}

MUTATION_FLAGS = {
    "active_mutation",
    "active_bundle_mutation",
    "active_guardrail_mutation",
    "active_guardrail_bundle_mutation",
    "active_prompt_mutation",
    "active_process_model_mutation",
    "active_mutation_claim",
    "guardrail_mutation_claim",
    "guardrail_bundle_mutation_claim",
    "guardrails_changed",
    "guardrail_bundles_changed",
    "prompts_changed",
    "process_models_changed",
    "mutates_active_guardrails",
    "updates_active_guardrails",
    "opens_devhub",
    "uses_private_artifacts",
    "uses_session_artifacts",
    "uploads",
    "submits",
    "certifies",
    "pays",
    "schedules",
}

PRIVATE_KEY_FRAGMENTS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "har",
    "password",
    "private_artifact",
    "session_file",
    "session_path",
    "session_state",
    "storage_state",
    "trace_file",
)

FORBIDDEN_STRING_FRAGMENTS = (
    "opened devhub",
    "authenticated devhub",
    "live devhub",
    "live crawl",
    "active guardrail mutation",
    "active guardrail bundle mutation",
    "mutated active guardrail",
    "mutates active guardrail",
    "updated active guardrail",
    "updates active guardrail",
    "guardrails changed",
    "submitted permit",
    "official action completed",
    "completed official action",
    "certified acknowledgement",
    "paid fee",
    "payment completed",
    "scheduled inspection",
    "permit will be approved",
    "guarantee approval",
    "legal guarantee",
    "permitting guarantee",
)


@dataclass(frozen=True)
class GuardrailRecompileReviewerPacketV5Result:
    valid: bool
    problems: tuple[str, ...]


class GuardrailRecompileReviewerPacketV5Error(ValueError):
    """Raised when a guardrail recompile reviewer packet v5 is invalid."""


def load_guardrail_recompile_reviewer_packet_v5_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = _load_json_object(manifest_path)
    candidate_ref = _text(manifest.get("guardrail_bundle_recompile_candidate_v4_fixture"))
    if not candidate_ref:
        raise ValueError("manifest must include guardrail_bundle_recompile_candidate_v4_fixture")
    if set(manifest) - {"manifest_id", "guardrail_bundle_recompile_candidate_v4_fixture"}:
        raise ValueError("manifest may only reference a guardrail bundle recompile candidate v4 fixture")
    candidate = load_guardrail_bundle_recompile_candidate_v4_manifest(manifest_path.parent / candidate_ref)
    return build_guardrail_recompile_reviewer_packet_v5(
        candidate,
        source_manifest_id=_text(manifest.get("manifest_id"), "inline-guardrail-recompile-reviewer-packet-v5"),
        candidate_fixture_ref=candidate_ref,
    )


def build_guardrail_recompile_reviewer_packet_v5(
    guardrail_bundle_recompile_candidate_v4: Mapping[str, Any],
    source_manifest_id: str = "inline-fixtures",
    candidate_fixture_ref: str = "guardrail_bundle_recompile_candidate_v4/input_manifest.json",
) -> dict[str, Any]:
    try:
        require_valid_guardrail_bundle_recompile_candidate_v4(guardrail_bundle_recompile_candidate_v4)
    except GuardrailBundleRecompileCandidateV4Error as exc:
        raise GuardrailRecompileReviewerPacketV5Error(str(exc)) from exc

    candidate_rows = _mapping_sequence(guardrail_bundle_recompile_candidate_v4.get("inactive_deterministic_predicate_changes"))
    reviewer_rows = [_reviewer_row(index, row) for index, row in enumerate(candidate_rows)]
    summaries = _summary_sections(reviewer_rows)
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "source_manifest_id": source_manifest_id,
        "consumes": {"guardrail_bundle_recompile_candidate_v4_fixture": candidate_fixture_ref},
        "candidate_packet_type": guardrail_bundle_recompile_candidate_v4.get("packet_type"),
        "candidate_guardrail_bundle_ids": list(guardrail_bundle_recompile_candidate_v4.get("candidate_guardrail_bundle_ids", [])),
        "reviewer_predicate_rows": reviewer_rows,
        "source_evidence_references": _source_evidence_references(reviewer_rows),
        "cited_process_impact_references": _source_evidence_references(reviewer_rows),
        "source_freshness_caveats": _source_freshness_caveats(reviewer_rows),
        "stale_source_hold_summaries": summaries["stale_source_hold_summaries"],
        "reversible_action_summaries": summaries["reversible_action_summaries"],
        "exact_confirmation_checkpoint_summaries": summaries["exact_confirmation_checkpoint_summaries"],
        "refused_action_summaries": summaries["refused_action_summaries"],
        "rollback_owner_placeholders": _rollback_owner_placeholders(guardrail_bundle_recompile_candidate_v4),
        "reviewer_decision_placeholders": _reviewer_decision_placeholders(reviewer_rows),
        "validation_status": {
            "status": "review_packet_validated_offline_only",
            "candidate_validation_status": _mapping(guardrail_bundle_recompile_candidate_v4.get("validation_status")).get("status"),
            "active_bundle_mutation": False,
            "validation_commands": OFFLINE_VALIDATION_COMMANDS,
        },
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "attestations": dict(REQUIRED_ATTESTATIONS),
    }
    require_valid_guardrail_recompile_reviewer_packet_v5(packet)
    return packet


def validate_guardrail_recompile_reviewer_packet_v5(packet: Mapping[str, Any]) -> GuardrailRecompileReviewerPacketV5Result:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return GuardrailRecompileReviewerPacketV5Result(False, ("packet must be an object",))
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v5")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("candidate_packet_type") != CANDIDATE_TYPE:
        problems.append(f"candidate_packet_type must be {CANDIDATE_TYPE}")
    if not _text(packet.get("source_manifest_id")):
        problems.append("source_manifest_id must be present")
    if not _text_sequence(packet.get("candidate_guardrail_bundle_ids")):
        problems.append("candidate_guardrail_bundle_ids must be non-empty")

    consumes = _mapping(packet.get("consumes"))
    if set(consumes) != {"guardrail_bundle_recompile_candidate_v4_fixture"}:
        problems.append("consumes must contain only guardrail_bundle_recompile_candidate_v4_fixture")
    if not _text(consumes.get("guardrail_bundle_recompile_candidate_v4_fixture")).endswith(".json"):
        problems.append("guardrail_bundle_recompile_candidate_v4_fixture must point to a JSON fixture")

    rows = _mapping_sequence(packet.get("reviewer_predicate_rows"))
    if tuple(_text(row.get("category")) for row in rows) != REQUIRED_CHANGE_CATEGORIES:
        problems.append("reviewer_predicate_rows must cover candidate categories in deterministic order")
    for index, row in enumerate(rows):
        _validate_reviewer_row(row, index, problems)

    _validate_reference_section(packet, "source_evidence_references", problems)
    _validate_reference_section(packet, "cited_process_impact_references", problems)
    _validate_summary_section(packet, "source_freshness_caveats", problems)
    _validate_summary_section(packet, "stale_source_hold_summaries", problems)
    _validate_summary_section(packet, "reversible_action_summaries", problems)
    _validate_summary_section(packet, "exact_confirmation_checkpoint_summaries", problems)
    _validate_summary_section(packet, "refused_action_summaries", problems)
    _validate_placeholder_section(packet, "rollback_owner_placeholders", "rollback_owner_placeholder", problems)
    _validate_placeholder_section(packet, "reviewer_decision_placeholders", "reviewer_decision_placeholder", problems)

    validation_status = _mapping(packet.get("validation_status"))
    if validation_status.get("status") != "review_packet_validated_offline_only":
        problems.append("validation_status.status must be review_packet_validated_offline_only")
    if validation_status.get("active_bundle_mutation") is not False:
        problems.append("validation_status.active_bundle_mutation must be false")
    if validation_status.get("validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        problems.append("validation_status.validation_commands must exactly match offline_validation_commands")
    if packet.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match the reviewer packet command bundle")

    attestations = _mapping(packet.get("attestations"))
    for key, expected in REQUIRED_ATTESTATIONS.items():
        if attestations.get(key) is not expected:
            problems.append(f"attestations.{key} must be true")

    _validate_no_forbidden_state(packet, problems)
    return GuardrailRecompileReviewerPacketV5Result(not problems, tuple(problems))


def require_valid_guardrail_recompile_reviewer_packet_v5(packet: Mapping[str, Any]) -> None:
    result = validate_guardrail_recompile_reviewer_packet_v5(packet)
    if not result.valid:
        raise GuardrailRecompileReviewerPacketV5Error("invalid guardrail recompile reviewer packet v5: " + "; ".join(result.problems))


def _reviewer_row(index: int, candidate_row: Mapping[str, Any]) -> dict[str, Any]:
    category = _text(candidate_row.get("category"))
    cited_refs = _mapping_sequence(candidate_row.get("source_impact_refs"))
    return {
        "reviewer_row_id": f"reviewer-v5-{index + 1:02d}-{category}",
        "candidate_change_id": _text(candidate_row.get("change_id")),
        "category": category,
        "placeholder_guardrail_bundle_id": _text(candidate_row.get("placeholder_guardrail_bundle_id")),
        "placeholder_predicate_slot": _text(candidate_row.get("placeholder_predicate_slot")),
        "reviewer_ready_predicate": _text(candidate_row.get("proposed_inactive_predicate")),
        "source_evidence_refs": [_source_ref(ref) for ref in cited_refs],
        "process_impact_reference_count": len(cited_refs),
        "review_status": "pending_human_review",
        "reviewer_hold_status": "unresolved",
        "active_bundle_mutation": False,
        "rollback_note_ref": _text(candidate_row.get("rollback_note_ref")),
    }


def _source_ref(ref: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "impact_id": _text(ref.get("impact_id")),
        "process_id": _text(ref.get("process_id")),
        "citation_refs": _text_sequence(ref.get("citation_refs")),
    }


def _source_evidence_references(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    references: list[dict[str, Any]] = []
    for row in rows:
        for ref in _mapping_sequence(row.get("source_evidence_refs")):
            key = (_text(ref.get("impact_id")), _text(ref.get("process_id")))
            if key in seen:
                continue
            seen.add(key)
            references.append(
                {
                    "impact_id": key[0],
                    "process_id": key[1],
                    "citation_refs": _text_sequence(ref.get("citation_refs")),
                    "used_by_reviewer_row_ids": [
                        _text(other.get("reviewer_row_id"))
                        for other in rows
                        if any(_text(item.get("impact_id")) == key[0] for item in _mapping_sequence(other.get("source_evidence_refs")))
                    ],
                }
            )
    return references


def _source_freshness_caveats(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "summary_id": "source-freshness-caveat-v5",
            "reviewer_row_id": "all-reviewer-rows",
            "predicate": "Reviewer must keep recommendations held when cited fixture evidence is stale, missing, or conflicting.",
            "boundary": "Freshness caveat is review-only and does not update active source state.",
            "citation_refs": [
                citation
                for row in rows
                for ref in _mapping_sequence(row.get("source_evidence_refs"))
                for citation in _text_sequence(ref.get("citation_refs"))
            ],
        }
    ]


def _summary_sections(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    summaries: dict[str, list[dict[str, Any]]] = {name: [] for name in SUMMARY_CATEGORIES.values()}
    summaries["reversible_action_summaries"] = []
    for row in rows:
        target = SUMMARY_CATEGORIES.get(_text(row.get("category")))
        if target is None:
            continue
        summaries[target].append(
            {
                "summary_id": f"summary-{_text(row.get('reviewer_row_id'))}",
                "reviewer_row_id": _text(row.get("reviewer_row_id")),
                "predicate": _text(row.get("reviewer_ready_predicate")),
                "boundary": _boundary_for_category(_text(row.get("category"))),
                "citation_refs": [
                    citation
                    for ref in _mapping_sequence(row.get("source_evidence_refs"))
                    for citation in _text_sequence(ref.get("citation_refs"))
                ],
            }
        )
    return summaries


def _rollback_owner_placeholders(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    notes = _mapping_sequence(candidate.get("rollback_notes"))
    return [
        {
            "placeholder_id": f"rollback-owner-placeholder-{index + 1:02d}",
            "rollback_note_ref": _text(note.get("rollback_id")),
            "rollback_owner_placeholder": "pending_human_reviewer_assignment",
            "release_state": "held",
        }
        for index, note in enumerate(notes)
    ]


def _reviewer_decision_placeholders(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "placeholder_id": f"decision-placeholder-{_text(row.get('reviewer_row_id'))}",
            "reviewer_row_id": _text(row.get("reviewer_row_id")),
            "reviewer_decision_placeholder": "pending_human_reviewer_decision",
            "allowed_decisions": ["approve_in_later_task", "reject_in_later_task", "hold_for_source_refresh"],
            "release_state": "held",
        }
        for row in rows
    ]


def _boundary_for_category(category: str) -> str:
    mapping = {
        "reversible_action_predicates": "Local draft and read-only preparation only.",
        "exact_confirmation_predicates": "Exact user confirmation remains required before attended consequential handling.",
        "refused_consequential_action_predicates": "Official execution is refused and converted to attended handoff text.",
        "stale_evidence_block_predicates": "Stale or conflicting evidence keeps the row on reviewer hold.",
    }
    return mapping.get(category, "Reviewer disposition is required before later activation work.")


def _validate_reviewer_row(row: Mapping[str, Any], index: int, problems: list[str]) -> None:
    prefix = f"reviewer_predicate_rows[{index}]"
    for key in ("reviewer_row_id", "candidate_change_id", "category", "placeholder_guardrail_bundle_id", "placeholder_predicate_slot", "reviewer_ready_predicate", "rollback_note_ref"):
        if not _text(row.get(key)):
            problems.append(f"{prefix}.{key} must be present")
    if row.get("review_status") != "pending_human_review":
        problems.append(f"{prefix}.review_status must be pending_human_review")
    if row.get("reviewer_hold_status") != "unresolved":
        problems.append(f"{prefix}.reviewer_hold_status must be unresolved")
    if row.get("active_bundle_mutation") is not False:
        problems.append(f"{prefix}.active_bundle_mutation must be false")
    refs = _mapping_sequence(row.get("source_evidence_refs"))
    if not refs:
        problems.append(f"{prefix}.source_evidence_refs must be non-empty")
    if row.get("process_impact_reference_count") != len(refs):
        problems.append(f"{prefix}.process_impact_reference_count must match source_evidence_refs")
    for ref_index, ref in enumerate(refs):
        ref_prefix = f"{prefix}.source_evidence_refs[{ref_index}]"
        if not _text(ref.get("impact_id")):
            problems.append(f"{ref_prefix}.impact_id must be present")
        if not _text(ref.get("process_id")):
            problems.append(f"{ref_prefix}.process_id must be present")
        if not _text_sequence(ref.get("citation_refs")):
            problems.append(f"{ref_prefix}.citation_refs must be non-empty")


def _validate_reference_section(packet: Mapping[str, Any], key: str, problems: list[str]) -> None:
    refs = _mapping_sequence(packet.get(key))
    if not refs:
        problems.append(f"{key} must be non-empty")
    for index, ref in enumerate(refs):
        prefix = f"{key}[{index}]"
        if not _text(ref.get("impact_id")):
            problems.append(f"{prefix}.impact_id must be present")
        if not _text(ref.get("process_id")):
            problems.append(f"{prefix}.process_id must be present")
        if not _text_sequence(ref.get("citation_refs")):
            problems.append(f"{prefix}.citation_refs must be non-empty")
        if not _text_sequence(ref.get("used_by_reviewer_row_ids")):
            problems.append(f"{prefix}.used_by_reviewer_row_ids must be non-empty")


def _validate_summary_section(packet: Mapping[str, Any], key: str, problems: list[str]) -> None:
    summaries = _mapping_sequence(packet.get(key))
    if not summaries:
        problems.append(f"{key} must be non-empty")
    for index, summary in enumerate(summaries):
        prefix = f"{key}[{index}]"
        for field in ("summary_id", "reviewer_row_id", "predicate", "boundary"):
            if not _text(summary.get(field)):
                problems.append(f"{prefix}.{field} must be present")
        if not _text_sequence(summary.get("citation_refs")):
            problems.append(f"{prefix}.citation_refs must be non-empty")


def _validate_placeholder_section(packet: Mapping[str, Any], key: str, placeholder_key: str, problems: list[str]) -> None:
    placeholders = _mapping_sequence(packet.get(key))
    if not placeholders:
        problems.append(f"{key} must be non-empty")
    for index, placeholder in enumerate(placeholders):
        prefix = f"{key}[{index}]"
        if not _text(placeholder.get("placeholder_id")):
            problems.append(f"{prefix}.placeholder_id must be present")
        if not _text(placeholder.get(placeholder_key)):
            problems.append(f"{prefix}.{placeholder_key} must be present")
        if placeholder.get("release_state") != "held":
            problems.append(f"{prefix}.release_state must be held")


def _validate_no_forbidden_state(value: Any, problems: list[str], path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower().replace("-", "_").replace(" ", "_")
            child_path = f"{path}.{key_text}"
            if normalized in MUTATION_FLAGS and child is not False:
                problems.append(f"{child_path} must be false or absent")
            if any(fragment in normalized for fragment in PRIVATE_KEY_FRAGMENTS):
                problems.append(f"{child_path} must not include private/session/auth artifact keys")
            _validate_no_forbidden_state(child, problems, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _validate_no_forbidden_state(child, problems, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for fragment in FORBIDDEN_STRING_FRAGMENTS:
            if fragment in lowered:
                problems.append(f"{path} must not contain forbidden live, official-action, or guarantee claim: {fragment}")


def _load_json_object(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in (_text(item) for item in value) if item]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default
