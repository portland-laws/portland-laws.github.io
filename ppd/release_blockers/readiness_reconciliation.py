"""Fixture-first release blocker reconciliation for PP&D agent readiness.

This module is intentionally side-effect free. It accepts already-captured audit
packets and emits an offline reconciliation packet; it does not invoke consumers,
open DevHub, fetch URLs, or mutate guardrail bundles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONSEQUENTIAL_ACTIONS = (
    "submit_permit_request",
    "certify_acknowledgement",
    "upload_to_official_record",
    "purchase_trade_permit",
    "schedule_inspection",
    "cancel_or_withdraw",
    "request_extension_or_reactivation",
    "enter_payment_details",
    "execute_payment",
)

BLOCKING_STATUSES = {"blocked", "blocker", "fail", "failed", "open", "missing", "stale"}
BLOCKING_SEVERITIES = {"critical", "high", "blocker"}
READY_STATES = {"ready", "complete", "passed", "pass", "ok"}


@dataclass(frozen=True)
class PacketIssue:
    issue_id: str
    source_packet: str
    summary: str
    citations: tuple[str, ...]
    reviewer_owner: str
    reason: str
    stale_evidence_acknowledgement: str | None = None


def reconcile_agent_readiness_release_blockers(
    guardrail_consumer_contract_audit: dict[str, Any],
    post_release_audit_findings: dict[str, Any],
    safe_next_action_user_handoff_checklist: dict[str, Any],
) -> dict[str, Any]:
    """Return an offline release blocker reconciliation packet.

    The caller supplies fixture or previously captured packet dictionaries. The
    returned packet is deterministic and commit-safe: it contains no private
    session data and explicitly attests that live actions remain disabled.
    """

    issues = [
        *_issues_from_guardrail_contract(guardrail_consumer_contract_audit),
        *_issues_from_post_release_audit(post_release_audit_findings),
        *_issues_from_handoff_checklist(safe_next_action_user_handoff_checklist),
    ]
    stale_acknowledgements = _stale_evidence_acknowledgements(
        guardrail_consumer_contract_audit,
        post_release_audit_findings,
        safe_next_action_user_handoff_checklist,
    )

    owner_map: dict[str, list[str]] = {}
    for issue in issues:
        owner_map.setdefault(issue.reviewer_owner, []).append(issue.issue_id)

    return {
        "packet_type": "ppd_agent_readiness_release_blocker_reconciliation",
        "packet_version": "1.0",
        "fixture_first": True,
        "live_actions_disabled": True,
        "consumers_invoked": False,
        "devhub_launched": False,
        "urls_fetched": False,
        "guardrail_bundles_changed": False,
        "input_packets": {
            "guardrail_consumer_contract_audit": _packet_ref(guardrail_consumer_contract_audit),
            "post_release_audit_findings": _packet_ref(post_release_audit_findings),
            "safe_next_action_user_handoff_checklist": _packet_ref(safe_next_action_user_handoff_checklist),
        },
        "remaining_blockers": [_issue_to_blocker(issue) for issue in issues],
        "reviewer_owners": [
            {"owner": owner, "blocker_ids": blocker_ids}
            for owner, blocker_ids in sorted(owner_map.items())
        ],
        "disabled_live_action_attestations": _disabled_live_action_attestations(),
        "stale_evidence_acknowledgements": stale_acknowledgements,
        "next_offline_daemon_recommendations": _next_offline_daemon_recommendations(issues, stale_acknowledgements),
    }


def _issues_from_guardrail_contract(packet: dict[str, Any]) -> list[PacketIssue]:
    issues: list[PacketIssue] = []
    for index, item in enumerate(_as_list(packet.get("remaining_blockers")) + _as_list(packet.get("consumer_blockers"))):
        issues.append(_packet_issue("guardrail_contract", item, index, "guardrail-contract-reviewer"))

    for index, finding in enumerate(_as_list(packet.get("findings"))):
        status = str(finding.get("status", "")).lower()
        severity = str(finding.get("severity", "")).lower()
        if status in BLOCKING_STATUSES or severity in BLOCKING_SEVERITIES:
            issues.append(_packet_issue("guardrail_contract", finding, index, "guardrail-contract-reviewer"))
    return _dedupe_issues(issues)


def _issues_from_post_release_audit(packet: dict[str, Any]) -> list[PacketIssue]:
    issues: list[PacketIssue] = []
    for index, finding in enumerate(_as_list(packet.get("findings"))):
        status = str(finding.get("status", "")).lower()
        severity = str(finding.get("severity", "")).lower()
        if status in BLOCKING_STATUSES or severity in BLOCKING_SEVERITIES:
            issues.append(_packet_issue("post_release_audit", finding, index, "post-release-audit-reviewer"))
    return _dedupe_issues(issues)


def _issues_from_handoff_checklist(packet: dict[str, Any]) -> list[PacketIssue]:
    issues: list[PacketIssue] = []
    for index, item in enumerate(_as_list(packet.get("items"))):
        state = str(item.get("state", item.get("status", "missing"))).lower()
        requires_attendance = bool(item.get("requires_user_attendance"))
        if state not in READY_STATES or requires_attendance:
            issues.append(_packet_issue("safe_next_action_handoff", item, index, "user-handoff-reviewer"))
    return _dedupe_issues(issues)


def _packet_issue(source_packet: str, item: dict[str, Any], index: int, fallback_owner: str) -> PacketIssue:
    item_id = str(item.get("id") or item.get("finding_id") or item.get("check_id") or f"{source_packet}-{index + 1}")
    citations = tuple(str(citation) for citation in _as_list(item.get("citations") or item.get("source_evidence_ids")))
    if not citations:
        citations = (f"{source_packet}:{item_id}",)
    stale_ack = item.get("stale_evidence_acknowledgement") or item.get("stale_reason")
    return PacketIssue(
        issue_id=item_id,
        source_packet=source_packet,
        summary=str(item.get("summary") or item.get("title") or item.get("description") or item_id),
        citations=citations,
        reviewer_owner=str(item.get("reviewer_owner") or item.get("owner") or fallback_owner),
        reason=str(item.get("reason") or item.get("status") or item.get("severity") or "release readiness blocker"),
        stale_evidence_acknowledgement=str(stale_ack) if stale_ack else None,
    )


def _issue_to_blocker(issue: PacketIssue) -> dict[str, Any]:
    blocker = {
        "blocker_id": issue.issue_id,
        "source_packet": issue.source_packet,
        "summary": issue.summary,
        "citations": list(issue.citations),
        "reviewer_owner": issue.reviewer_owner,
        "reason": issue.reason,
    }
    if issue.stale_evidence_acknowledgement:
        blocker["stale_evidence_acknowledgement"] = issue.stale_evidence_acknowledgement
    return blocker


def _stale_evidence_acknowledgements(*packets: dict[str, Any]) -> list[dict[str, Any]]:
    acknowledgements: list[dict[str, Any]] = []
    for packet in packets:
        packet_id = _packet_ref(packet)["packet_id"]
        for index, item in enumerate(_as_list(packet.get("stale_evidence"))):
            evidence_id = str(item.get("evidence_id") or item.get("id") or f"{packet_id}:stale:{index + 1}")
            acknowledgements.append(
                {
                    "evidence_id": evidence_id,
                    "packet_id": packet_id,
                    "acknowledgement": str(item.get("acknowledgement") or item.get("reason") or "Evidence is stale and must be refreshed before release."),
                    "citations": [str(citation) for citation in _as_list(item.get("citations") or item.get("source_evidence_ids"))] or [evidence_id],
                }
            )
    return acknowledgements


def _disabled_live_action_attestations() -> list[dict[str, Any]]:
    return [
        {
            "attestation_id": "release-blocker-reconciliation-live-actions-disabled",
            "live_actions_disabled": True,
            "prohibited_actions": list(CONSEQUENTIAL_ACTIONS),
            "attestation": "This reconciliation packet is fixture-first and must not invoke consumers, launch DevHub, fetch URLs, upload documents, submit, certify, schedule, cancel, or pay.",
        }
    ]


def _next_offline_daemon_recommendations(issues: list[PacketIssue], stale_acknowledgements: list[dict[str, Any]]) -> list[dict[str, str]]:
    recommendations = [
        {
            "recommendation_id": "offline-review-open-blockers",
            "summary": "Route cited remaining blockers to their reviewer owners before release enablement.",
            "mode": "offline_only",
        },
        {
            "recommendation_id": "offline-validate-fixtures",
            "summary": "Run deterministic fixture validation and syntax checks before any live crawl or authenticated automation.",
            "mode": "offline_only",
        },
        {
            "recommendation_id": "offline-keep-live-actions-disabled",
            "summary": "Keep consequential DevHub and payment actions disabled until blockers are resolved and exact-confirmation gates are re-reviewed.",
            "mode": "offline_only",
        },
    ]
    if stale_acknowledgements:
        recommendations.append(
            {
                "recommendation_id": "offline-refresh-stale-evidence-plan",
                "summary": "Prepare a source refresh plan for stale evidence without fetching URLs in this release blocker pass.",
                "mode": "offline_only",
            }
        )
    if not issues:
        recommendations.append(
            {
                "recommendation_id": "offline-record-no-blockers",
                "summary": "Record the no-open-blocker result with the same disabled live-action attestation.",
                "mode": "offline_only",
            }
        )
    return recommendations


def _packet_ref(packet: dict[str, Any]) -> dict[str, str]:
    return {
        "packet_id": str(packet.get("packet_id") or packet.get("id") or "unknown-packet"),
        "packet_type": str(packet.get("packet_type") or "unknown"),
    }


def _dedupe_issues(issues: list[PacketIssue]) -> list[PacketIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[PacketIssue] = []
    for issue in issues:
        key = (issue.source_packet, issue.issue_id)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
