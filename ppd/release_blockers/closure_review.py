"""Validate fixture-first PP&D release blocker closure review packets."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


_CITATION_KEYS = ("citations", "source_citations", "evidence_citations", "citation_ids", "source_evidence_ids")
_CONSUMED_PACKET_KEYS = ("consumed_packet_refs", "consumed_packets", "input_packet_refs", "input_packets", "source_packets")
_DECISION_KEYS = ("blocker_decisions", "closure_decisions", "decisions", "blockers")
_OWNER_KEYS = ("reviewer_owner", "reviewer", "owner", "reviewer_owners")
_COMMAND_KEYS = ("follow_up_validation_commands", "validation_commands", "followup_validation_commands", "post_closure_validation_commands")

_RAW_ARTIFACT_KEY_MARKERS = (
    "archive",
    "body",
    "download",
    "full_html",
    "full_text",
    "html_body",
    "pdf_bytes",
    "raw_body",
    "raw_download",
    "raw_html",
    "raw_pdf",
    "raw_text",
)
_PRIVATE_KEY_MARKERS = (
    "auth",
    "browser_trace",
    "card_number",
    "cookie",
    "credential",
    "cvv",
    "email",
    "har",
    "mfa",
    "password",
    "payment",
    "phone",
    "private",
    "session",
    "screenshot",
    "ssn",
    "storage_state",
    "token",
)
_MUTATION_KEY_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"active[_-]?(source|requirement|process|guardrail|prompt|surface[_-]?registry|release[_-]?state).*(mutat|patch|update|write|change|replace|promote)",
        r"(mutat|patch|update|write|change|replace|promote).*active[_-]?(source|requirement|process|guardrail|prompt|surface[_-]?registry|release[_-]?state)",
    )
)
_LIVE_EXECUTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(live|real)\s+(crawler|crawl|processor|processing|devhub|llm)\b",
        r"\b(crawler|processor|devhub|llm)\s+(ran|run|executed|launched|opened|called|invoked|processed|generated)\b",
        r"\b(ran|executed|launched|opened|called|invoked)\s+(the\s+)?(crawler|processor|devhub|llm)\b",
        r"\b(fetch(?:ed)?|download(?:ed)?|crawl(?:ed)?|scrap(?:ed|ing))\s+(live|public|devhub|production)\b",
    )
)
_GUARANTEE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bguarantee[sd]?\b.*\b(approval|approved|permit|legal|compliance|outcome)\b",
        r"\b(approval|approved|permit|legal|compliance|outcome)\b.*\bguarantee[sd]?\b",
        r"\bwill\s+(be\s+)?(approved|permitted|legal|compliant|accepted)\b",
        r"\bensures?\s+(permit|legal|approval|compliance|acceptance)\b",
    )
)
_RAW_VALUE_MARKERS = (
    ".har",
    ".trace",
    ".zip",
    "/archive/",
    "/downloads/",
    "archive://",
    "downloaded file",
    "raw body",
    "raw html",
    "raw pdf",
)
_PRIVATE_VALUE_MARKERS = (
    "bearer ",
    "cookie=",
    "password=",
    "playwright/.auth",
    "session_cookie",
    "storage-state",
    "token=",
)


@dataclass(frozen=True)
class ClosureReviewFinding:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ClosureReviewValidation:
    ok: bool
    findings: tuple[ClosureReviewFinding, ...]


class ClosureReviewPacketError(ValueError):
    def __init__(self, findings: Sequence[ClosureReviewFinding]) -> None:
        self.findings = tuple(findings)
        codes = ", ".join(finding.code for finding in self.findings)
        super().__init__(f"release blocker closure review packet rejected: {codes}")


def validate_release_blocker_closure_review_packet(packet: Mapping[str, Any]) -> ClosureReviewValidation:
    """Return validation findings for a release blocker closure review packet."""

    if not isinstance(packet, Mapping):
        finding = ClosureReviewFinding("invalid_packet", "$", "Closure review packet must be an object.")
        return ClosureReviewValidation(False, (finding,))

    findings: list[ClosureReviewFinding] = []
    decisions = _decisions(packet)

    if not decisions:
        findings.append(ClosureReviewFinding("missing_blocker_decisions", "$.blocker_decisions", "Packet must include blocker closure decisions."))

    if not _has_consumed_packet_refs(packet):
        findings.append(ClosureReviewFinding("missing_consumed_packet_refs", "$", "Packet must reference the consumed review packets."))

    if not _has_follow_up_validation_commands(packet):
        findings.append(ClosureReviewFinding("missing_follow_up_validation_commands", "$", "Packet must include follow-up validation commands."))

    if not _has_packet_owner(packet) and not all(_has_owner(decision) for _, decision in decisions):
        findings.append(ClosureReviewFinding("missing_reviewer_owner", "$", "Packet or every decision must identify reviewer owners."))

    for index, decision in decisions:
        path = f"$.blocker_decisions[{index}]"
        if not _has_citations(decision):
            findings.append(ClosureReviewFinding("uncited_blocker_decision", path, "Each blocker decision must cite source evidence."))
        if not _has_consumed_packet_refs(decision) and not _text(decision.get("source_packet")):
            findings.append(ClosureReviewFinding("missing_consumed_packet_refs", path, "Each blocker decision must reference the consumed packet it closes or keeps open."))
        if not _has_owner(decision) and not _has_packet_owner(packet):
            findings.append(ClosureReviewFinding("missing_reviewer_owner", path, "Each blocker decision must identify a reviewer owner."))

    findings.extend(_unsafe_content_findings(packet))
    return ClosureReviewValidation(ok=not findings, findings=tuple(findings))


def require_release_blocker_closure_review_packet(packet: Mapping[str, Any]) -> None:
    result = validate_release_blocker_closure_review_packet(packet)
    if result.findings:
        raise ClosureReviewPacketError(result.findings)


def finding_codes(findings: Iterable[ClosureReviewFinding] | ClosureReviewValidation) -> set[str]:
    if isinstance(findings, ClosureReviewValidation):
        findings = findings.findings
    return {finding.code for finding in findings}


def _decisions(packet: Mapping[str, Any]) -> tuple[tuple[int, Mapping[str, Any]], ...]:
    for key in _DECISION_KEYS:
        value = packet.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return tuple((index, item) for index, item in enumerate(value) if isinstance(item, Mapping))
    return ()


def _has_packet_owner(packet: Mapping[str, Any]) -> bool:
    owners = packet.get("reviewer_owners")
    if isinstance(owners, Sequence) and not isinstance(owners, (str, bytes, bytearray)):
        return any(_has_value(owner) for owner in owners)
    return _has_owner(packet)


def _has_owner(value: Mapping[str, Any]) -> bool:
    return any(_has_value(value.get(key)) for key in _OWNER_KEYS)


def _has_citations(value: Mapping[str, Any]) -> bool:
    return any(_has_value(value.get(key)) for key in _CITATION_KEYS)


def _has_consumed_packet_refs(value: Mapping[str, Any]) -> bool:
    return any(_has_value(value.get(key)) for key in _CONSUMED_PACKET_KEYS)


def _has_follow_up_validation_commands(packet: Mapping[str, Any]) -> bool:
    for key in _COMMAND_KEYS:
        value = packet.get(key)
        commands = _as_sequence(value)
        if any(_text(command) for command in commands):
            return True
    return False


def _unsafe_content_findings(value: Any, path: str = "$", key_name: str = "") -> tuple[ClosureReviewFinding, ...]:
    findings: list[ClosureReviewFinding] = []
    normalized_key = _normalize_key(key_name)

    if normalized_key:
        if any(marker in normalized_key for marker in _RAW_ARTIFACT_KEY_MARKERS):
            findings.append(ClosureReviewFinding("raw_body_download_archive_reference", path, "Closure review packets must not include raw body, download, or archive references."))
        if any(marker in normalized_key for marker in _PRIVATE_KEY_MARKERS):
            findings.append(ClosureReviewFinding("private_session_artifact", path, "Closure review packets must not include private values, session state, traces, screenshots, credentials, or payment artifacts."))
        if any(pattern.search(normalized_key) for pattern in _MUTATION_KEY_PATTERNS) and _has_value(value):
            findings.append(ClosureReviewFinding("active_mutation_flag", path, "Closure review packets must not carry active source, requirement, process, guardrail, prompt, surface-registry, or release-state mutation flags."))

    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_text = str(child_key)
            findings.extend(_unsafe_content_findings(child, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            findings.extend(_unsafe_content_findings(child, f"{path}[{index}]", key_name))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _RAW_VALUE_MARKERS):
            findings.append(ClosureReviewFinding("raw_body_download_archive_reference", path, "Closure review packets must not reference raw bodies, downloads, or archives."))
        if any(marker in lowered for marker in _PRIVATE_VALUE_MARKERS):
            findings.append(ClosureReviewFinding("private_session_artifact", path, "Closure review packets must not reference private or session artifacts."))
        if any(pattern.search(value) for pattern in _LIVE_EXECUTION_PATTERNS):
            findings.append(ClosureReviewFinding("live_execution_claim", path, "Closure review packets must not claim live crawler, processor, DevHub, or LLM execution."))
        if any(pattern.search(value) for pattern in _GUARANTEE_PATTERNS):
            findings.append(ClosureReviewFinding("outcome_guarantee", path, "Closure review packets must not guarantee legal or permitting outcomes."))

    return tuple(findings)


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_value(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_value(item) for item in value)
    return True


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_key(value: str) -> str:
    chars: list[str] = []
    for character in value:
        chars.append(character.lower() if character.isalnum() else "_")
    normalized = "".join(chars)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


validate_packet = validate_release_blocker_closure_review_packet
require_packet = require_release_blocker_closure_review_packet

__all__ = [
    "ClosureReviewFinding",
    "ClosureReviewPacketError",
    "ClosureReviewValidation",
    "finding_codes",
    "require_packet",
    "require_release_blocker_closure_review_packet",
    "validate_packet",
    "validate_release_blocker_closure_review_packet",
]
