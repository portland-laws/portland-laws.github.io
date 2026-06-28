"""Validation for PP&D release readiness snapshots.

The validator is intentionally schema-tolerant because release snapshots are
assembled from multiple PP&D subsystems.  It accepts plain mappings and checks
for the release-blocking conditions that must never pass unnoticed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any, Iterable, Mapping, Sequence


_CONSEQUENTIAL_PATH_TERMS = {
    "live_crawl": ("live_crawl", "live crawl", "crawl_live", "liveCrawl"),
    "devhub": ("devhub", "dev_hub", "DevHub"),
    "payment": ("payment", "pay_fee", "fee_payment", "submit_payment"),
    "upload": ("upload", "attachment_upload", "correction_upload"),
    "submission": ("submission", "submit", "submit_permit", "permit_submit"),
    "scheduling": ("scheduling", "schedule", "inspection_schedule"),
    "cancellation": ("cancellation", "cancel", "withdraw"),
    "certification": ("certification", "certify", "acknowledgement", "attestation"),
}

_PRIVATE_OR_SESSION_RE = re.compile(
    r"(cookie|cookies|credential|secret|password|token|auth[_-]?state|"
    r"storage[_-]?state|session|playwright.*state|\.har\b|trace\.zip|"
    r"screenshot|screenshots|private[_-]?devhub|payment[_-]?detail)",
    re.IGNORECASE,
)

_RAW_CRAWL_RE = re.compile(
    r"(raw[_-]?crawl|crawl[_-]?output|raw[_-]?html|raw[_-]?body|warc|"
    r"downloaded[_-]?documents|page[_-]?dump|browser[_-]?dump|response[_-]?body)",
    re.IGNORECASE,
)

_PRODUCTION_READY_LABELS = {
    "production-ready",
    "production_ready",
    "production ready",
    "prod-ready",
    "prod_ready",
    "ready for production",
    "release-ready",
    "release_ready",
    "release ready",
}

_PREREQUISITE_KEYS = (
    "prerequisite_packets",
    "prerequisitePackets",
    "prerequisites",
    "required_packets",
    "requiredPackets",
)

_CLAIM_KEYS = (
    "readiness_claims",
    "readinessClaims",
    "claims",
    "assertions",
)

_LINK_KEYS = (
    "link",
    "url",
    "href",
    "packet_link",
    "packetLink",
    "source_link",
    "sourceLink",
    "citation_url",
    "citationUrl",
)

_CITATION_KEYS = (
    "citation",
    "citations",
    "evidence",
    "evidence_refs",
    "evidenceRefs",
    "source_evidence_ids",
    "sourceEvidenceIds",
    "source_refs",
    "sourceRefs",
    "sources",
)

_BLOCKER_KEYS = (
    "unresolved_blockers",
    "unresolvedBlockers",
    "blockers",
    "open_blockers",
    "openBlockers",
    "known_blockers",
    "knownBlockers",
)

_LABEL_KEYS = (
    "label",
    "labels",
    "readiness_label",
    "readinessLabel",
    "status",
    "release_status",
    "releaseStatus",
)

_ENABLED_KEYS = {"enabled", "active", "allowed", "available"}
_DISABLED_VALUES = {"disabled", "blocked", "refused", "manual_only", "manual-only", "dry_run", "dry-run", "false", "off"}
_ENABLED_VALUES = {"enabled", "active", "allowed", "available", "true", "on", "live"}


@dataclass(frozen=True)
class ReadinessValidationError:
    """A release-readiness validation failure."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ReadinessValidationResult:
    """Validation result for a release readiness snapshot."""

    errors: tuple[ReadinessValidationError, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def messages(self) -> tuple[str, ...]:
        return tuple(f"{error.path}: {error.message}" for error in self.errors)


def load_release_readiness_snapshot(path: str | Path) -> Mapping[str, Any]:
    """Load a JSON readiness snapshot from disk without permitting side effects."""

    snapshot_path = Path(path)
    with snapshot_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError("release readiness snapshot must be a JSON object")
    return data


def validate_release_readiness_snapshot(snapshot: Mapping[str, Any]) -> ReadinessValidationResult:
    """Return every blocking validation error for a readiness snapshot."""

    errors: list[ReadinessValidationError] = []
    errors.extend(_validate_prerequisite_packet_links(snapshot))
    errors.extend(_validate_readiness_claim_citations(snapshot))
    errors.extend(_validate_reference_patterns(snapshot))
    errors.extend(_validate_production_ready_blockers(snapshot))
    errors.extend(_validate_enabled_consequential_paths(snapshot))
    return ReadinessValidationResult(tuple(errors))


def assert_release_readiness_snapshot(snapshot: Mapping[str, Any]) -> None:
    """Raise ValueError when a release readiness snapshot is not acceptable."""

    result = validate_release_readiness_snapshot(snapshot)
    if not result.ok:
        raise ValueError("; ".join(result.messages()))


def _validate_prerequisite_packet_links(snapshot: Mapping[str, Any]) -> list[ReadinessValidationError]:
    errors: list[ReadinessValidationError] = []
    for key in _PREREQUISITE_KEYS:
        if key not in snapshot:
            continue
        packets = _as_sequence(snapshot[key])
        if not packets:
            errors.append(
                ReadinessValidationError(
                    "missing_prerequisite_packet_link",
                    key,
                    "prerequisite packet list is empty or not a list",
                )
            )
            continue
        for index, packet in enumerate(packets):
            packet_path = f"{key}[{index}]"
            if not _has_any_value(packet, _LINK_KEYS):
                errors.append(
                    ReadinessValidationError(
                        "missing_prerequisite_packet_link",
                        packet_path,
                        "prerequisite packet must include a stable packet/source link",
                    )
                )
    return errors


def _validate_readiness_claim_citations(snapshot: Mapping[str, Any]) -> list[ReadinessValidationError]:
    errors: list[ReadinessValidationError] = []
    for claim_path, claim in _iter_claims(snapshot):
        if isinstance(claim, str):
            errors.append(
                ReadinessValidationError(
                    "uncited_readiness_claim",
                    claim_path,
                    "readiness claim is plain text and has no citation evidence",
                )
            )
            continue
        if not _has_any_value(claim, _CITATION_KEYS):
            errors.append(
                ReadinessValidationError(
                    "uncited_readiness_claim",
                    claim_path,
                    "readiness claim must cite source evidence",
                )
            )
    return errors


def _validate_reference_patterns(snapshot: Mapping[str, Any]) -> list[ReadinessValidationError]:
    errors: list[ReadinessValidationError] = []
    for path, value in _walk(snapshot):
        text = f"{path} {value}" if isinstance(value, str) else path
        if _PRIVATE_OR_SESSION_RE.search(text):
            errors.append(
                ReadinessValidationError(
                    "private_or_session_artifact",
                    path,
                    "snapshot must not reference private DevHub, session, auth, trace, HAR, screenshot, credential, or payment artifacts",
                )
            )
        if _RAW_CRAWL_RE.search(text):
            errors.append(
                ReadinessValidationError(
                    "raw_crawl_output_reference",
                    path,
                    "snapshot must reference normalized manifests or citations, not raw crawl output",
                )
            )
    return errors


def _validate_production_ready_blockers(snapshot: Mapping[str, Any]) -> list[ReadinessValidationError]:
    if not _has_production_ready_label(snapshot):
        return []
    blockers = _collect_blockers(snapshot)
    if not blockers:
        return []
    return [
        ReadinessValidationError(
            "production_ready_with_unresolved_blockers",
            "release_status",
            "production-ready or release-ready labels are not allowed while unresolved blockers remain",
        )
    ]


def _validate_enabled_consequential_paths(snapshot: Mapping[str, Any]) -> list[ReadinessValidationError]:
    errors: list[ReadinessValidationError] = []
    for path, value in _walk(snapshot):
        matched = _matched_consequential_term(path)
        if matched and _is_enabled_node(value):
            errors.append(
                ReadinessValidationError(
                    "enabled_consequential_path",
                    path,
                    f"{matched} path must not be enabled in a release readiness snapshot",
                )
            )
        if isinstance(value, str):
            matched_value = _matched_consequential_term(value)
            if matched_value and _looks_enabled_string(value):
                errors.append(
                    ReadinessValidationError(
                        "enabled_consequential_path",
                        path,
                        f"{matched_value} path must not be described as enabled",
                    )
                )
    return errors


def _iter_claims(snapshot: Mapping[str, Any]) -> Iterable[tuple[str, Any]]:
    for path, value in _walk(snapshot):
        key = path.rsplit(".", 1)[-1]
        if key not in _CLAIM_KEYS:
            continue
        claims = _as_sequence(value)
        if not claims:
            yield path, value
            continue
        for index, claim in enumerate(claims):
            yield f"{path}[{index}]", claim


def _walk(value: Any, path: str = "$root") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _has_any_value(value: Any, keys: Sequence[str]) -> bool:
    if not isinstance(value, Mapping):
        return False
    for key in keys:
        candidate = value.get(key)
        if candidate is None:
            continue
        if isinstance(candidate, str) and candidate.strip():
            return True
        if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes, bytearray)) and len(candidate) > 0:
            return True
        if isinstance(candidate, Mapping) and len(candidate) > 0:
            return True
    return False


