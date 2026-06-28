from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from ppd.agent_readiness.dry_run_promotion_sequence_packet import validate_dry_run_promotion_sequence_packet
from ppd.agent_readiness.offline_release_decision_packet import validate_offline_release_decision_packet
from ppd.agent_readiness.post_promotion_smoke_test_plan import validate_post_promotion_smoke_test_plan

PACKET_TYPE = "ppd.release_notes_candidate_packet.v1"

_FALSE_POLICY_KEYS = {
    "publishes_release_notes",
    "changes_active_artifacts",
    "writes_active_state",
    "promotes_release",
    "uses_live_network",
    "invokes_devhub",
    "invokes_agents",
    "invokes_crawlers",
    "invokes_processors",
    "reads_private_case_files",
}

_REQUIRED_LISTS = (
    "operator_facing_change_notes",
    "known_limitations",
    "validation_evidence_references",
    "rollback_notes",
    "manual_handoff_reminders",
    "no_publication_attestations",
)

_PRIVATE_OR_RUNTIME_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(^/var/folders/)|"
    r"(auth[_-]?state|browser[_-]?state|cookie|credential|download[_-]?(path|url|ref)?|har|password|"
    r"private[_-]?path|raw[_-]?(archive|body|crawl|download|html)|session[_-]?state|screenshot|secret|"
    r"storage[_-]?state|token|trace\.zip|warc|\.warc(\.gz)?)",
    re.IGNORECASE,
)

_RAW_REFERENCE_RE = re.compile(
    r"\b(raw crawl|raw download|raw archive|downloaded document|crawl output|archive output|warc|har|trace zip)\b",
    re.IGNORECASE,
)

_LIVE_OR_PUBLICATION_CLAIM_RE = re.compile(
    r"\b(release notes published|published release notes|promoted to active|active artifact changed|"
    r"active artifacts changed|live devhub executed|live crawler executed|live processor executed|"
    r"submitted to devhub|uploaded to devhub|paid fees|scheduled inspection|certified application)\b",
    re.IGNORECASE,
)

_LEGAL_OR_PERMITTING_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|ensures?|will ensure|will be approved|permit approval is assured|"
    r"approval is guaranteed|legally compliant|legal advice|binding legal determination|"
    r"no legal risk|no permitting risk|will satisfy code|will pass inspection)\b",
    re.IGNORECASE,
)

_PRIVATE_URL_HOST_MARKERS = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
)

_AUTH_URL_MARKERS = (
    "/login",
    "/signin",
    "/sign-in",
    "/oauth",
    "/saml",
    "/session",
    "access_token=",
    "auth=",
    "token=",
)

_MUTATION_FLAG_KEYS = {
    "active_artifact_mutation",
    "active_artifact_mutation_enabled",
    "active_artifact_mutation_flag",
    "active_mutation",
    "changes_active_artifacts",
    "mutates_active_artifacts",
    "promotes_release",
    "publishes_release_notes",
    "writes_active_state",
}


