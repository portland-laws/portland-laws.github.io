"""Validation for offline requirement extraction delta packet v1.

The packet is intentionally narrow: it is a deterministic review artifact, not a
live crawl, DevHub automation result, or official-action completion record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


class RequirementExtractionDeltaPacketV1Error(ValueError):
    """Raised when a requirement extraction delta packet is incomplete or unsafe."""


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


REQUIRED_CANDIDATE_GROUPS = ("add", "change", "remove")

PRIVATE_ARTIFACT_KEYWORDS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "download_path",
    "downloaded_artifact",
    "har",
    "local_private_path",
    "playwright_trace",
    "private_artifact",
    "raw_body",
    "raw_download",
    "raw_html",
    "screenshot",
    "session_file",
    "session_state",
    "trace_zip",
)

PRIVATE_ARTIFACT_VALUE_MARKERS = (
    ".har",
    "trace.zip",
    "storage_state.json",
    "auth-state",
    "browser-state",
    "downloaded/",
    "/downloads/",
    "/private/",
    "/session/",
    "raw-crawl-output",
    "raw_body",
    "raw_html",
)

LIVE_OR_DEVHUB_CLAIM_MARKERS = (
    "authenticated devhub",
    "devhub login",
    "devhub session",
    "live crawl",
    "live devhub",
    "observed in devhub",
    "queried devhub",
    "ran playwright",
    "real browser session",
)

GUARANTEE_MARKERS = (
    "guarantee",
    "guaranteed",
    "legal advice",
    "legally sufficient",
    "permit approval is assured",
    "permit is guaranteed",
    "permit will be approved",
    "permit will be issued",
    "will pass inspection",
)

OFFICIAL_ACTION_COMPLETION_MARKERS = (
    "cancelled the permit",
    "certified the application",
    "completed official action",
    "inspection scheduled",
    "paid the fee",
    "payment submitted",
    "permit submitted",
    "scheduled inspection",
    "submitted application",
    "submitted the permit",
    "uploaded correction",
    "uploaded to devhub",
)

ACTIVE_MUTATION_KEYS = (
    "active_mutation",
    "active_mutation_enabled",
    "allow_live_mutation",
    "live_mutation_enabled",
    "mutates_live_state",
    "official_action_enabled",
    "writes_to_devhub",
)


_REQUIRED_TOP_LEVEL = (
    "candidate_rows",
    "source_evidence_refs",
    "confidence_rows",
    "human_review_status",
    "stale_evidence_impact_rows",
    "validation_commands",
)


def validate_requirement_extraction_delta_packet_v1(packet: Mapping[str, Any]) -> None:
    """Validate that a requirement extraction delta packet is complete and safe.

    Raises RequirementExtractionDeltaPacketV1Error with all detected issues when
    the packet is incomplete or contains disallowed claims/artifact references.
    """

    issues = list(iter_requirement_extraction_delta_packet_v1_issues(packet))
    if issues:
        detail = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise RequirementExtractionDeltaPacketV1Error(detail)


def iter_requirement_extraction_delta_packet_v1_issues(packet: Mapping[str, Any]) -> Iterable[ValidationIssue]:
    if not isinstance(packet, Mapping):
        yield ValidationIssue("$", "packet must be a mapping")
        return

    for key in _REQUIRED_TOP_LEVEL:
        if key not in packet:
            yield ValidationIssue(key, "missing required field")

    candidate_rows = packet.get("candidate_rows")
    if isinstance(candidate_rows, Mapping):
        for group in REQUIRED_CANDIDATE_GROUPS:
            rows = candidate_rows.get(group)
            if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
                yield ValidationIssue(f"candidate_rows.{group}", "must contain at least one candidate row")
            else:
                for index, row in enumerate(rows):
                    yield from _candidate_row_issues(row, f"candidate_rows.{group}[{index}]")
    elif "candidate_rows" in packet:
        yield ValidationIssue("candidate_rows", "must be a mapping with add, change, and remove rows")

    source_evidence_refs = packet.get("source_evidence_refs")
    evidence_ids: set[str] = set()
    if isinstance(source_evidence_refs, Sequence) and not isinstance(source_evidence_refs, (str, bytes)) and source_evidence_refs:
        for index, row in enumerate(source_evidence_refs):
            row_path = f"source_evidence_refs[{index}]"
            if not isinstance(row, Mapping):
                yield ValidationIssue(row_path, "must be a mapping")
                continue
            evidence_id = row.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                yield ValidationIssue(f"{row_path}.evidence_id", "missing source evidence reference id")
            else:
                evidence_ids.add(evidence_id)
            citation = row.get("citation") or row.get("source_url")
            if not isinstance(citation, str) or not citation.strip():
                yield ValidationIssue(f"{row_path}.citation", "missing source citation")
    elif "source_evidence_refs" in packet:
        yield ValidationIssue("source_evidence_refs", "must contain at least one source evidence reference")

    confidence_ids = _ids_from_rows(packet.get("confidence_rows"), "confidence_id")
    if confidence_ids is None:
        if "confidence_rows" in packet:
            yield ValidationIssue("confidence_rows", "must contain confidence rows with confidence_id")
        confidence_ids = set()

    stale_ids = _ids_from_rows(packet.get("stale_evidence_impact_rows"), "impact_id")
    if stale_ids is None:
        if "stale_evidence_impact_rows" in packet:
            yield ValidationIssue("stale_evidence_impact_rows", "must contain stale-evidence impact rows with impact_id")
        stale_ids = set()

    human_review_status = packet.get("human_review_status")
    if not isinstance(human_review_status, str) or not human_review_status.strip():
        if "human_review_status" in packet:
            yield ValidationIssue("human_review_status", "missing human-review status")

    validation_commands = packet.get("validation_commands")
    if not _valid_validation_commands(validation_commands):
        if "validation_commands" in packet:
            yield ValidationIssue("validation_commands", "must contain at least one validation command as a list of strings")

    if isinstance(candidate_rows, Mapping):
        for group in REQUIRED_CANDIDATE_GROUPS:
            rows = candidate_rows.get(group)
            if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
                continue
            for index, row in enumerate(rows):
                if not isinstance(row, Mapping):
                    continue
                row_path = f"candidate_rows.{group}[{index}]"
                for evidence_id in _string_list(row.get("source_evidence_ids")):
                    if evidence_ids and evidence_id not in evidence_ids:
                        yield ValidationIssue(f"{row_path}.source_evidence_ids", f"unknown source evidence id: {evidence_id}")
                confidence_id = row.get("confidence_id")
                if isinstance(confidence_id, str) and confidence_ids and confidence_id not in confidence_ids:
                    yield ValidationIssue(f"{row_path}.confidence_id", f"unknown confidence id: {confidence_id}")
                impact_id = row.get("stale_evidence_impact_id")
                if isinstance(impact_id, str) and stale_ids and impact_id not in stale_ids:
                    yield ValidationIssue(f"{row_path}.stale_evidence_impact_id", f"unknown stale-evidence impact id: {impact_id}")

    yield from _safety_issues(packet, "$.")


def _candidate_row_issues(row: Any, path: str) -> Iterable[ValidationIssue]:
    if not isinstance(row, Mapping):
        yield ValidationIssue(path, "candidate row must be a mapping")
        return
    if not isinstance(row.get("requirement_id"), str) or not row.get("requirement_id", "").strip():
        yield ValidationIssue(f"{path}.requirement_id", "missing requirement id")
    if not _string_list(row.get("source_evidence_ids")):
        yield ValidationIssue(f"{path}.source_evidence_ids", "missing source evidence references")
    if not isinstance(row.get("confidence_id"), str) or not row.get("confidence_id", "").strip():
        yield ValidationIssue(f"{path}.confidence_id", "missing confidence row reference")
    if not isinstance(row.get("human_review_status"), str) or not row.get("human_review_status", "").strip():
        yield ValidationIssue(f"{path}.human_review_status", "missing human-review status")
    if not isinstance(row.get("stale_evidence_impact_id"), str) or not row.get("stale_evidence_impact_id", "").strip():
        yield ValidationIssue(f"{path}.stale_evidence_impact_id", "missing stale-evidence impact row reference")


def _ids_from_rows(rows: Any, id_field: str) -> set[str] | None:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        return None
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            return None
        value = row.get(id_field)
        if not isinstance(value, str) or not value.strip():
            return None
        ids.add(value)
    return ids


def _valid_validation_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)) or not command:
            return False
        if not all(isinstance(part, str) and part.strip() for part in command):
            return False
    return True


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item)
    return result


def _safety_issues(value: Any, path: str) -> Iterable[ValidationIssue]:
    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key)
            key_lower = key.lower()
            nested_path = f"{path}{key}"
            if any(marker in key_lower for marker in PRIVATE_ARTIFACT_KEYWORDS):
                yield ValidationIssue(nested_path, "private/session/browser/raw/downloaded artifact fields are not allowed")
            if key_lower in ACTIVE_MUTATION_KEYS and bool(nested_value):
                yield ValidationIssue(nested_path, "active mutation flags are not allowed")
            yield from _safety_issues(nested_value, f"{nested_path}.")
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            yield from _safety_issues(item, f"{path}[{index}].")
        return

    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PRIVATE_ARTIFACT_VALUE_MARKERS):
            yield ValidationIssue(path.rstrip("."), "private/session/browser/raw/downloaded artifact references are not allowed")
        if any(marker in lowered for marker in LIVE_OR_DEVHUB_CLAIM_MARKERS):
            yield ValidationIssue(path.rstrip("."), "live crawl or DevHub claims are not allowed")
        if any(marker in lowered for marker in GUARANTEE_MARKERS):
            yield ValidationIssue(path.rstrip("."), "legal or permitting guarantees are not allowed")
        if any(marker in lowered for marker in OFFICIAL_ACTION_COMPLETION_MARKERS):
            yield ValidationIssue(path.rstrip("."), "official-action completion claims are not allowed")


__all__ = [
    "RequirementExtractionDeltaPacketV1Error",
    "ValidationIssue",
    "iter_requirement_extraction_delta_packet_v1_issues",
    "validate_requirement_extraction_delta_packet_v1",
]
