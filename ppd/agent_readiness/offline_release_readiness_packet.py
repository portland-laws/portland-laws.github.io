from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PRIVATE_KEYS = {
    "access_token",
    "auth_state",
    "browser_state",
    "card_number",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "cvv",
    "devhub_session",
    "email",
    "field_value",
    "har",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "private_value",
    "raw_value",
    "refresh_token",
    "screenshot",
    "secret",
    "session",
    "session_cookie",
    "session_state",
    "ssn",
    "token",
    "trace",
    "user_input",
    "value",
}

MUTATION_KEYS = {
    "apply_update",
    "archive_manifest_promotion_enabled",
    "commit_to_registry",
    "guardrail_promotion_enabled",
    "manifest_promotion_active",
    "mutate_guardrail_bundle",
    "mutate_manifest",
    "mutate_process_model",
    "mutate_registry",
    "promotion_enabled",
    "registry_write_enabled",
    "write_active_manifest",
    "write_active_registry",
}

RAW_OR_PRIVATE_PATH_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/private/)|(^/tmp/)|(^[A-Za-z]:\\Users\\[^\\]+\\)|(\.har$)|(trace\.zip$)|(/raw/)|(/downloads?/)"
)

REQUIRED_INPUT_COLLECTIONS = (
    "source_registry_update_candidates",
    "archive_manifest_promotion_readiness",
    "requirement_rerun_review_dispositions",
    "process_model_update_candidates",
    "guardrail_bundle_update_candidates",
    "agent_regression_rerun_plans",
)


