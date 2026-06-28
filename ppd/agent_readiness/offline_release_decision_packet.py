from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ppd.agent_readiness.offline_release_readiness_packet import validate_offline_release_readiness_packet

PACKET_TYPE = "ppd.offline_release_decision_packet.v1"

_MUTATION_KEYS = {
    "active_promotion",
    "apply_update",
    "commit_to_registry",
    "enable_devhub",
    "launch_devhub",
    "manifest_promotion_active",
    "mutate_guardrail_bundle",
    "mutate_manifest",
    "mutate_process_model",
    "mutate_registry",
    "performs_promotion",
    "promotion_enabled",
    "write_active_manifest",
    "write_active_registry",
}

_CONSEQUENTIAL_CONTROL_KEYS = {
    "cancel_enabled",
    "certification_enabled",
    "certify_enabled",
    "consequential_controls_enabled",
    "execution_enabled",
    "fee_payment_enabled",
    "final_submit_enabled",
    "official_action_enabled",
    "payment_enabled",
    "purchase_enabled",
    "schedule_enabled",
    "submission_enabled",
    "submit_enabled",
    "upload_enabled",
    "withdraw_enabled",
}

_PRIVATE_OR_RAW_KEYS = {
    "archive_artifact_ref",
    "archive_path",
    "archive_url",
    "authenticated_url",
    "download_path",
    "download_url",
    "local_path",
    "private_path",
    "private_url",
    "raw_archive_ref",
    "raw_body",
    "raw_body_ref",
    "raw_download_ref",
}

_PRIVATE_OR_RAW_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(^[A-Za-z]:\\Users\\[^\\]+\\)|"
    r"(https?://[^\s?#]+/(?:auth|authenticated|private|session|download|downloads|archive|archives|raw)(?:[/?#]|$))|"
    r"(https?://[^\s?#]+[^\s]*(?:[?&](?:access_token|auth|password|session|token)=))|"
    r"(auth[_-]?state|browser[_-]?state|cookie|credential|har|password|raw[_-]?(body|crawl|html)|"
    r"session[_-]?state|screenshot|secret|storage[_-]?state|token|trace\.zip|warc)",
    re.IGNORECASE,
)

_LIVE_ACTION_RE = re.compile(
    r"\b(live\s+(crawl|crawler|devhub|processor|compiler|llm)|submitted\s+to\s+devhub|"
    r"uploaded\s+to\s+devhub|paid\s+fees?|scheduled\s+inspection|certified\s+application)\b",
    re.IGNORECASE,
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?\s+(approval|issuance|permit|legal|compliance|outcome)|"
    r"(permit|application|inspection|appeal)\s+(will|shall)\s+be\s+(approved|issued|accepted|granted|upheld)|"
    r"legally\s+guaranteed|guaranteed\s+code\s+compliance)\b",
    re.IGNORECASE,
)

_REQUIRED_READINESS_FIELDS = (
    "release_blockers",
    "required_operator_signoffs",
    "rollback_checkpoints",
    "validation_evidence_references",
    "no_promotion_attestations",
)


