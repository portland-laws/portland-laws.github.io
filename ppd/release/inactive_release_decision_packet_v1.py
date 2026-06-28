"""Fixture-first inactive release decision packet v1.

This module intentionally consumes caller-provided rows only. It does not crawl,
promote releases, open DevHub, persist private artifacts, or perform official
actions.
"""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from typing import Any

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_release_decision_packet_v1.py"],
]

PROHIBITED_ACTIONS = [
    "release promotion",
    "live crawling",
    "opening DevHub",
    "storing private artifacts",
    "official actions",
]


def _topological_order(rows: list[dict[str, Any]]) -> list[str]:
    ids = [str(row["candidate_id"]) for row in rows]
    known = set(ids)
    indegree = {candidate_id: 0 for candidate_id in ids}
    children: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        candidate_id = str(row["candidate_id"])
        for dependency_id in row.get("dependency_ids", []):
            dependency = str(dependency_id)
            if dependency in known:
                indegree[candidate_id] += 1
                children[dependency].append(candidate_id)

    ready = deque(sorted(candidate_id for candidate_id, degree in indegree.items() if degree == 0))
    ordered: list[str] = []
    while ready:
        candidate_id = ready.popleft()
        ordered.append(candidate_id)
        for child in sorted(children[candidate_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if len(ordered) != len(ids):
        unresolved = sorted(set(ids) - set(ordered))
        ordered.extend(unresolved)
    return ordered


def build_decision_packet(
    candidate_rows: list[dict[str, Any]], readiness_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    candidates = {str(row["candidate_id"]): deepcopy(row) for row in candidate_rows}
    readiness_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in readiness_rows:
        readiness_by_candidate[str(row["candidate_id"])].append(deepcopy(row))

    decisions_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids = _topological_order(candidate_rows)

    for candidate_id in ordered_ids:
        candidate = candidates[candidate_id]
        readiness = readiness_by_candidate.get(candidate_id, [])
        blockers = list(candidate.get("release_blockers", []))
        rollback_notes = list(candidate.get("rollback_notes", []))
        smoke_requirements: list[str] = []

        guardrail_status = str(candidate.get("guardrail_status", "hold")).lower()
        readiness_statuses = [str(row.get("replay_status", "missing")).lower() for row in readiness]
        failed_agents = [str(row.get("agent", "unknown")) for row in readiness if str(row.get("replay_status", "missing")).lower() == "fail"]
        missing_readiness = not readiness

        for row in readiness:
            if bool(row.get("smoke_replay_required", False)):
                smoke_requirements.append(str(row.get("smoke_replay", "rerun targeted smoke replay")))

        dependency_ids = [str(value) for value in candidate.get("dependency_ids", [])]
        dependency_decisions = {
            dependency_id: decisions_by_id.get(dependency_id, {"decision": "hold"})["decision"]
            for dependency_id in dependency_ids
        }
        rejected_dependencies = [key for key, value in dependency_decisions.items() if value == "reject"]
        unapproved_dependencies = [key for key, value in dependency_decisions.items() if value != "approve"]

        if guardrail_status in {"reject", "fail", "failed"}:
            decision = "reject"
            blockers.append("inactive guardrail failed")
        elif failed_agents:
            decision = "reject"
            blockers.append("post-recompile readiness replay failed: " + ", ".join(sorted(failed_agents)))
        elif rejected_dependencies:
            decision = "reject"
            blockers.append("dependency rejected: " + ", ".join(sorted(rejected_dependencies)))
        elif guardrail_status in {"hold", "pending"}:
            decision = "hold"
            blockers.append("inactive guardrail requires human review")
        elif missing_readiness:
            decision = "hold"
            blockers.append("post-recompile readiness replay row missing")
        elif unapproved_dependencies:
            decision = "hold"
            blockers.append("dependency not approved: " + ", ".join(sorted(unapproved_dependencies)))
        elif smoke_requirements:
            decision = "hold"
            blockers.append("smoke replay required before approval")
        elif all(status == "pass" for status in readiness_statuses):
            decision = "approve"
        else:
            decision = "hold"
            blockers.append("readiness replay status is incomplete")

        if not rollback_notes:
            rollback_notes.append("No promotion was performed; rollback is limited to discarding this packet.")

        decisions_by_id[candidate_id] = {
            "candidate_id": candidate_id,
            "ordinance_id": str(candidate.get("ordinance_id", "")),
            "decision": decision,
            "dependency_ids": dependency_ids,
            "dependency_decisions": dependency_decisions,
            "human_reviewer_route": str(candidate.get("human_reviewer_route", "ppd-release-review")),
            "release_blocker_summary": sorted(set(blockers)),
            "smoke_replay_requirements": sorted(set(smoke_requirements)),
            "rollback_notes": rollback_notes,
        }

    return {
        "schema_version": "fixture-first.inactive-release-decision-packet.v1",
        "source": "synthetic fixtures only",
        "prohibited_actions": PROHIBITED_ACTIONS,
        "validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "dependency_order": ordered_ids,
        "decisions": [decisions_by_id[candidate_id] for candidate_id in ordered_ids],
    }