def _has_production_ready_label(snapshot: Mapping[str, Any]) -> bool:
    for path, value in _walk(snapshot):
        key = path.rsplit(".", 1)[-1]
        if key not in _LABEL_KEYS:
            continue
        values = value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else (value,)
        for item in values:
            if isinstance(item, str) and item.strip().lower() in _PRODUCTION_READY_LABELS:
                return True
    return False


def _collect_blockers(snapshot: Mapping[str, Any]) -> tuple[Any, ...]:
    blockers: list[Any] = []
    for path, value in _walk(snapshot):
        key = path.rsplit(".", 1)[-1]
        if key not in _BLOCKER_KEYS:
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            blockers.extend(item for item in value if item)
        elif value:
            blockers.append(value)
    return tuple(blockers)


def _matched_consequential_term(text: str) -> str | None:
    normalized = text.lower().replace("-", "_")
    for label, terms in _CONSEQUENTIAL_PATH_TERMS.items():
        for term in terms:
            if term.lower().replace("-", "_") in normalized:
                return label
    return None


def _is_enabled_node(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _ENABLED_VALUES
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in _ENABLED_KEYS and _truthy_enabled_value(child):
                return True
            if normalized_key in {"mode", "status", "state"} and isinstance(child, str):
                lowered = child.strip().lower()
                if lowered in _ENABLED_VALUES and lowered not in _DISABLED_VALUES:
                    return True
        return False
    return False


def _truthy_enabled_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        return lowered in _ENABLED_VALUES and lowered not in _DISABLED_VALUES
    return bool(value)


def _looks_enabled_string(value: str) -> bool:
    lowered = value.strip().lower()
    return any(token in lowered for token in _ENABLED_VALUES) and not any(
        token in lowered for token in _DISABLED_VALUES
    )