@dataclass(frozen=True)
class OfflineReleaseDecisionValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def build_offline_release_decision_packet(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Build a cited, side-effect-free release decision packet from fixtures."""

    _raise_if_unsafe(inputs)
    readiness_packet = _mapping(inputs.get("offline_release_readiness_packet"))
    validation_results = list(_mapping_sequence(inputs.get("readiness_validation_results")))
    if not readiness_packet:
        raise ValueError("offline_release_readiness_packet is required")
    if not validation_results:
        raise ValueError("readiness_validation_results must include at least one command result")

    readiness_validation = validate_offline_release_readiness_packet(readiness_packet)
    unresolved_blockers = _blocker_summaries(readiness_packet)
    if not readiness_validation.valid:
        unresolved_blockers.append(
            {
                "blocker_id": "blocker-readiness-packet-validation",
                "candidate_id": str(readiness_packet.get("packet_id") or "offline-release-readiness-packet"),
                "reason": "readiness_packet_validation_failed",
                "summary": "; ".join(readiness_validation.problems),
                "source_evidence_ids": _packet_evidence_ids(readiness_packet),
            }
        )

    command_refs = [_validation_command_reference(index, result) for index, result in enumerate(validation_results)]
    failed_commands = [ref for ref in command_refs if ref["returncode"] != 0]
    for ref in failed_commands:
        unresolved_blockers.append(
            {
                "blocker_id": f"blocker-{ref['command_ref_id']}",
                "candidate_id": ref["command_ref_id"],
                "reason": "validation_command_failed",
                "summary": f"Validation command returned {ref['returncode']} and must pass before release review.",
                "source_evidence_ids": ref["source_evidence_ids"],
            }
        )

    recommendation = "no_go" if unresolved_blockers else "go_for_operator_review_only"
    decision_packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": str(inputs.get("packet_id") or "fixture-offline-release-decision-packet"),
        "fixture_only": True,
        "source_packet_id": str(readiness_packet.get("packet_id") or "offline-release-readiness-packet"),
        "recommendations": [
            {
                "recommendation_id": "release-decision-primary",
                "decision": recommendation,
                "summary": _recommendation_summary(recommendation),
                "source_evidence_ids": _packet_evidence_ids(readiness_packet),
                "validation_command_ref_ids": [ref["command_ref_id"] for ref in command_refs],
            }
        ],
        "unresolved_blocker_summaries": _dedupe_dicts(unresolved_blockers),
        "operator_signoff_requests": _operator_signoff_requests(readiness_packet),
        "rollback_checkpoints": _rollback_checkpoints(readiness_packet),
        "validation_command_references": command_refs,
        "no_promotion_attestations": _no_promotion_attestations(readiness_packet),
        "release_state_effects": {
            "mutates_registries": False,
            "mutates_manifests": False,
            "mutates_requirements": False,
            "mutates_process_models": False,
            "mutates_guardrails": False,
            "promotes_release": False,
            "launches_devhub": False,
            "uses_live_network": False,
        },
    }
    assert_valid_offline_release_decision_packet(decision_packet)
    return decision_packet


def validate_offline_release_decision_packet(packet: Mapping[str, Any]) -> OfflineReleaseDecisionValidationResult:
    problems: list[str] = []
    try:
        _raise_if_unsafe(packet)
    except ValueError as exc:
        problems.append(str(exc))

    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.offline_release_decision_packet.v1")
    if packet.get("fixture_only") is not True:
        problems.append("fixture_only must be true")

    for key in (
        "recommendations",
        "unresolved_blocker_summaries",
        "operator_signoff_requests",
        "rollback_checkpoints",
        "validation_command_references",
        "no_promotion_attestations",
    ):
        if not isinstance(packet.get(key), list):
            problems.append(f"packet must include list field: {key}")

    recommendations = list(_mapping_sequence(packet.get("recommendations")))
    blockers = list(_mapping_sequence(packet.get("unresolved_blocker_summaries")))
    signoffs = list(_mapping_sequence(packet.get("operator_signoff_requests")))
    checkpoints = list(_mapping_sequence(packet.get("rollback_checkpoints")))

    if not recommendations:
        problems.append("packet must include at least one cited recommendation")
    if not signoffs:
        problems.append("operator_signoff_requests must include at least one required signoff")
    if not checkpoints:
        problems.append("rollback_checkpoints must include at least one checkpoint")

    blocker_ids = {str(blocker.get("blocker_id")) for blocker in blockers if blocker.get("blocker_id")}
    for index, recommendation in enumerate(recommendations):
        decision = recommendation.get("decision")
        if decision not in {"no_go", "go_for_operator_review_only"}:
            problems.append(f"recommendations[{index}] has invalid decision")
        if not _evidence_ids(recommendation):
            problems.append(f"recommendations[{index}] lacks source_evidence_ids")
        if not recommendation.get("validation_command_ref_ids"):
            problems.append(f"recommendations[{index}] lacks validation_command_ref_ids")
        if blocker_ids and decision != "no_go":
            problems.append(f"recommendations[{index}] ignores unresolved readiness blockers")

    for index, blocker in enumerate(blockers):
        if not blocker.get("blocker_id"):
            problems.append(f"unresolved_blocker_summaries[{index}] lacks blocker_id")
        if not blocker.get("summary"):
            problems.append(f"unresolved_blocker_summaries[{index}] lacks summary")
        if not _evidence_ids(blocker):
            problems.append(f"unresolved_blocker_summaries[{index}] lacks source_evidence_ids")

    for index, signoff in enumerate(signoffs):
        if not signoff.get("role"):
            problems.append(f"operator_signoff_requests[{index}] lacks role")
        if signoff.get("required_before") != "any_release_promotion_or_operator_go_claim":
            problems.append(f"operator_signoff_requests[{index}] must gate promotion and go claims")
        if not _evidence_ids(signoff):
            problems.append(f"operator_signoff_requests[{index}] lacks source_evidence_ids")

    for index, checkpoint in enumerate(checkpoints):
        if not checkpoint.get("checkpoint"):
            problems.append(f"rollback_checkpoints[{index}] lacks checkpoint")
        if checkpoint.get("required_before") != "operator_signoff":
            problems.append(f"rollback_checkpoints[{index}] must be required before operator_signoff")
        if not _evidence_ids(checkpoint):
            problems.append(f"rollback_checkpoints[{index}] lacks source_evidence_ids")

    failed_command_refs: list[str] = []
    for index, command_ref in enumerate(_mapping_sequence(packet.get("validation_command_references"))):
        if not command_ref.get("command"):
            problems.append(f"validation_command_references[{index}] lacks command")
        if "returncode" not in command_ref:
            problems.append(f"validation_command_references[{index}] lacks returncode")
        elif int(command_ref.get("returncode") or 0) != 0:
            failed_command_refs.append(str(command_ref.get("command_ref_id") or index))
        if not _evidence_ids(command_ref):
            problems.append(f"validation_command_references[{index}] lacks source_evidence_ids")
    for command_ref_id in failed_command_refs:
        if not any(str(blocker.get("candidate_id")) == command_ref_id or command_ref_id in str(blocker.get("blocker_id")) for blocker in blockers):
            problems.append(f"failed validation command is not represented as a blocker: {command_ref_id}")

    for attestation in _mapping_sequence(packet.get("no_promotion_attestations")):
        if attestation.get("value") is not True:
            problems.append(f"no-promotion attestation is not true: {attestation.get('attestation_id', 'unknown')}")

    effects = _mapping(packet.get("release_state_effects"))
    for key in (
        "mutates_registries",
        "mutates_manifests",
        "mutates_requirements",
        "mutates_process_models",
        "mutates_guardrails",
        "promotes_release",
        "launches_devhub",
        "uses_live_network",
    ):
        if effects.get(key) is not False:
            problems.append(f"release_state_effects.{key} must be explicitly false")

    return OfflineReleaseDecisionValidationResult(valid=not problems, problems=tuple(problems))


def assert_valid_offline_release_decision_packet(packet: Mapping[str, Any]) -> None:
    result = validate_offline_release_decision_packet(packet)
    if not result.valid:
        raise ValueError("invalid_offline_release_decision_packet: " + "; ".join(result.problems))


def _blocker_summaries(readiness_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for blocker in _mapping_sequence(readiness_packet.get("release_blockers")):
        blockers.append(
            {
                "blocker_id": str(blocker.get("blocker_id") or "blocker-unknown"),
                "candidate_id": str(blocker.get("candidate_id") or "unknown-candidate"),
                "reason": str(blocker.get("reason") or "unresolved"),
                "summary": str(blocker.get("message") or blocker.get("summary") or "Unresolved readiness blocker."),
                "source_evidence_ids": _evidence_ids(blocker),
            }
        )
    return blockers


def _operator_signoff_requests(readiness_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for signoff in _mapping_sequence(readiness_packet.get("required_operator_signoffs")):
        candidate_id = str(signoff.get("candidate_id") or "release-decision")
        role = str(signoff.get("role") or "ppd_release_operator")
        requests.append(
            {
                "signoff_request_id": str(signoff.get("signoff_id") or f"signoff-{candidate_id}-{role}"),
                "role": role,
                "candidate_id": candidate_id,
                "request": "Review blocker status, rollback checkpoints, validation command references, and no-promotion attestations before any go claim.",
                "required_before": "any_release_promotion_or_operator_go_claim",
                "source_evidence_ids": _evidence_ids(signoff),
            }
        )
    return _dedupe_dicts(requests)


def _rollback_checkpoints(readiness_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    checkpoints: list[dict[str, Any]] = []
    for checkpoint in _mapping_sequence(readiness_packet.get("rollback_checkpoints")):
        checkpoints.append(
            {
                "checkpoint_id": str(checkpoint.get("checkpoint_id") or "rollback-release-decision"),
                "candidate_id": str(checkpoint.get("candidate_id") or "release-decision"),
                "checkpoint": str(checkpoint.get("checkpoint") or "Keep active release state unchanged."),
                "required_before": "operator_signoff",
                "source_evidence_ids": _evidence_ids(checkpoint),
            }
        )
    return _dedupe_dicts(checkpoints)


def _validation_command_reference(index: int, result: Mapping[str, Any]) -> dict[str, Any]:
    command = result.get("command")
    if isinstance(command, str):
        command_parts = [command]
    elif isinstance(command, Sequence) and not isinstance(command, (bytes, bytearray)):
        command_parts = [str(part) for part in command]
    else:
        command_parts = []
    command_ref_id = str(result.get("command_ref_id") or result.get("id") or f"validation-command-{index + 1}")
    return {
        "command_ref_id": command_ref_id,
        "command": command_parts,
        "returncode": int(result.get("returncode") or 0),
        "summary": str(result.get("summary") or "Fixture validation command result."),
        "source_evidence_ids": _evidence_ids(result) or [command_ref_id],
    }


def _no_promotion_attestations(readiness_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    attestations: list[dict[str, Any]] = []
    for attestation in _mapping_sequence(readiness_packet.get("no_promotion_attestations")):
        attestations.append(
            {
                "attestation_id": str(attestation.get("attestation_id") or "no-promotion"),
                "attests": str(attestation.get("attests") or "No promotion or active mutation is performed."),
                "value": attestation.get("value") is True,
                "source_packet_id": str(readiness_packet.get("packet_id") or "offline-release-readiness-packet"),
            }
        )
    return attestations


def _recommendation_summary(recommendation: str) -> str:
    if recommendation == "no_go":
        return "Do not promote or claim release readiness until unresolved blockers and failed validation commands are cleared."
    return "All cited fixture blockers and validation commands are clear for operator review only; promotion remains disabled."


def _packet_evidence_ids(packet: Mapping[str, Any]) -> list[str]:
    evidence_ids: list[str] = []
    for field in _REQUIRED_READINESS_FIELDS:
        for item in _mapping_sequence(packet.get(field)):
            evidence_ids.extend(_evidence_ids(item))
    return _dedupe_strings(evidence_ids) or [str(packet.get("packet_id") or "offline-release-readiness-packet")]


def _evidence_ids(record: Mapping[str, Any]) -> list[str]:
    raw = record.get("source_evidence_ids") or record.get("validation_evidence_ids") or record.get("citation_ids") or record.get("evidence_ids") or []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Sequence) and not isinstance(raw, (bytes, bytearray)):
        return [str(item) for item in raw if str(item)]
    return []


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _dedupe_strings(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _dedupe_dicts(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = tuple(sorted((str(key), repr(value)) for key, value in item.items()))
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _raise_if_unsafe(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _MUTATION_KEYS and child is True:
                raise ValueError(f"mutation or promotion flag must be false at {child_path}")
            if normalized_key in _CONSEQUENTIAL_CONTROL_KEYS and child is True:
                raise ValueError(f"consequential control must be disabled at {child_path}")
            if normalized_key in _PRIVATE_OR_RAW_KEYS and child not in (None, "", [], {}):
                raise ValueError(f"private, authenticated, download, archive, or raw reference is not allowed at {child_path}")
            _raise_if_unsafe(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _raise_if_unsafe(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if _PRIVATE_OR_RAW_RE.search(value):
            raise ValueError(f"private, authenticated, download, archive, or raw reference is not allowed at {path}")
        if _LIVE_ACTION_RE.search(value):
            raise ValueError(f"live execution claim is not allowed at {path}")
        if _OUTCOME_GUARANTEE_RE.search(value):
            raise ValueError(f"legal or permitting outcome guarantee is not allowed at {path}")
