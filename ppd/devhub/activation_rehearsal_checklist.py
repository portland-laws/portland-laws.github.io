"""Validation for inactive PP&D activation rehearsal checklist artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_LIST_FIELDS: tuple[str, ...] = (
    "release_decision_references",
    "smoke_replay_references",
    "activation_prerequisites",
    "source_evidence_placeholder_checks",
    "reviewer_signoff_placeholders",
    "rollback_checkpoints",
    "post_activation_smoke_requirements",
    "hold_conditions",
    "validation_commands",
)

MUTATION_FLAG_KEYS: frozenset[str] = frozenset(
    {
        "active",
        "activation_enabled",
        "apply_mutations",
        "can_mutate",
        "devhub_write_enabled",
        "enabled",
        "live_mutation_enabled",
        "mutation_enabled",
        "official_action_enabled",
        "promote_enabled",
        "writes_enabled",
    }
)

LIVE_CLAIM_KEYS: frozenset[str] = frozenset(
    {
        "authenticated_devhub_checked",
        "devhub_live_checked",
        "live_crawl_completed",
        "live_devhub_completed",
        "live_replay_completed",
        "production_crawl_completed",
    }
)

PRIVATE_ARTIFACT_KEYWORDS: tuple[str, ...] = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "downloaded_document",
    "har",
    "private_artifact",
    "raw_crawl_output",
    "raw_download",
    "session_file",
    "trace",
)

PRIVATE_ARTIFACT_TEXT: tuple[str, ...] = (
    ".har",
    ".trace",
    "auth state",
    "browser state",
    "cookie jar",
    "downloaded document",
    "private artifact",
    "raw crawl output",
    "raw downloaded",
    "session storage",
    "storage_state",
)

LIVE_CLAIM_TEXT: tuple[str, ...] = (
    "authenticated devhub run completed",
    "devhub live crawl",
    "devhub live run",
    "live crawl completed",
    "live devhub completed",
    "production crawl completed",
)

ACTIVATION_CLAIM_TEXT: tuple[str, ...] = (
    "activation completed",
    "activation is complete",
    "activated in production",
    "promoted to production",
    "promotion completed",
)

OFFICIAL_ACTION_TEXT: tuple[str, ...] = (
    "certification completed",
    "fee payment completed",
    "inspection scheduled",
    "official action completed",
    "permit submitted",
    "submitted to devhub",
    "upload completed to official record",
)

GUARANTEE_TEXT: tuple[str, ...] = (
    "guaranteed approval",
    "guarantees approval",
    "legal guarantee",
    "permit approval is guaranteed",
    "will be approved",
    "will receive a permit",
)


@dataclass(frozen=True)
class ChecklistFinding:
    """A deterministic validation failure for a rehearsal checklist."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ChecklistValidationReport:
    """Validation result for an inactive activation rehearsal checklist."""

    ok: bool
    findings: tuple[ChecklistFinding, ...]

    def raise_for_errors(self) -> None:
        if self.ok:
            return
        rendered = "; ".join(f"{finding.path}: {finding.message}" for finding in self.findings)
        raise ValueError(rendered)


def validate_inactive_activation_rehearsal_checklist_v1(
    checklist: Mapping[str, Any],
) -> ChecklistValidationReport:
    """Validate that an inactive activation rehearsal checklist fails closed.

    The validator is intentionally schema-light: it accepts ordinary dictionaries
    from JSON or YAML loaders, checks required rehearsal evidence placeholders,
    and rejects claims or flags that would make an inactive rehearsal appear live.
    """

    findings: list[ChecklistFinding] = []

    version = checklist.get("version")
    if version != "inactive_activation_rehearsal_checklist_v1":
        findings.append(
            ChecklistFinding(
                code="invalid_version",
                path="version",
                message="must be inactive_activation_rehearsal_checklist_v1",
            )
        )

    status = checklist.get("status")
    if status != "inactive":
        findings.append(
            ChecklistFinding(
                code="not_inactive",
                path="status",
                message="must be inactive",
            )
        )

    for field in REQUIRED_LIST_FIELDS:
        value = checklist.get(field)
        if not _non_empty_sequence(value):
            findings.append(
                ChecklistFinding(
                    code=f"missing_{field}",
                    path=field,
                    message="must contain at least one non-empty placeholder or reference",
                )
            )

    for path, key, value in _walk(checklist):
        lowered_key = key.lower()
        if lowered_key in MUTATION_FLAG_KEYS and value is True:
            findings.append(
                ChecklistFinding(
                    code="active_mutation_flag",
                    path=path,
                    message="inactive rehearsal checklists must not enable mutation or activation flags",
                )
            )
        if lowered_key in LIVE_CLAIM_KEYS and value is True:
            findings.append(
                ChecklistFinding(
                    code="live_crawl_or_devhub_claim",
                    path=path,
                    message="inactive rehearsal checklists must not claim live crawl or DevHub completion",
                )
            )
        if _contains_any(lowered_key, PRIVATE_ARTIFACT_KEYWORDS) and _has_value(value):
            findings.append(
                ChecklistFinding(
                    code="private_or_raw_artifact",
                    path=path,
                    message="must not reference private, raw, downloaded, session, trace, or HAR artifacts",
                )
            )
        if isinstance(value, str):
            lowered_value = " ".join(value.lower().split())
            text_checks: tuple[tuple[str, tuple[str, ...], str], ...] = (
                (
                    "private_or_raw_artifact",
                    PRIVATE_ARTIFACT_TEXT,
                    "must not reference private, raw, downloaded, session, trace, or HAR artifacts",
                ),
                (
                    "live_crawl_or_devhub_claim",
                    LIVE_CLAIM_TEXT,
                    "must not claim live crawl or DevHub completion",
                ),
                (
                    "activation_or_promotion_claim",
                    ACTIVATION_CLAIM_TEXT,
                    "must not claim activation or promotion completion",
                ),
                (
                    "official_action_completion_claim",
                    OFFICIAL_ACTION_TEXT,
                    "must not claim official-action completion",
                ),
                (
                    "legal_or_permitting_guarantee",
                    GUARANTEE_TEXT,
                    "must not provide legal or permitting guarantees",
                ),
            )
            for code, needles, message in text_checks:
                if _contains_any(lowered_value, needles):
                    findings.append(ChecklistFinding(code=code, path=path, message=message))

    return ChecklistValidationReport(ok=not findings, findings=tuple(findings))


def _non_empty_sequence(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return False
    return any(_has_value(item) for item in value)


def _has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_value(item) for item in value)
    return True


def _contains_any(value: str, needles: Iterable[str]) -> bool:
    return any(needle in value for needle in needles)


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}"
            yield child_path, key, child
            yield from _walk(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, str(index), child
            yield from _walk(child, child_path)
