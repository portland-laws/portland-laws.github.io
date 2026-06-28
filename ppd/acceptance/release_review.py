"""Validation for PP&D release acceptance review packets.

The validator is intentionally schema-tolerant: supervisor packets may grow new
fields, but acceptance still requires citations, traceability, reviewer owners,
rerun expectations, and explicit rejection of unsafe release claims or controls.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReviewPacketIssue:
    """A deterministic validation issue for a release acceptance packet."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ReviewPacketValidationResult:
    """Validation result for a release acceptance review packet."""

    ok: bool
    issues: tuple[ReviewPacketIssue, ...]


_PRIVATE_ARTIFACT_RE = re.compile(
    r"(auth[_-]?state|cookie|credential|devhub[_-]?session|\.har\b|trace\.zip|playwright/.auth|session[_-]?storage|screenshot)",
    re.IGNORECASE,
)
_RAW_ARTIFACT_RE = re.compile(
    r"(raw[_-]?crawl|raw[_-]?download|raw[_-]?archive|/downloads?/|\.warc(?:\.gz)?\b|archive/raw|crawl-output)",
    re.IGNORECASE,
)
_LIVE_PUBLICATION_RE = re.compile(
    r"(published\s+live|live\s+publication|deployed\s+to\s+production|public\s+site\s+updated|production\s+release\s+complete)",
    re.IGNORECASE,
)
_OUTCOME_GUARANTEE_RE = re.compile(
    r"(permit\s+(?:will|shall)\s+be\s+(?:approved|issued)|approval\s+guaranteed|guarantees?\s+(?:approval|issuance|legal\s+compliance)|legally\s+binding\s+determination)",
    re.IGNORECASE,
)

_CONSEQUENTIAL_CONTROL_NAMES = {
    "submit",
    "certify",
    "upload",
    "schedule_inspection",
    "cancel",
    "withdraw",
    "pay",
    "purchase",
    "request_extension",
    "reactivate",
}
_ARTIFACT_MUTATION_NAMES = {
    "mutate_artifacts",
    "write_artifacts",
    "refresh_artifacts",
    "publish_artifacts",
    "crawl_live",
    "download_live",
}


def validate_release_acceptance_review_packet(packet: Mapping[str, Any]) -> ReviewPacketValidationResult:
    """Return deterministic acceptance issues for a release review packet."""

    issues: list[ReviewPacketIssue] = []
    _require_cited_checklist_items(packet, issues)
    _require_consumed_packet_refs(packet, issues)
    _require_open_blocker_dispositions(packet, issues)
    _require_reviewer_owners(packet, issues)
    _require_validation_rerun_expectations(packet, issues)
    _reject_recursive_unsafe_content(packet, issues)
    _reject_enabled_consequential_controls(packet, issues)
    _reject_active_artifact_mutation_flags(packet, issues)
    return ReviewPacketValidationResult(ok=not issues, issues=tuple(issues))


