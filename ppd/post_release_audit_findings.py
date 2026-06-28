"""Fixture-first post-release audit findings packet builder.

This module intentionally performs no crawling, DevHub automation, LLM calls, or
private-file reads. It transforms explicit JSON fixtures into a deterministic
post-release audit findings packet suitable for daemon validation and reviewer
handoff.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LIVE_ACTION_ATTESTATIONS = {
    "crawls_started": False,
    "devhub_launched": False,
    "llm_called": False,
    "private_files_read": False,
    "captcha_or_mfa_automated": False,
    "submissions_or_uploads_performed": False,
}

FOLLOW_UP_CATEGORY_BY_SEVERITY = {
    "critical": "release-blocker-triage",
    "high": "reviewer-owned-remediation",
    "medium": "scheduled-daemon-follow-up",
    "low": "backlog-observation",
}


class AuditPacketError(ValueError):
    """Raised when fixture input cannot produce a valid audit packet."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise AuditPacketError(f"expected JSON object in {path}")
    return payload


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuditPacketError(f"missing non-empty text field: {field}")
    return value.strip()


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise AuditPacketError(f"missing list field: {field}")
    return value


def _checklist_index(checklist: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = _require_list(checklist.get("safe_next_actions"), "safe_next_actions")
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise AuditPacketError("safe_next_actions entries must be objects")
        action_id = _require_text(entry.get("id"), "safe_next_actions.id")
        indexed[action_id] = entry
    return indexed


def build_post_release_audit_findings_packet(
    seed_packet: dict[str, Any], checklist: dict[str, Any]
) -> dict[str, Any]:
    """Build a cited post-release findings packet from public fixtures."""

    seed_id = _require_text(seed_packet.get("packet_id"), "packet_id")
    checklist_id = _require_text(checklist.get("checklist_id"), "checklist_id")
    generated_from = {
        "seed_packet_id": seed_id,
        "handoff_checklist_id": checklist_id,
    }
    checklist_by_id = _checklist_index(checklist)

    findings: list[dict[str, Any]] = []
    unresolved_blockers: list[dict[str, str]] = []
    for offset, seed_finding in enumerate(_require_list(seed_packet.get("findings"), "findings"), 1):
        if not isinstance(seed_finding, dict):
            raise AuditPacketError("findings entries must be objects")

        source_id = _require_text(seed_finding.get("id"), "findings.id")
        severity = _require_text(seed_finding.get("severity"), "findings.severity").lower()
        if severity not in FOLLOW_UP_CATEGORY_BY_SEVERITY:
            raise AuditPacketError(f"unsupported severity for {source_id}: {severity}")

        reviewer_owner = _require_text(seed_finding.get("reviewer_owner"), "findings.reviewer_owner")
        checklist_ref = _require_text(seed_finding.get("safe_next_action_ref"), "findings.safe_next_action_ref")
        if checklist_ref not in checklist_by_id:
            raise AuditPacketError(f"unknown safe-next-action reference for {source_id}: {checklist_ref}")

        blocker_refs = [
            _require_text(blocker, "findings.unresolved_blocker_refs")
            for blocker in seed_finding.get("unresolved_blocker_refs", [])
        ]
        for blocker_ref in blocker_refs:
            unresolved_blockers.append({
                "finding_id": f"PPAF-{offset:03d}",
                "blocker_ref": blocker_ref,
                "reviewer_owner": reviewer_owner,
            })

        finding = {
            "finding_id": f"PPAF-{offset:03d}",
            "source_finding_id": source_id,
            "title": _require_text(seed_finding.get("title"), "findings.title"),
            "severity": severity,
            "reviewer_owner": reviewer_owner,
            "citation_refs": [
                _require_text(ref, "findings.citation_refs")
                for ref in _require_list(seed_finding.get("citation_refs"), "findings.citation_refs")
            ],
            "safe_next_action_ref": checklist_ref,
            "safe_next_action_owner": _require_text(checklist_by_id[checklist_ref].get("owner"), "safe_next_actions.owner"),
            "unresolved_blocker_refs": blocker_refs,
            "recommended_daemon_follow_up_category": FOLLOW_UP_CATEGORY_BY_SEVERITY[severity],
        }
        findings.append(finding)

    return {
        "packet_type": "post_release_audit_findings_packet",
        "generated_from": generated_from,
        "live_action_attestations": dict(LIVE_ACTION_ATTESTATIONS),
        "findings": findings,
        "unresolved_blockers": unresolved_blockers,
        "recommended_daemon_follow_up_categories": sorted(
            {finding["recommended_daemon_follow_up_category"] for finding in findings}
        ),
    }


def build_packet_from_fixture_paths(seed_packet_path: Path, checklist_path: Path) -> dict[str, Any]:
    return build_post_release_audit_findings_packet(
        seed_packet=_read_json(seed_packet_path),
        checklist=_read_json(checklist_path),
    )


__all__ = [
    "AuditPacketError",
    "build_packet_from_fixture_paths",
    "build_post_release_audit_findings_packet",
]
