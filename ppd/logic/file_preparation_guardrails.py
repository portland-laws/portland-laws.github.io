"""Map file-preparation metadata findings into PP&D guardrail actions.

The helper in this module is intentionally small and deterministic. It accepts
already-extracted document metadata compliance findings and produces the
UserGapAnalysis-shaped guardrail fragments agents need before proposing DevHub
upload, certification, or submission actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

_BLOCKING_STATUSES = {"noncompliant", "missing", "stale", "conflicting", "failed"}
_BLOCKING_SEVERITIES = {"blocker", "error", "critical"}


@dataclass(frozen=True)
class ActionImpact:
    """A consequential action affected by a metadata finding."""

    action_id: str
    reason: str


def map_metadata_findings_to_guardrails(
    findings: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return blocked actions and next safe actions for metadata findings.

    Each input finding may contain these keys:
    - finding_id: stable identifier for the compliance finding
    - document_id: affected document identifier
    - status: compliant, noncompliant, missing, stale, conflicting, or failed
    - severity: info, warning, error, critical, or blocker
    - action_impacts: list of {action_id, reason} objects
    - safe_actions: list of {action_id, label, rationale} objects
    - source_evidence_ids: citation or requirement identifiers

    Findings only block actions when both their status and severity indicate
    that official action would be unsafe. Safe actions remain available whenever
    they are supplied by a finding.
    """

    blocked_by_action: dict[str, dict[str, Any]] = {}
    safe_by_action: dict[str, dict[str, Any]] = {}
    total = 0
    blocking_count = 0

    for finding in findings:
        total += 1
        finding_id = str(finding.get("finding_id", "unknown_finding"))
        document_id = str(finding.get("document_id", "unknown_document"))
        status = str(finding.get("status", "")).lower()
        severity = str(finding.get("severity", "")).lower()
        evidence_ids = [str(value) for value in finding.get("source_evidence_ids", [])]
        is_blocking = status in _BLOCKING_STATUSES and severity in _BLOCKING_SEVERITIES

        if is_blocking:
            blocking_count += 1
            for impact in _iter_action_impacts(finding):
                blocked = blocked_by_action.setdefault(
                    impact.action_id,
                    {
                        "action_id": impact.action_id,
                        "reason": impact.reason,
                        "finding_ids": [],
                        "document_ids": [],
                        "source_evidence_ids": [],
                    },
                )
                _append_unique(blocked["finding_ids"], finding_id)
                _append_unique(blocked["document_ids"], document_id)
                for evidence_id in evidence_ids:
                    _append_unique(blocked["source_evidence_ids"], evidence_id)

        for safe_action in finding.get("safe_actions", []):
            if not isinstance(safe_action, Mapping):
                continue
            action_id = str(safe_action.get("action_id", "")).strip()
            if not action_id:
                continue
            safe = safe_by_action.setdefault(
                action_id,
                {
                    "action_id": action_id,
                    "label": str(safe_action.get("label", action_id)),
                    "rationale": str(safe_action.get("rationale", "Resolve metadata finding before official action.")),
                    "finding_ids": [],
                },
            )
            _append_unique(safe["finding_ids"], finding_id)

    return {
        "compliance_summary": {
            "total_findings": total,
            "blocking_findings": blocking_count,
            "ready_for_official_actions": blocking_count == 0,
        },
        "blocked_actions": sorted(blocked_by_action.values(), key=lambda item: item["action_id"]),
        "next_safe_actions": sorted(safe_by_action.values(), key=lambda item: item["action_id"]),
    }


def _iter_action_impacts(finding: Mapping[str, Any]) -> Iterable[ActionImpact]:
    for impact in finding.get("action_impacts", []):
        if not isinstance(impact, Mapping):
            continue
        action_id = str(impact.get("action_id", "")).strip()
        if not action_id:
            continue
        reason = str(impact.get("reason", "Metadata compliance finding blocks this action."))
        yield ActionImpact(action_id=action_id, reason=reason)


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
