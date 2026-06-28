"""Validation for agent safe-next-action release notes packets.

The validator is intentionally conservative. Release notes are an agent-facing and
user-facing boundary, so packets must not imply live DevHub execution, production
readiness, legal outcomes, private artifact retention, or enabled consequential
capabilities unless later code adds an explicitly reviewed exception.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


_LINK_FIELDS = {
    "href",
    "link",
    "source_link",
    "source_url",
    "url",
    "evidence_url",
    "citation_url",
    "prerequisite_link",
}

_CITATION_FIELDS = {
    "citation",
    "citations",
    "evidence",
    "evidence_ids",
    "source",
    "sources",
    "source_evidence_ids",
    "source_links",
    "source_urls",
}

_BLOCKER_FIELDS = {"blocker", "blockers", "known_blockers", "open_blockers", "blocking_issues"}

_PRODUCTION_READY_VALUES = {
    "production-ready",
    "production ready",
    "prod-ready",
    "prod ready",
    "ready for production",
    "ship-ready",
    "ship ready",
    "release-ready",
    "release ready",
}

_FORBIDDEN_CAPABILITY_WORDS = {
    "payment",
    "pay",
    "upload",
    "submit",
    "submission",
    "schedule",
    "scheduling",
    "cancel",
    "cancellation",
    "certify",
    "certification",
}

_GUARANTEE_PATTERNS = (
    re.compile(r"\bguarantee(?:d|s)?\b", re.IGNORECASE),
    re.compile(r"\bwill\s+(?:be\s+)?(?:approve|approved|issue|issued|accepted|pass|granted)\b", re.IGNORECASE),
    re.compile(r"\bensure(?:s|d)?\s+(?:approval|issuance|acceptance|compliance|eligibility)\b", re.IGNORECASE),
    re.compile(r"\b(?:legally|code)\s+compliant\b", re.IGNORECASE),
    re.compile(r"\b(?:permit|application)\s+(?:approval|issuance)\s+is\s+(?:certain|assured)\b", re.IGNORECASE),
)

_PRIVATE_ARTIFACT_PATTERNS = (
    re.compile(r"\b(?:cookie|cookies|password|credential|credentials|token|secret|mfa|captcha)\b", re.IGNORECASE),
    re.compile(r"\b(?:session|auth|storage)[_-]?state\b", re.IGNORECASE),
    re.compile(r"\b(?:trace\.zip|\.har|har file|screenshot|video recording)\b", re.IGNORECASE),
    re.compile(r"\b(?:/home/|/Users/|C:\\\\Users\\|private file path)\b", re.IGNORECASE),
)

_RAW_REFERENCE_PATTERNS = (
    re.compile(r"\b(?:raw crawl|raw html|raw body|warc|archive artifact|downloaded document|downloaded pdf)\b", re.IGNORECASE),
    re.compile(r"\b(?:downloads?/|crawl-output|crawl_output|archive/)\b", re.IGNORECASE),
)

_LIVE_EXECUTION_PATTERNS = (
    re.compile(r"\b(?:fetched|crawled|downloaded|queried)\s+(?:live|from\s+the\s+network|from\s+DevHub)\b", re.IGNORECASE),
    re.compile(r"\b(?:logged\s+in|signed\s+in)\s+(?:to\s+)?DevHub\b", re.IGNORECASE),
    re.compile(r"\b(?:clicked|pressed|ran|executed)\s+(?:in\s+)?DevHub\b", re.IGNORECASE),
    re.compile(r"\blive\s+(?:network|DevHub|browser|portal)\s+(?:run|execution|session|automation)\b", re.IGNORECASE),
)

_USER_FACING_KEYS = {"claim", "claims", "summary", "impact", "user_message", "release_note", "release_notes", "notes"}


@dataclass(frozen=True)
class ReleaseNotesValidationIssue:
    """A deterministic validation issue for a release notes packet."""

    code: str
    path: str
    message: str


def validate_release_notes_packet(packet: Mapping[str, Any]) -> list[ReleaseNotesValidationIssue]:
    """Return validation issues for an agent safe-next-action release notes packet."""

    issues: list[ReleaseNotesValidationIssue] = []
    issues.extend(_validate_prerequisite_links(packet))
    issues.extend(_validate_user_facing_claim_citations(packet))
    issues.extend(_validate_text_patterns(packet))
    issues.extend(_validate_production_ready_with_blockers(packet))
    issues.extend(_validate_enabled_consequential_capabilities(packet))
    return issues


def assert_valid_release_notes_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a release notes packet violates guardrails."""

    issues = validate_release_notes_packet(packet)
    if issues:
        details = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(details)


def _validate_prerequisite_links(packet: Mapping[str, Any]) -> list[ReleaseNotesValidationIssue]:
    issues: list[ReleaseNotesValidationIssue] = []
    prerequisites = packet.get("prerequisites", [])
    if prerequisites in (None, ""):
        return issues
    if not isinstance(prerequisites, Sequence) or isinstance(prerequisites, (str, bytes)):
        return [
            ReleaseNotesValidationIssue(
                "invalid_prerequisites",
                "$.prerequisites",
                "prerequisites must be a list of cited prerequisite objects",
            )
        ]
    for index, prerequisite in enumerate(prerequisites):
        path = f"$.prerequisites[{index}]"
        if not isinstance(prerequisite, Mapping):
            issues.append(
                ReleaseNotesValidationIssue(
                    "invalid_prerequisite",
                    path,
                    "each prerequisite must be an object with a source or evidence link",
                )
            )
            continue
        if not _mapping_has_link(prerequisite):
            issues.append(
                ReleaseNotesValidationIssue(
                    "missing_prerequisite_link",
                    path,
                    "prerequisite entries must include a source, citation, or evidence URL",
                )
            )
    return issues