@dataclass(frozen=True)
class ReleaseNotesCandidateValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def build_release_notes_candidate_packet(
    offline_release_decision_packet: Mapping[str, Any],
    dry_run_promotion_sequence_packet: Mapping[str, Any],
    post_promotion_smoke_test_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Build fixture-only operator-facing release note candidates from readiness packets."""

    _require_valid_sources(
        offline_release_decision_packet,
        dry_run_promotion_sequence_packet,
        post_promotion_smoke_test_plan,
    )

    offline_packet_id = _packet_id(offline_release_decision_packet, "offline-release-decision-packet")
    dry_run_packet_id = _packet_id(dry_run_promotion_sequence_packet, "dry-run-promotion-sequence-packet")
    smoke_plan_id = _packet_id(post_promotion_smoke_test_plan, "post-promotion-smoke-test-plan")
    evidence_ids = _packet_evidence_ids(
        offline_release_decision_packet,
        dry_run_promotion_sequence_packet,
        post_promotion_smoke_test_plan,
    )

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": "fixture-first-release-notes-candidate-packet",
        "fixture_only": True,
        "candidate_status": "draft_operator_notes_not_published",
        "source_packet_ids": {
            "offline_release_decision_packet": offline_packet_id,
            "dry_run_promotion_sequence_packet": dry_run_packet_id,
            "post_promotion_smoke_test_plan": smoke_plan_id,
        },
        "publication_policy": {
            "fixtures_only": True,
            "publishes_release_notes": False,
            "changes_active_artifacts": False,
            "writes_active_state": False,
            "promotes_release": False,
            "uses_live_network": False,
            "invokes_devhub": False,
            "invokes_agents": False,
            "invokes_crawlers": False,
            "invokes_processors": False,
            "reads_private_case_files": False,
        },
        "operator_facing_change_notes": _change_notes(offline_release_decision_packet, dry_run_promotion_sequence_packet, post_promotion_smoke_test_plan, evidence_ids),
        "known_limitations": _known_limitations(offline_release_decision_packet, dry_run_promotion_sequence_packet, post_promotion_smoke_test_plan, evidence_ids),
        "validation_evidence_references": _validation_evidence_references(offline_release_decision_packet, dry_run_promotion_sequence_packet, post_promotion_smoke_test_plan),
        "rollback_notes": _rollback_notes(offline_release_decision_packet, dry_run_promotion_sequence_packet, evidence_ids),
        "manual_handoff_reminders": _manual_handoff_reminders(offline_release_decision_packet, dry_run_promotion_sequence_packet, post_promotion_smoke_test_plan, evidence_ids),
        "no_publication_attestations": [
            {
                "attestation_id": "release-notes-candidate-only",
                "attested": True,
                "summary": "This packet is a release notes candidate for operator review only and does not publish notes or update active PP&D artifacts.",
                "source_evidence_ids": evidence_ids,
            }
        ],
    }
    assert_valid_release_notes_candidate_packet(packet)
    return packet


def validate_release_notes_candidate_packet(packet: Mapping[str, Any]) -> ReleaseNotesCandidateValidationResult:
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.release_notes_candidate_packet.v1")
    if packet.get("fixture_only") is not True:
        problems.append("fixture_only must be true")
    if packet.get("candidate_status") != "draft_operator_notes_not_published":
        problems.append("candidate_status must keep release notes unpublished")

    source_packet_ids = packet.get("source_packet_ids") if isinstance(packet.get("source_packet_ids"), Mapping) else {}
    for key in ("offline_release_decision_packet", "dry_run_promotion_sequence_packet", "post_promotion_smoke_test_plan"):
        if not source_packet_ids.get(key):
            problems.append(f"source_packet_ids.{key} is required")

    policy = packet.get("publication_policy") if isinstance(packet.get("publication_policy"), Mapping) else {}
    if policy.get("fixtures_only") is not True:
        problems.append("publication_policy.fixtures_only must be true")
    for key in sorted(_FALSE_POLICY_KEYS):
        if policy.get(key) is not False:
            problems.append(f"publication_policy.{key} must be false")

    for key in _REQUIRED_LISTS:
        if not isinstance(packet.get(key), list) or not packet.get(key):
            problems.append(f"{key} must be a non-empty list")

    for key in ("operator_facing_change_notes", "known_limitations", "rollback_notes", "manual_handoff_reminders"):
        for index, item in enumerate(_mapping_sequence(packet.get(key))):
            if not _string_list(item.get("source_evidence_ids")):
                problems.append(f"{key}[{index}] lacks source_evidence_ids")
            if not _string_list(item.get("source_packet_refs")):
                problems.append(f"{key}[{index}] lacks source_packet_refs")

    for index, item in enumerate(_mapping_sequence(packet.get("operator_facing_change_notes"))):
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"operator_facing_change_notes[{index}] contains an uncited change claim")

    for index, item in enumerate(_mapping_sequence(packet.get("validation_evidence_references"))):
        if not item.get("reference_id"):
            problems.append(f"validation_evidence_references[{index}] lacks reference_id")
        if not item.get("source_packet_ref"):
            problems.append(f"validation_evidence_references[{index}] lacks source_packet_ref")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"validation_evidence_references[{index}] lacks source_evidence_ids")

    for index, item in enumerate(_mapping_sequence(packet.get("no_publication_attestations"))):
        if item.get("attested") is not True:
            problems.append(f"no_publication_attestations[{index}] must be attested")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"no_publication_attestations[{index}] lacks source_evidence_ids")

    problems.extend(_recursive_safety_problems(packet))
    return ReleaseNotesCandidateValidationResult(valid=not problems, problems=tuple(_dedupe(problems)))


def assert_valid_release_notes_candidate_packet(packet: Mapping[str, Any]) -> None:
    result = validate_release_notes_candidate_packet(packet)
    if not result.valid:
        raise ValueError("invalid_release_notes_candidate_packet: " + "; ".join(result.problems))


def _require_valid_sources(offline_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], smoke_plan: Mapping[str, Any]) -> None:
    offline_result = validate_offline_release_decision_packet(offline_packet)
    if not offline_result.valid:
        raise ValueError("invalid_source_offline_release_decision_packet: " + "; ".join(offline_result.problems))
    dry_run_result = validate_dry_run_promotion_sequence_packet(dry_run_packet)
    if not dry_run_result.valid:
        raise ValueError("invalid_source_dry_run_promotion_sequence_packet: " + "; ".join(dry_run_result.problems))
    smoke_result = validate_post_promotion_smoke_test_plan(smoke_plan)
    if not smoke_result.valid:
        raise ValueError("invalid_source_post_promotion_smoke_test_plan: " + "; ".join(smoke_result.problems))

    offline_packet_id = _packet_id(offline_packet, "offline-release-decision-packet")
    if str(dry_run_packet.get("source_packet_id") or "") != offline_packet_id:
        raise ValueError("dry_run_promotion_sequence_packet must cite the offline release decision packet")
    smoke_source_ids = smoke_plan.get("source_packet_ids") if isinstance(smoke_plan.get("source_packet_ids"), Mapping) else {}
    if str(smoke_source_ids.get("dry_run_promotion_sequence_packet") or "") != _packet_id(dry_run_packet, "dry-run-promotion-sequence-packet"):
        raise ValueError("post_promotion_smoke_test_plan must cite the dry-run promotion sequence packet")


def _change_notes(offline_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], smoke_plan: Mapping[str, Any], evidence_ids: list[str]) -> list[dict[str, Any]]:
    recommendations = [str(item.get("decision")) for item in _mapping_sequence(offline_packet.get("recommendations")) if item.get("decision")]
    sequence_status = str(dry_run_packet.get("sequence_status") or "unknown")
    smoke_case_count = len(_mapping_sequence(smoke_plan.get("synthetic_read_only_smoke_cases")))
    return [
        {
            "note_id": "change-note-release-decision",
            "title": "Offline release decision remains operator-gated",
            "body": f"The release decision packet reports {', '.join(recommendations) or 'no recommendation'} and must be reviewed before any release claim.",
            "source_packet_refs": ["offline_release_decision_packet"],
            "source_evidence_ids": _packet_evidence_ids(offline_packet) or evidence_ids,
        },
        {
            "note_id": "change-note-dry-run-sequence",
            "title": "Promotion sequence is synthetic",
            "body": f"The promotion sequence status is {sequence_status}; ordered steps are review instructions only and declare no active-state writes.",
            "source_packet_refs": ["dry_run_promotion_sequence_packet"],
            "source_evidence_ids": _packet_evidence_ids(dry_run_packet) or evidence_ids,
        },
        {
            "note_id": "change-note-smoke-plan",
            "title": "Post-promotion checks are fixture-only",
            "body": f"The smoke-test plan contains {smoke_case_count} cited read-only fixture cases and no agent, DevHub, crawler, processor, or compiler invocation.",
            "source_packet_refs": ["post_promotion_smoke_test_plan"],
            "source_evidence_ids": _packet_evidence_ids(smoke_plan) or evidence_ids,
        },
    ]


def _known_limitations(offline_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], smoke_plan: Mapping[str, Any], evidence_ids: list[str]) -> list[dict[str, Any]]:
    blockers = _mapping_sequence(offline_packet.get("unresolved_blocker_summaries"))
    abort_conditions = _mapping_sequence(dry_run_packet.get("abort_conditions"))
    refusal_checks = _mapping_sequence(smoke_plan.get("refusal_checks"))
    return [
        {
            "limitation_id": "limitation-unresolved-blockers",
            "summary": f"Unresolved blocker count: {len(blockers)}. Operators must treat blockers as release-note-visible caveats until separately resolved.",
            "source_packet_refs": ["offline_release_decision_packet"],
            "source_evidence_ids": _first_evidence(blockers, evidence_ids),
        },
        {
            "limitation_id": "limitation-abort-conditions",
            "summary": f"Dry-run promotion includes {len(abort_conditions)} abort condition(s); any matching condition stops the handoff before active PP&D state boundaries.",
            "source_packet_refs": ["dry_run_promotion_sequence_packet"],
            "source_evidence_ids": _first_evidence(abort_conditions, evidence_ids),
        },
        {
            "limitation_id": "limitation-consequential-actions-refused",
            "summary": f"Smoke-test expectations include {len(refusal_checks)} refusal check(s) for consequential or financial boundaries.",
            "source_packet_refs": ["post_promotion_smoke_test_plan"],
            "source_evidence_ids": _first_evidence(refusal_checks, evidence_ids),
        },
    ]


def _validation_evidence_references(offline_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], smoke_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for item in _mapping_sequence(offline_packet.get("validation_command_references")):
        references.append(
            {
                "reference_id": str(item.get("command_ref_id") or item.get("reference_id") or "offline-validation-command"),
                "source_packet_ref": "offline_release_decision_packet",
                "description": str(item.get("summary") or item.get("command") or "Offline release decision validation evidence."),
                "source_evidence_ids": _evidence_ids(item),
            }
        )
    for item in _mapping_sequence(dry_run_packet.get("prerequisite_validation_evidence")):
        references.append(
            {
                "reference_id": str(item.get("prerequisite_id") or "dry-run-prerequisite"),
                "source_packet_ref": "dry_run_promotion_sequence_packet",
                "description": str(item.get("summary") or item.get("status") or "Dry-run prerequisite evidence."),
                "source_evidence_ids": _evidence_ids(item),
            }
        )
    for item in _mapping_sequence(smoke_plan.get("expected_citation_coverage")):
        references.append(
            {
                "reference_id": str(item.get("coverage_id") or "smoke-citation-coverage"),
                "source_packet_ref": "post_promotion_smoke_test_plan",
                "description": "Smoke-test expected answer citation coverage.",
                "source_evidence_ids": _string_list(item.get("required_source_evidence_ids")),
            }
        )
    return [item for item in _dedupe_dicts(references) if item["source_evidence_ids"]]


def _rollback_notes(offline_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], evidence_ids: list[str]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for item in _mapping_sequence(offline_packet.get("rollback_checkpoints")):
        notes.append(
            {
                "rollback_note_id": str(item.get("checkpoint_id") or "offline-rollback-checkpoint"),
                "summary": str(item.get("checkpoint") or "Keep active PP&D artifacts unchanged."),
                "source_packet_refs": ["offline_release_decision_packet"],
                "source_evidence_ids": _evidence_ids(item) or evidence_ids,
            }
        )
    for item in _mapping_sequence(dry_run_packet.get("rollback_order")):
        notes.append(
            {
                "rollback_note_id": str(item.get("rollback_id") or "dry-run-rollback"),
                "summary": str(item.get("rollback_action") or "Discard synthetic release notes candidate packet."),
                "source_packet_refs": ["dry_run_promotion_sequence_packet"],
                "source_evidence_ids": _evidence_ids(item) or evidence_ids,
            }
        )
    return _dedupe_dicts(notes)


def _manual_handoff_reminders(offline_packet: Mapping[str, Any], dry_run_packet: Mapping[str, Any], smoke_plan: Mapping[str, Any], evidence_ids: list[str]) -> list[dict[str, Any]]:
    reminders: list[dict[str, Any]] = []
    for item in _mapping_sequence(offline_packet.get("operator_signoff_requests")):
        reminders.append(
            {
                "reminder_id": str(item.get("signoff_request_id") or item.get("role") or "operator-signoff"),
                "summary": str(item.get("request") or "Operator signoff is required before any release go claim."),
                "source_packet_refs": ["offline_release_decision_packet"],
                "source_evidence_ids": _evidence_ids(item) or evidence_ids,
            }
        )
    owner_ids = [str(owner.get("owner_id")) for owner in _mapping_sequence(dry_run_packet.get("reviewer_owners")) if owner.get("owner_id")]
    reminders.append(
        {
            "reminder_id": "manual-handoff-reviewer-owners",
            "summary": "Named reviewer owners must complete the handoff review: " + ", ".join(owner_ids or ["ppd-release-operator"]),
            "source_packet_refs": ["dry_run_promotion_sequence_packet"],
            "source_evidence_ids": _packet_evidence_ids(dry_run_packet) or evidence_ids,
        }
    )
    reminders.append(
        {
            "reminder_id": "manual-handoff-smoke-results",
            "summary": "Operators must review fixture smoke-test expectations and refusal checks manually; this packet does not execute consumers or DevHub workflows.",
            "source_packet_refs": ["post_promotion_smoke_test_plan"],
            "source_evidence_ids": _packet_evidence_ids(smoke_plan) or evidence_ids,
        }
    )
    return _dedupe_dicts(reminders)


def _recursive_safety_problems(value: Any) -> list[str]:
    problems: list[str] = []
    for path, child in _walk(value):
        if isinstance(child, str):
            if _PRIVATE_OR_RUNTIME_RE.search(child):
                problems.append(f"private or runtime artifact reference is not allowed at {path}")
            if _RAW_REFERENCE_RE.search(child):
                problems.append(f"raw crawl, download, or archive reference is not allowed at {path}")
            if _LIVE_OR_PUBLICATION_CLAIM_RE.search(child):
                problems.append(f"live execution, publication, or active mutation claim is not allowed at {path}")
            if _LEGAL_OR_PERMITTING_GUARANTEE_RE.search(child):
                problems.append(f"legal or permitting outcome guarantee is not allowed at {path}")
            if _is_private_or_authenticated_url(child):
                problems.append(f"private or authenticated URL is not allowed at {path}")
        elif isinstance(child, bool):
            key = _path_leaf(path)
            if child is True and key in _MUTATION_FLAG_KEYS:
                problems.append(f"active artifact mutation flag must not be true at {path}")
    return problems


def _is_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    lowered = value.lower()
    if host in _PRIVATE_URL_HOST_MARKERS or host.endswith(".local") or host.startswith("10.") or host.startswith("192.168."):
        return True
    return any(marker in lowered for marker in _AUTH_URL_MARKERS)


def _path_leaf(path: str) -> str:
    parts = [part for part in path.rstrip(".").split(".") if part and not part.isdigit()]
    return parts[-1] if parts else ""


def _walk(value: Any, path: str = "") -> list[tuple[str, Any]]:
    rows = [(path or "$", value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            rows.extend(_walk(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            child_path = f"{path}.{index}" if path else str(index)
            rows.extend(_walk(child, child_path))
    return rows


def _packet_id(packet: Mapping[str, Any], fallback: str) -> str:
    return str(packet.get("packet_id") or packet.get("plan_id") or fallback)


def _packet_evidence_ids(*packets: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for packet in packets:
        for _, child in _walk(packet):
            if isinstance(child, Mapping):
                values.extend(_evidence_ids(child))
    return _dedupe(values) or ["fixture-release-notes-candidate-evidence"]


def _first_evidence(items: list[Mapping[str, Any]], fallback: list[str]) -> list[str]:
    for item in items:
        evidence = _evidence_ids(item)
        if evidence:
            return evidence
    return fallback


def _evidence_ids(item: Mapping[str, Any]) -> list[str]:
    values = []
    for key in ("source_evidence_ids", "evidence_ids", "prerequisite_evidence_ids"):
        values.extend(_string_list(item.get(key)))
    return _dedupe(values)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item) for item in value if str(item)]
    return []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        marker = repr(sorted(item.items()))
        if marker not in seen:
            seen.add(marker)
            result.append(item)
    return result