def _require_cited_checklist_items(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    checklist = _as_list(packet.get("checklist_items") or packet.get("checklist") or packet.get("acceptance_checklist"))
    if not checklist:
        issues.append(ReviewPacketIssue("missing_checklist", "checklist_items", "release acceptance review requires checklist items"))
        return
    for index, item in enumerate(checklist):
        path = f"checklist_items[{index}]"
        if not isinstance(item, Mapping):
            issues.append(ReviewPacketIssue("invalid_checklist_item", path, "checklist item must be an object"))
            continue
        citations = item.get("citations") or item.get("citation_refs") or item.get("source_evidence_ids") or item.get("evidence")
        if not _has_nonempty_ref(citations):
            issues.append(ReviewPacketIssue("uncited_checklist_item", path, "checklist item must cite source evidence or review evidence"))


def _require_consumed_packet_refs(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    refs = packet.get("consumed_packet_refs") or packet.get("consumed_packets") or packet.get("input_packet_refs")
    if not _has_nonempty_ref(refs):
        issues.append(ReviewPacketIssue("missing_consumed_packet_refs", "consumed_packet_refs", "release review must identify consumed packet references"))


def _require_open_blocker_dispositions(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    blockers = _as_list(packet.get("blockers") or packet.get("open_blockers") or packet.get("known_blockers"))
    for index, blocker in enumerate(blockers):
        path = f"blockers[{index}]"
        if not isinstance(blocker, Mapping):
            continue
        status = str(blocker.get("status", "open")).strip().lower()
        if status in {"open", "active", "unresolved", "blocking"} and not _nonempty_text(blocker.get("disposition")):
            issues.append(ReviewPacketIssue("missing_open_blocker_disposition", path, "open blocker must include an explicit disposition"))


def _require_reviewer_owners(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    reviewers = _as_list(packet.get("reviewers") or packet.get("reviewer_owners") or packet.get("owners"))
    if not reviewers:
        issues.append(ReviewPacketIssue("missing_reviewer_owner", "reviewers", "release review must name at least one reviewer owner"))
        return
    for index, reviewer in enumerate(reviewers):
        path = f"reviewers[{index}]"
        if isinstance(reviewer, str) and reviewer.strip():
            continue
        if isinstance(reviewer, Mapping) and _nonempty_text(reviewer.get("owner") or reviewer.get("reviewer") or reviewer.get("name")):
            continue
        issues.append(ReviewPacketIssue("missing_reviewer_owner", path, "reviewer entry must include an owner"))


def _require_validation_rerun_expectations(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    reruns = _as_list(packet.get("validation_rerun_expectations") or packet.get("validation_reruns") or packet.get("rerun_expectations"))
    if not reruns:
        issues.append(ReviewPacketIssue("missing_validation_rerun_expectations", "validation_rerun_expectations", "release review must document expected validation reruns"))
        return
    for index, rerun in enumerate(reruns):
        path = f"validation_rerun_expectations[{index}]"
        if isinstance(rerun, str) and rerun.strip():
            continue
        if isinstance(rerun, Mapping) and _nonempty_text(rerun.get("command") or rerun.get("check")) and _nonempty_text(rerun.get("expectation") or rerun.get("expected_result") or rerun.get("must_pass")):
            continue
        issues.append(ReviewPacketIssue("incomplete_validation_rerun_expectation", path, "rerun expectation must include a check and expected result"))


def _reject_recursive_unsafe_content(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    for path, value in _walk(packet):
        if not isinstance(value, str):
            continue
        if _PRIVATE_ARTIFACT_RE.search(value):
            issues.append(ReviewPacketIssue("private_or_session_artifact", path, "review packet must not reference private/session artifacts"))
        if _RAW_ARTIFACT_RE.search(value):
            issues.append(ReviewPacketIssue("raw_crawl_download_archive_reference", path, "review packet must not reference raw crawl, download, or archive artifacts"))
        if _LIVE_PUBLICATION_RE.search(value):
            issues.append(ReviewPacketIssue("live_publication_claim", path, "review packet must not claim live publication"))
        if _OUTCOME_GUARANTEE_RE.search(value):
            issues.append(ReviewPacketIssue("legal_or_permitting_outcome_guarantee", path, "review packet must not guarantee legal or permitting outcomes"))


def _reject_enabled_consequential_controls(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    controls = _as_list(packet.get("consequential_controls") or packet.get("action_controls") or packet.get("controls"))
    for index, control in enumerate(controls):
        path = f"consequential_controls[{index}]"
        if isinstance(control, Mapping):
            name = str(control.get("name") or control.get("control") or control.get("action") or "").strip().lower()
            enabled = bool(control.get("enabled") or control.get("active"))
            if enabled and (not name or name in _CONSEQUENTIAL_CONTROL_NAMES or str(control.get("classification", "")).lower() == "consequential"):
                issues.append(ReviewPacketIssue("enabled_consequential_control", path, "consequential controls must not be enabled in release acceptance packets"))


def _reject_active_artifact_mutation_flags(packet: Mapping[str, Any], issues: list[ReviewPacketIssue]) -> None:
    flags = packet.get("artifact_mutation_flags") or packet.get("mutation_flags") or packet.get("flags") or {}
    if isinstance(flags, Mapping):
        for name, value in flags.items():
            normalized = str(name).strip().lower()
            if normalized in _ARTIFACT_MUTATION_NAMES and value is True:
                issues.append(ReviewPacketIssue("active_artifact_mutation_flag", f"artifact_mutation_flags.{name}", "artifact mutation flags must be disabled"))
    elif isinstance(flags, list):
        for index, flag in enumerate(flags):
            if isinstance(flag, Mapping):
                name = str(flag.get("name") or flag.get("flag") or "").strip().lower()
                active = bool(flag.get("active") or flag.get("enabled"))
                if name in _ARTIFACT_MUTATION_NAMES and active:
                    issues.append(ReviewPacketIssue("active_artifact_mutation_flag", f"artifact_mutation_flags[{index}]", "artifact mutation flags must be disabled"))


def _walk(value: Any, path: str = "$.") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}{key}"
            yield child_path, child
            yield from _walk(child, f"{child_path}.")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, f"{child_path}.")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _has_nonempty_ref(value: Any) -> bool:
    if _nonempty_text(value):
        return True
    if isinstance(value, Mapping):
        return any(_has_nonempty_ref(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_nonempty_ref(child) for child in value)
    return False


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