def _validate_user_facing_claim_citations(packet: Mapping[str, Any]) -> list[ReleaseNotesValidationIssue]:
    issues: list[ReleaseNotesValidationIssue] = []
    for path, value in _walk(packet):
        if not isinstance(value, Mapping):
            continue
        if not _is_user_facing_claim(value):
            continue
        if not _mapping_has_citation(value):
            issues.append(
                ReleaseNotesValidationIssue(
                    "uncited_user_facing_claim",
                    path,
                    "user-facing claims must include citations or source evidence identifiers",
                )
            )
    return issues


def _validate_text_patterns(packet: Mapping[str, Any]) -> list[ReleaseNotesValidationIssue]:
    issues: list[ReleaseNotesValidationIssue] = []
    pattern_groups = (
        ("outcome_guarantee", _GUARANTEE_PATTERNS, "release notes must not guarantee legal, permitting, approval, or compliance outcomes"),
        ("private_or_session_artifact", _PRIVATE_ARTIFACT_PATTERNS, "release notes must not reference private session artifacts, credentials, traces, screenshots, or local paths"),
        ("raw_crawl_download_archive_reference", _RAW_REFERENCE_PATTERNS, "release notes must not reference raw crawl, download, WARC, or archive artifacts"),
        ("live_network_or_devhub_execution_claim", _LIVE_EXECUTION_PATTERNS, "release notes must not claim live network access or DevHub execution"),
    )
    for path, value in _walk(packet):
        if not isinstance(value, str):
            continue
        for code, patterns, message in pattern_groups:
            if any(pattern.search(value) for pattern in patterns):
                issues.append(ReleaseNotesValidationIssue(code, path, message))
    for path, value in _walk(packet):
        if _path_name(path) in {"live_network", "devhub_execution", "executed_live", "live_devhub_run"} and value is True:
            issues.append(
                ReleaseNotesValidationIssue(
                    "live_network_or_devhub_execution_claim",
                    path,
                    "boolean live network or DevHub execution claims are not allowed in release notes packets",
                )
            )
    return issues


def _validate_production_ready_with_blockers(packet: Mapping[str, Any]) -> list[ReleaseNotesValidationIssue]:
    has_blockers = any(_path_name(path) in _BLOCKER_FIELDS and _has_content(value) for path, value in _walk(packet))
    if not has_blockers:
        return []
    issues: list[ReleaseNotesValidationIssue] = []
    for path, value in _walk(packet):
        if isinstance(value, str) and value.strip().lower() in _PRODUCTION_READY_VALUES:
            issues.append(
                ReleaseNotesValidationIssue(
                    "production_ready_with_blockers",
                    path,
                    "packets with blockers must not be labeled production-ready",
                )
            )
    return issues


def _validate_enabled_consequential_capabilities(packet: Mapping[str, Any]) -> list[ReleaseNotesValidationIssue]:
    issues: list[ReleaseNotesValidationIssue] = []
    for path, value in _walk(packet):
        field = _path_name(path).replace("_", "-").lower()
        field_words = set(re.split(r"[^a-z]+", field))
        if value is True and field_words.intersection(_FORBIDDEN_CAPABILITY_WORDS):
            issues.append(
                ReleaseNotesValidationIssue(
                    "enabled_consequential_capability",
                    path,
                    "payment, upload, submission, scheduling, cancellation, and certification capabilities must not be enabled",
                )
            )
        if isinstance(value, Mapping):
            name = str(value.get("name") or value.get("capability") or value.get("action") or "").lower()
            enabled = value.get("enabled") is True or value.get("state") == "enabled"
            if enabled and _contains_forbidden_capability_word(name):
                issues.append(
                    ReleaseNotesValidationIssue(
                        "enabled_consequential_capability",
                        path,
                        "consequential DevHub capabilities must remain disabled or blocked in release notes packets",
                    )
                )
    return issues


def _is_user_facing_claim(value: Mapping[str, Any]) -> bool:
    if value.get("user_facing") is True or value.get("audience") in {"user", "public", "user-facing"}:
        return any(key in value for key in _USER_FACING_KEYS)
    if "claim" in value and value.get("internal_only") is not True:
        return True
    return False


def _mapping_has_citation(value: Mapping[str, Any]) -> bool:
    return any(key in value and _has_content(value[key]) for key in _CITATION_FIELDS) or _mapping_has_link(value)


def _mapping_has_link(value: Mapping[str, Any]) -> bool:
    for key, candidate in value.items():
        if key in _LINK_FIELDS and _has_content(candidate):
            return True
        if key in _CITATION_FIELDS and _contains_url(candidate):
            return True
    return False


def _contains_url(value: Any) -> bool:
    if isinstance(value, str):
        return value.startswith("https://") or value.startswith("http://")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_url(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_url(item) for item in value.values())
    return False


def _contains_forbidden_capability_word(value: str) -> bool:
    words = set(re.split(r"[^a-z]+", value.lower()))
    return bool(words.intersection(_FORBIDDEN_CAPABILITY_WORDS))


def _has_content(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_has_content(item) for item in value)
    return True


def _path_name(path: str) -> str:
    name = path.rsplit(".", 1)[-1]
    if name.endswith("]") and "[" in name:
        name = name.split("[", 1)[0]
    return name.strip("$")


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