@dataclass(frozen=True)
class OfflineReleaseReadinessValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def compile_offline_release_readiness_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Compile a side-effect-free offline release readiness packet.

    The compiler consumes fixture metadata only. It does not read files, crawl,
    call DevHub, or mutate any PP&D registry, manifest, requirement, process
    model, or guardrail bundle.
    """

    _raise_if_unsafe_input(packet)
    evidence_by_id = _evidence_by_id(packet.get("validation_evidence"))

    blockers: list[dict[str, Any]] = []
    signoffs: list[dict[str, Any]] = []
    rollback_checkpoints: list[dict[str, Any]] = []
    validation_refs: list[dict[str, Any]] = []

    for collection_name in REQUIRED_INPUT_COLLECTIONS:
        records = list(_mapping_sequence(packet.get(collection_name)))
        if not records:
            blockers.append(_blocker(collection_name, "missing_input_collection", [], "Required release input collection is empty."))
            continue
        for record in records:
            record_id = _record_id(record, collection_name)
            evidence_ids = _evidence_ids(record)
            status = _status(record)
            if not evidence_ids:
                blockers.append(_blocker(record_id, "missing_citation", [], "Candidate lacks validation evidence citations."))
            for evidence_id in evidence_ids:
                if evidence_id not in evidence_by_id:
                    blockers.append(_blocker(record_id, "unknown_citation", [evidence_id], "Candidate cites unknown validation evidence."))
                else:
                    validation_refs.append(_validation_ref(record_id, evidence_id, evidence_by_id[evidence_id]))
            if status in {"blocked", "failed", "missing", "needs_review", "open", "pending", "stale", "unresolved"}:
                blockers.append(_blocker(record_id, status, evidence_ids, "Candidate is not release-clear."))
            signoff_roles = _signoff_roles(record, collection_name)
            for role in signoff_roles:
                signoffs.append({
                    "signoff_id": f"signoff-{record_id}-{role}",
                    "role": role,
                    "candidate_id": record_id,
                    "source_evidence_ids": evidence_ids,
                    "required_before": "any_promotion_or_operator_release_claim",
                })
            rollback_checkpoints.append({
                "checkpoint_id": f"rollback-{record_id}",
                "candidate_id": record_id,
                "source_evidence_ids": evidence_ids,
                "checkpoint": _rollback_text(collection_name),
                "must_complete_before": "operator_signoff",
            })

    compiled = {
        "packet_id": str(packet.get("packet_id") or "fixture-first-offline-release-readiness"),
        "packet_status": "blocked_no_promotion" if blockers else "ready_for_operator_review_no_promotion",
        "fixture_only": True,
        "source": "committed PP&D test fixtures only",
        "release_blockers": _dedupe_dicts(blockers),
        "required_operator_signoffs": _dedupe_dicts(signoffs),
        "rollback_checkpoints": _dedupe_dicts(rollback_checkpoints),
        "validation_evidence_references": _dedupe_dicts(validation_refs),
        "no_promotion_attestations": [
            {"attestation_id": "no-registry-mutation", "attests": "source registries are not mutated by this packet", "value": True},
            {"attestation_id": "no-manifest-promotion", "attests": "archive manifests are not promoted by this packet", "value": True},
            {"attestation_id": "no-requirement-mutation", "attests": "requirements are not mutated by this packet", "value": True},
            {"attestation_id": "no-process-model-mutation", "attests": "process models are not mutated by this packet", "value": True},
            {"attestation_id": "no-guardrail-mutation", "attests": "guardrail bundles are not mutated by this packet", "value": True},
            {"attestation_id": "no-live-devhub-or-crawl", "attests": "no live crawl, DevHub session, authenticated automation, upload, submission, payment, scheduling, certification, or cancellation is performed", "value": True},
        ],
        "execution_boundaries": {
            "live_network": False,
            "launches_devhub": False,
            "uses_authenticated_session": False,
            "writes_registries": False,
            "writes_manifests": False,
            "writes_requirements": False,
            "writes_process_models": False,
            "writes_guardrails": False,
            "performs_promotion": False,
        },
    }
    assert_valid_offline_release_readiness_packet(compiled)
    return compiled


def validate_offline_release_readiness_packet(packet: Mapping[str, Any]) -> OfflineReleaseReadinessValidationResult:
    problems: list[str] = []
    try:
        _raise_if_unsafe_input(packet)
    except ValueError as exc:
        problems.append(str(exc))

    for key in ("release_blockers", "required_operator_signoffs", "rollback_checkpoints", "validation_evidence_references", "no_promotion_attestations"):
        if not isinstance(packet.get(key), list):
            problems.append(f"packet must include list field: {key}")

    for index, blocker in enumerate(_mapping_sequence(packet.get("release_blockers"))):
        if not _evidence_ids(blocker):
            problems.append(f"release_blockers[{index}] lacks source_evidence_ids")
        if not blocker.get("blocker_id"):
            problems.append(f"release_blockers[{index}] lacks blocker_id")

    for index, signoff in enumerate(_mapping_sequence(packet.get("required_operator_signoffs"))):
        if not signoff.get("role"):
            problems.append(f"required_operator_signoffs[{index}] lacks role")
        if not _evidence_ids(signoff):
            problems.append(f"required_operator_signoffs[{index}] lacks source_evidence_ids")

    for index, checkpoint in enumerate(_mapping_sequence(packet.get("rollback_checkpoints"))):
        if not checkpoint.get("checkpoint"):
            problems.append(f"rollback_checkpoints[{index}] lacks checkpoint")
        if not _evidence_ids(checkpoint):
            problems.append(f"rollback_checkpoints[{index}] lacks source_evidence_ids")

    attestations = list(_mapping_sequence(packet.get("no_promotion_attestations")))
    if not attestations:
        problems.append("packet must include no_promotion_attestations")
    for attestation in attestations:
        if attestation.get("value") is not True:
            problems.append(f"no-promotion attestation is not true: {attestation.get('attestation_id', 'unknown')}")

    boundaries = _mapping(packet.get("execution_boundaries"))
    for key in ("live_network", "launches_devhub", "uses_authenticated_session", "writes_registries", "writes_manifests", "writes_requirements", "writes_process_models", "writes_guardrails", "performs_promotion"):
        if boundaries.get(key) is not False:
            problems.append(f"execution boundary must be explicitly false: {key}")

    return OfflineReleaseReadinessValidationResult(valid=not problems, problems=tuple(problems))


def assert_valid_offline_release_readiness_packet(packet: Mapping[str, Any]) -> None:
    result = validate_offline_release_readiness_packet(packet)
    if not result.valid:
        raise ValueError("invalid_offline_release_readiness_packet: " + "; ".join(result.problems))


def _raise_if_unsafe_input(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in PRIVATE_KEYS and child not in (None, "", [], {}):
                raise ValueError(f"private/session field is not allowed at {child_path}")
            if normalized_key in MUTATION_KEYS and child is True:
                raise ValueError(f"mutation or promotion flag must be false at {child_path}")
            _raise_if_unsafe_input(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _raise_if_unsafe_input(child, f"{path}[{index}]")
    elif isinstance(value, str) and RAW_OR_PRIVATE_PATH_RE.search(value):
        raise ValueError(f"raw output or private local path is not allowed at {path}")


def _evidence_by_id(value: Any) -> dict[str, Mapping[str, Any]]:
    evidence: dict[str, Mapping[str, Any]] = {}
    for item in _mapping_sequence(value):
        evidence_id = str(item.get("evidence_id") or item.get("id") or "")
        if evidence_id:
            evidence[evidence_id] = item
    return evidence


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _record_id(record: Mapping[str, Any], fallback: str) -> str:
    return str(record.get("candidate_id") or record.get("packet_id") or record.get("plan_id") or record.get("disposition_id") or record.get("id") or fallback)


def _evidence_ids(record: Mapping[str, Any]) -> list[str]:
    raw = record.get("source_evidence_ids") or record.get("validation_evidence_ids") or record.get("citation_ids") or record.get("evidence_ids") or []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Sequence):
        return [item for item in raw if isinstance(item, str) and item]
    return []


def _status(record: Mapping[str, Any]) -> str:
    return str(record.get("status") or record.get("review_status") or record.get("readiness_status") or record.get("validation_status") or "").lower()


def _signoff_roles(record: Mapping[str, Any], collection_name: str) -> list[str]:
    raw = record.get("required_operator_signoffs") or record.get("required_signoff_roles") or record.get("operator_signoff_roles")
    roles: list[str]
    if isinstance(raw, str):
        roles = [raw]
    elif isinstance(raw, Sequence):
        roles = [item for item in raw if isinstance(item, str) and item]
    else:
        roles = []
    if roles:
        return roles
    if collection_name == "archive_manifest_promotion_readiness":
        return ["archive_operator"]
    if collection_name == "guardrail_bundle_update_candidates":
        return ["guardrail_reviewer"]
    if collection_name == "agent_regression_rerun_plans":
        return ["agent_regression_reviewer"]
    return ["ppd_release_operator"]


def _rollback_text(collection_name: str) -> str:
    if collection_name == "source_registry_update_candidates":
        return "Keep active source registry unchanged and discard candidate registry diff."
    if collection_name == "archive_manifest_promotion_readiness":
        return "Keep current archive manifest pointer unchanged and do not promote candidate manifest."
    if collection_name == "requirement_rerun_review_dispositions":
        return "Keep current requirement formalization output unchanged until rerun disposition is approved."
    if collection_name == "process_model_update_candidates":
        return "Keep active process model unchanged and retain prior process-model fixture."
    if collection_name == "guardrail_bundle_update_candidates":
        return "Keep active guardrail bundle unchanged and retain prior bundle id."
    return "Do not execute agent regression rerun plan outside committed fixtures."


def _blocker(candidate_id: str, reason: str, evidence_ids: list[str], message: str) -> dict[str, Any]:
    return {
        "blocker_id": f"blocker-{candidate_id}-{reason}",
        "candidate_id": candidate_id,
        "reason": reason,
        "message": message,
        "source_evidence_ids": evidence_ids,
    }


def _validation_ref(candidate_id: str, evidence_id: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "reference_id": f"validation-{candidate_id}-{evidence_id}",
        "candidate_id": candidate_id,
        "evidence_id": evidence_id,
        "source_evidence_ids": [evidence_id],
        "evidence_type": str(evidence.get("evidence_type") or "fixture_validation"),
        "description": str(evidence.get("description") or evidence_id),
    }


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = tuple(sorted((str(key), repr(value)) for key, value in item.items()))
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped
