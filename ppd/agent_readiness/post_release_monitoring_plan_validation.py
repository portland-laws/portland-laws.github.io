"""Validation for PP&D post-release monitoring plans.

The validator is intentionally side-effect free. It checks fixture or packet
metadata only; it does not fetch URLs, open browsers, activate schedules, or
mutate artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping
from urllib.parse import urlparse


@dataclass(frozen=True)
class PostReleaseMonitoringPlanValidationResult:
    """Machine-readable validation result for post-release monitoring plans."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


_MONITORING_CHECK_KEYS = {
    "monitoring_check",
    "monitoring_checks",
    "post_release_check",
    "post_release_checks",
    "checks",
}
_CITATION_KEYS = {"source_evidence_id", "source_evidence_ids", "citation_id", "citation_ids", "citations"}
_REVIEWER_OWNER_KEYS = {"reviewer_owner", "reviewer_owner_id", "owner", "owner_id"}
_ESCALATION_KEYS = {"escalation_note", "escalation_notes", "escalation_path", "escalation_runbook"}
_THRESHOLD_KEYS = {
    "alert_threshold",
    "alert_thresholds",
    "failure_threshold",
    "freshness_threshold",
    "max_age_days",
    "threshold",
    "thresholds",
}
_RAW_REFERENCE_KEYS = {
    "archive_artifact_ref",
    "archive_path",
    "download_artifact_ref",
    "download_path",
    "download_url",
    "downloaded_document",
    "raw_archive_ref",
    "raw_body",
    "raw_body_path",
    "raw_crawl_ref",
    "raw_download_ref",
    "raw_html",
    "warc_path",
}
_LIVE_EXECUTION_KEYS = {
    "browser_execution_claim",
    "browser_opened",
    "browser_ran",
    "fetch_executed",
    "fetch_ran",
    "live_browser_execution",
    "live_fetch",
    "live_fetch_executed",
    "live_monitor_execution",
    "monitor_executed",
    "monitor_ran",
    "playwright_executed",
}
_ACTIVE_SCHEDULE_KEYS = {
    "active_schedule",
    "active_schedule_enabled",
    "cron_enabled",
    "schedule_active",
    "schedule_enabled",
    "scheduled_job_enabled",
}
_ARTIFACT_MUTATION_KEYS = {
    "artifact_mutation_enabled",
    "artifact_writes_enabled",
    "commit_artifacts",
    "mutates_artifacts",
    "persist_artifacts",
    "updates_artifacts",
    "write_artifacts",
    "writes_active_state",
}
_LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/private/)|(^/var/folders/)|(^~?/\.devhub/)|(^[A-Za-z]:[\\/]Users[\\/][^\\/]+[\\/])",
    re.IGNORECASE,
)
_RAW_REFERENCE_RE = re.compile(
    r"(\.har$|\.trace$|trace\.zip$|\.warc(\.gz)?$|raw[-_/ ]?(body|crawl|download)|/downloads?/|/archives?/|archive_artifact|download_artifact)",
    re.IGNORECASE,
)
_LIVE_EXECUTION_RE = re.compile(
    r"\b(live monitor|monitor ran|monitor executed|live fetch|fetch ran|fetch executed|browser ran|browser executed|opened a browser|playwright ran|playwright executed)\b",
    re.IGNORECASE,
)
_PRIVATE_URL_RE = re.compile(
    r"\b(auth|authenticated|account|login|signin|sign-in|session|token|cookie|my[-_ ]?permits|private|portal/dashboard)\b",
    re.IGNORECASE,
)


def validate_post_release_monitoring_plan(packet: Mapping[str, Any]) -> PostReleaseMonitoringPlanValidationResult:
    """Return fail-closed validation for a PP&D post-release monitoring plan."""

    evidence_ids = _evidence_ids(packet)
    problems: list[str] = []
    problems.extend(_monitoring_check_problems(packet, evidence_ids))
    problems.extend(_private_url_problems(packet))
    problems.extend(_raw_reference_problems(packet))
    problems.extend(_local_private_path_problems(packet))
    problems.extend(_live_execution_claim_problems(packet))
    problems.extend(_active_schedule_or_mutation_problems(packet))
    return PostReleaseMonitoringPlanValidationResult(ready=not problems, problems=tuple(problems))


def require_post_release_monitoring_plan(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a post-release monitoring plan is unsafe."""

    result = validate_post_release_monitoring_plan(packet)
    if not result.ready:
        raise ValueError("invalid_post_release_monitoring_plan: " + "; ".join(result.problems))


def _monitoring_check_problems(value: Any, evidence_ids: set[str], path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in _MONITORING_CHECK_KEYS:
                checks = child if isinstance(child, list) else [child]
                for index, check in enumerate(checks):
                    check_path = f"{child_path}[{index}]"
                    if not isinstance(check, Mapping):
                        problems.append(f"monitoring check must be an object at {check_path}")
                        continue
                    refs = _collect_evidence_refs(check)
                    if not refs:
                        problems.append(f"monitoring check lacks citation at {check_path}")
                    for ref in sorted(refs):
                        if ref not in evidence_ids:
                            problems.append(f"monitoring check cites unknown source evidence {ref} at {check_path}")
                    if not _has_nonempty_key(check, _REVIEWER_OWNER_KEYS):
                        problems.append(f"monitoring check lacks reviewer owner at {check_path}")
                    if not _has_nonempty_key(check, _ESCALATION_KEYS):
                        problems.append(f"monitoring check lacks escalation note at {check_path}")
                    if not _has_nonempty_key(check, _THRESHOLD_KEYS):
                        problems.append(f"monitoring check lacks alert threshold at {check_path}")
            problems.extend(_monitoring_check_problems(child, evidence_ids, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_monitoring_check_problems(child, evidence_ids, f"{path}[{index}]"))
    return problems


def _private_url_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            problems.extend(_private_url_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_private_url_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _is_private_or_authenticated_url(value):
        problems.append(f"private or authenticated URL is not allowed at {path}")
    return problems


def _raw_reference_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _RAW_REFERENCE_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"raw body/download/archive reference is not allowed at {child_path}")
            if _contains_raw_reference(child):
                problems.append(f"raw body/download/archive reference is not allowed at {child_path}")
            problems.extend(_raw_reference_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_raw_reference_problems(child, f"{path}[{index}]"))
    return problems


def _local_private_path_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            problems.extend(_local_private_path_problems(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_local_private_path_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _LOCAL_PRIVATE_PATH_RE.search(value):
        problems.append(f"local private path is not allowed at {path}")
    return problems


def _live_execution_claim_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _LIVE_EXECUTION_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"live monitor/fetch/browser execution claim is not allowed at {child_path}")
            problems.extend(_live_execution_claim_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_live_execution_claim_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _LIVE_EXECUTION_RE.search(value):
        problems.append(f"live monitor/fetch/browser execution claim is not allowed at {path}")
    return problems


def _active_schedule_or_mutation_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized = key_text.lower()
            if normalized in _ACTIVE_SCHEDULE_KEYS and child is True:
                problems.append(f"active schedule flag is not allowed at {child_path}")
            if normalized in _ARTIFACT_MUTATION_KEYS and child is True:
                problems.append(f"artifact mutation flag is not allowed at {child_path}")
            problems.extend(_active_schedule_or_mutation_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_active_schedule_or_mutation_problems(child, f"{path}[{index}]"))
    return problems


def _evidence_ids(packet: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("normalized_source_evidence", "citations", "sources", "source_registry"):
        raw = packet.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            for id_key in ("evidence_id", "source_evidence_id", "citation_id", "source_id"):
                value = item.get(id_key)
                if isinstance(value, str) and value:
                    ids.add(value)
    return ids


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for key in _CITATION_KEYS:
            raw = value.get(key)
            if isinstance(raw, str) and raw:
                refs.add(raw)
            elif isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str) and item:
                        refs.add(item)
                    elif isinstance(item, Mapping):
                        refs.update(_collect_evidence_refs(item))
        for child in value.values():
            refs.update(_collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_evidence_refs(child))
    return refs


def _has_nonempty_key(value: Mapping[str, Any], keys: set[str]) -> bool:
    for key in keys:
        child = value.get(key)
        if child not in (None, False, "", [], {}):
            return True
    return False


def _contains_raw_reference(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_RAW_REFERENCE_RE.search(value))
    if isinstance(value, list):
        return any(_contains_raw_reference(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_raw_reference(item) for item in value.values())
    return False


def _is_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return True
    url_text = value.lower()
    if _PRIVATE_URL_RE.search(url_text):
        return True
    if parsed.scheme != "https":
        return True
    return False
