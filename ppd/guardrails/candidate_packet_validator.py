"""Validation for PP&D guardrail regeneration candidate packets.

The validator is intentionally deterministic and side-effect free. It accepts plain
Python dictionaries loaded from JSON/YAML fixtures and returns structured findings
instead of raising for policy failures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse


MAX_INPUT_MODEL_AGE_DAYS = 45

_PRIVATE_KEY_RE = re.compile(
    r"(^|_)(api[_-]?key|auth|credential|jwt|password|private|secret|session|token)(_|$)",
    re.IGNORECASE,
)
_PRIVATE_VALUE_RE = re.compile(
    r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{16,})",
    re.IGNORECASE,
)
_RAW_ARTIFACT_KEY_RE = re.compile(
    r"(^|_)(raw[_-]?body|body[_-]?path|download[_-]?path|archive[_-]?path|warc[_-]?path|raw[_-]?crawl|artifact[_-]?path|local[_-]?path)(_|$)",
    re.IGNORECASE,
)
_RAW_ARTIFACT_VALUE_RE = re.compile(
    r"(^(file|crawl|archive|warc)://|/(tmp|var/folders|private|home)/|\.warc(\.gz)?$|/raw/|/downloads?/|/archives?/)",
    re.IGNORECASE,
)
_CURRENT_STATUS_RE = re.compile(
    r"\b(current|currently|current-status|up[- ]to[- ]date|latest|as of today|present status)\b",
    re.IGNORECASE,
)

_PUBLIC_HOSTS = {
    "www.portland.gov",
    "portland.gov",
    "www.portlandoregon.gov",
    "devhub.portlandoregon.gov",
    "www.portlandmaps.com",
    "portlandmaps.com",
}


@dataclass(frozen=True)
class CandidatePacketFinding:
    """A deterministic validation failure for a candidate packet."""

    code: str
    path: str
    message: str


def validate_candidate_packet(
    packet: Mapping[str, Any],
    *,
    today: date | None = None,
    max_input_model_age_days: int = MAX_INPUT_MODEL_AGE_DAYS,
) -> list[CandidatePacketFinding]:
    """Return all policy findings for a guardrail regeneration candidate packet."""

    if today is None:
        today = datetime.now(timezone.utc).date()

    findings: list[CandidatePacketFinding] = []
    findings.extend(_validate_cited_predicates(packet))
    findings.extend(_validate_consequential_actions(packet))
    findings.extend(_validate_private_values(packet))
    findings.extend(_validate_raw_artifact_references(packet))
    findings.extend(_validate_input_models(packet, today, max_input_model_age_days))
    findings.extend(_validate_active_bundle_promotion(packet))
    findings.extend(_validate_regenerated_requirement_candidate(packet))
    return findings


def reject_candidate_packet(packet: Mapping[str, Any], *, today: date | None = None) -> None:
    """Raise ValueError when a packet has any validation findings."""

    findings = validate_candidate_packet(packet, today=today)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(details)


def _validate_cited_predicates(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    for index, predicate in enumerate(_as_sequence(packet.get("predicates"))):
        if not isinstance(predicate, Mapping):
            findings.append(
                CandidatePacketFinding(
                    "invalid_predicate",
                    f"predicates[{index}]",
                    "predicate entries must be objects",
                )
            )
            continue
        citations = _as_sequence(predicate.get("citations")) or _as_sequence(predicate.get("sources"))
        if not citations:
            findings.append(
                CandidatePacketFinding(
                    "uncited_predicate",
                    f"predicates[{index}]",
                    "predicate must include at least one citation or source",
                )
            )
    return findings


def _validate_consequential_actions(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    refusal_rules = _rule_ids(packet.get("refusal_rules"))
    confirmation_gates = _rule_ids(packet.get("exact_confirmation_gates")) | _rule_ids(packet.get("confirmation_gates"))

    for index, action in enumerate(_as_sequence(packet.get("actions"))):
        if not isinstance(action, Mapping):
            continue
        if not _is_consequential_action(action):
            continue

        action_id = str(action.get("id") or action.get("name") or index)
        action_path = f"actions[{index}]"
        action_refusal_rules = _rule_ids(action.get("refusal_rules"))
        action_confirmation_gates = _rule_ids(action.get("exact_confirmation_gates")) | _rule_ids(action.get("confirmation_gates"))

        if not (refusal_rules or action_refusal_rules):
            findings.append(
                CandidatePacketFinding(
                    "missing_refusal_rule",
                    action_path,
                    f"consequential action {action_id!r} must have refusal rules",
                )
            )

        has_gate = bool(confirmation_gates or action_confirmation_gates or action.get("exact_confirmation_required") is True)
        if not has_gate:
            findings.append(
                CandidatePacketFinding(
                    "missing_exact_confirmation_gate",
                    action_path,
                    f"consequential action {action_id!r} must require exact human confirmation",
                )
            )
    return findings


def _validate_private_values(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1]
        if _PRIVATE_KEY_RE.search(key):
            findings.append(
                CandidatePacketFinding(
                    "private_value",
                    path,
                    "candidate packet must not include private credential, token, secret, or session fields",
                )
            )
        elif isinstance(value, str) and _PRIVATE_VALUE_RE.search(value):
            findings.append(
                CandidatePacketFinding(
                    "private_value",
                    path,
                    "candidate packet must not include private credential-like values",
                )
            )
    return findings


def _validate_raw_artifact_references(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1]
        if _RAW_ARTIFACT_KEY_RE.search(key):
            findings.append(
                CandidatePacketFinding(
                    "raw_artifact_reference",
                    path,
                    "candidate packet must not include raw body, download, archive, WARC, or local artifact path fields",
                )
            )
        elif isinstance(value, str) and _RAW_ARTIFACT_VALUE_RE.search(value.strip()):
            findings.append(
                CandidatePacketFinding(
                    "raw_artifact_reference",
                    path,
                    "candidate packet must not include raw body, download, archive, WARC, or local artifact path values",
                )
            )
    return findings


def _validate_input_models(
    packet: Mapping[str, Any],
    today: date,
    max_input_model_age_days: int,
) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    for index, model in enumerate(_as_sequence(packet.get("input_models"))):
        if not isinstance(model, Mapping):
            findings.append(
                CandidatePacketFinding(
                    "invalid_input_model",
                    f"input_models[{index}]",
                    "input model entries must be objects",
                )
            )
            continue

        if model.get("stale") is True:
            findings.append(
                CandidatePacketFinding(
                    "stale_input_model",
                    f"input_models[{index}]",
                    "input model is explicitly marked stale",
                )
            )
            continue

        stamp = model.get("last_verified_at") or model.get("generated_at") or model.get("created_at")
        stamp_date = _parse_date(stamp)
        if stamp_date is None:
            findings.append(
                CandidatePacketFinding(
                    "stale_input_model",
                    f"input_models[{index}]",
                    "input model must include a parseable verification or generation date",
                )
            )
            continue

        age_days = (today - stamp_date).days
        if age_days > max_input_model_age_days:
            findings.append(
                CandidatePacketFinding(
                    "stale_input_model",
                    f"input_models[{index}]",
                    f"input model is {age_days} days old; maximum is {max_input_model_age_days}",
                )
            )
    return findings


def _validate_active_bundle_promotion(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    promotion = packet.get("promotion") or packet.get("bundle_promotion")
    if not isinstance(promotion, Mapping):
        return []

    target = str(promotion.get("target") or promotion.get("status") or "").lower()
    promotes_active = target in {"active", "active_bundle", "current"} or promotion.get("promote_to_active") is True
    if not promotes_active:
        return []

    review = promotion.get("human_review") or packet.get("human_review")
    approved = isinstance(review, Mapping) and review.get("approved") is True and bool(review.get("reviewer"))
    if approved:
        return []

    return [
        CandidatePacketFinding(
            "active_bundle_promotion_requires_review",
            "promotion",
            "active-bundle promotion is forbidden before explicit human review approval",
        )
    ]


def _validate_regenerated_requirement_candidate(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    if not _is_regenerated_requirement_candidate(packet):
        return []

    findings: list[CandidatePacketFinding] = []
    findings.extend(_validate_requirement_diffs(packet))
    findings.extend(_validate_public_evidence(packet))
    findings.extend(_validate_current_status_claims(packet))
    findings.extend(_validate_affected_links(packet))
    findings.extend(_validate_no_active_bundle_mutation(packet))
    return findings


def _validate_requirement_diffs(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    diffs = _as_sequence(packet.get("requirement_diffs") or packet.get("diffs"))
    if not diffs:
        return [
            CandidatePacketFinding(
                "missing_requirement_diffs",
                "requirement_diffs",
                "regenerated requirement candidate packets must include requirement diffs",
            )
        ]

    for index, diff in enumerate(diffs):
        path = f"requirement_diffs[{index}]"
        if not isinstance(diff, Mapping):
            findings.append(CandidatePacketFinding("invalid_requirement_diff", path, "requirement diff entries must be objects"))
            continue
        if not _has_any(diff, ("old_requirement_id", "previous_requirement_id", "from_requirement_id")):
            findings.append(
                CandidatePacketFinding(
                    "missing_old_requirement_id",
                    path,
                    "requirement diffs must include the old requirement ID",
                )
            )
        if not _has_any(diff, ("new_requirement_id", "regenerated_requirement_id", "to_requirement_id")):
            findings.append(
                CandidatePacketFinding(
                    "missing_new_requirement_id",
                    path,
                    "requirement diffs must include the new requirement ID",
                )
            )
        if not _citations(diff):
            findings.append(
                CandidatePacketFinding(
                    "uncited_requirement_diff",
                    path,
                    "requirement diffs must include citation-backed evidence",
                )
            )
    return findings


def _validate_public_evidence(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    evidence_items = list(_evidence_items(packet))
    for path, evidence in evidence_items:
        if not isinstance(evidence, Mapping):
            continue
        auth_scope = str(evidence.get("auth_scope") or evidence.get("access_scope") or "").lower()
        source_type = str(evidence.get("source_type") or evidence.get("type") or "").lower()
        privacy = str(evidence.get("privacy_classification") or evidence.get("privacy") or "").lower()
        url = str(evidence.get("url") or evidence.get("canonical_url") or evidence.get("source_url") or "")
        if auth_scope in {"authenticated", "private", "account", "user_account"}:
            findings.append(CandidatePacketFinding("private_or_authenticated_evidence", path, "evidence must be public and unauthenticated"))
            continue
        if source_type in {"devhub_authenticated", "private", "authenticated"}:
            findings.append(CandidatePacketFinding("private_or_authenticated_evidence", path, "evidence must not reference authenticated source types"))
            continue
        if privacy and privacy not in {"public", "public_guidance", "public_metadata"}:
            findings.append(CandidatePacketFinding("private_or_authenticated_evidence", path, "evidence privacy classification must be public"))
            continue
        if url and not _is_public_url(url):
            findings.append(CandidatePacketFinding("private_or_authenticated_evidence", path, "evidence URL must be an official public PP&D source"))
    return findings


def _validate_current_status_claims(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    if _has_reviewer_review(packet):
        return []

    findings: list[CandidatePacketFinding] = []
    for path, value in _walk(packet):
        if not isinstance(value, str):
            continue
        if _CURRENT_STATUS_RE.search(value):
            findings.append(
                CandidatePacketFinding(
                    "current_status_claim_requires_reviewer_review",
                    path,
                    "current-status claims require explicit reviewer review before the candidate can be accepted",
                )
            )
    return findings


def _validate_affected_links(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    process_links = packet.get("affected_process_ids") or packet.get("affected_process_links") or packet.get("process_model_ids")
    guardrail_links = packet.get("affected_guardrail_bundle_ids") or packet.get("affected_guardrail_links") or packet.get("guardrail_bundle_ids")
    if not _nonempty_sequence(process_links):
        findings.append(
            CandidatePacketFinding(
                "missing_affected_process_links",
                "affected_process_ids",
                "regenerated requirement candidates must identify affected process links",
            )
        )
    if not _nonempty_sequence(guardrail_links):
        findings.append(
            CandidatePacketFinding(
                "missing_affected_guardrail_links",
                "affected_guardrail_bundle_ids",
                "regenerated requirement candidates must identify affected guardrail bundle links",
            )
        )
    return findings


def _validate_no_active_bundle_mutation(packet: Mapping[str, Any]) -> list[CandidatePacketFinding]:
    findings: list[CandidatePacketFinding] = []
    if packet.get("does_not_replace_active_bundle") is False:
        findings.append(
            CandidatePacketFinding(
                "active_bundle_mutation",
                "does_not_replace_active_bundle",
                "regenerated candidates must not replace or mutate active guardrail bundles",
            )
        )
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].lower()
        if key in {"mutates_active_bundle", "replace_active_bundle", "replaces_active_bundle"} and value is True:
            findings.append(CandidatePacketFinding("active_bundle_mutation", path, "active-bundle mutation is forbidden in regenerated candidates"))
        if key in {"target_bundle_status", "bundle_status", "target"} and str(value).lower() in {"active", "active_bundle", "current"}:
            findings.append(CandidatePacketFinding("active_bundle_mutation", path, "regenerated candidates must target review candidates, not active bundles"))
    return findings


def _is_regenerated_requirement_candidate(packet: Mapping[str, Any]) -> bool:
    marker = str(packet.get("packet_type") or packet.get("candidate_kind") or packet.get("type") or "").lower()
    if marker in {"regenerated_requirement_candidate", "requirement_regeneration_candidate", "regenerated_requirement_packet"}:
        return True
    return "requirement_diffs" in packet or "diffs" in packet


def _citations(value: Mapping[str, Any]) -> Sequence[Any]:
    return (
        _as_sequence(value.get("citations"))
        or _as_sequence(value.get("source_evidence"))
        or _as_sequence(value.get("source_evidence_ids"))
        or _as_sequence(value.get("evidence"))
    )


def _evidence_items(packet: Mapping[str, Any]) -> Iterable[tuple[str, Any]]:
    for key in ("evidence", "source_evidence", "citations"):
        for index, item in enumerate(_as_sequence(packet.get(key))):
            yield f"{key}[{index}]", item
    for diff_index, diff in enumerate(_as_sequence(packet.get("requirement_diffs") or packet.get("diffs"))):
        if not isinstance(diff, Mapping):
            continue
        for key in ("evidence", "source_evidence", "citations"):
            for evidence_index, item in enumerate(_as_sequence(diff.get(key))):
                yield f"requirement_diffs[{diff_index}].{key}[{evidence_index}]", item


def _is_public_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.hostname not in _PUBLIC_HOSTS:
        return False
    path = parsed.path.lower()
    private_markers = ("/login", "/signin", "/account", "/my-", "/secure", "/session", "/admin")
    return not any(marker in path for marker in private_markers)


def _has_reviewer_review(packet: Mapping[str, Any]) -> bool:
    review = packet.get("reviewer_review") or packet.get("human_review") or packet.get("review")
    if not isinstance(review, Mapping):
        return False
    return review.get("approved") is True and bool(review.get("reviewer") or review.get("reviewer_id"))


def _has_any(value: Mapping[str, Any], keys: Sequence[str]) -> bool:
    return any(bool(value.get(key)) for key in keys)


def _nonempty_sequence(value: Any) -> bool:
    return any(bool(item) for item in _as_sequence(value))


def _is_consequential_action(action: Mapping[str, Any]) -> bool:
    if action.get("consequential") is True:
        return True
    action_type = str(action.get("type") or action.get("risk") or "").lower()
    return action_type in {"consequential", "submit", "submission", "certify", "cancel", "payment", "upload"}


def _rule_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    for item in _as_sequence(value):
        if isinstance(item, Mapping):
            rule_id = item.get("id") or item.get("name")
            if rule_id:
                ids.add(str(rule_id))
        elif item:
            ids.add(str(item))
    return ids


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return [value]


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, child
            yield from _walk(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, child_path)
