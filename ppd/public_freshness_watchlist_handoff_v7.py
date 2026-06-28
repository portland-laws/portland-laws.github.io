"""Fixture-first public freshness watchlist handoff v7.

This module assembles a deterministic public-source freshness handoff from
committed fixtures only. It does not crawl, authenticate, download, upload,
schedule, submit, pay, certify, or make legal/permitting guarantees.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).parent / "tests" / "fixtures" / "public_freshness_watchlist_v7"

VALIDATION_COMMANDS = [
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_freshness_watchlist_handoff_v7.py"],
]

PROHIBITED_ACTIONS = [
    "live_crawl",
    "raw_artifact_download",
    "devhub_open",
    "private_document_read",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantee",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_public_freshness_watchlist_handoff_v7(fixture_dir: Path | None = None) -> dict[str, Any]:
    """Build the v7 handoff from local fixtures only."""

    root = fixture_dir or FIXTURE_DIR
    matrix = _read_json(root / "agent_api_compatibility_matrix_v7.json")
    replay = _read_json(root / "post_promotion_smoke_replay_plan_v7.json")
    rollback = _read_json(root / "rollback_references_v7.json")
    registry = _read_json(root / "current_source_registry_v7.json")

    matrix_by_source = {item["source_id"]: item for item in matrix["sources"]}
    replay_by_source = {item["source_id"]: item for item in replay["sources"]}
    rollback_by_source = {item["source_id"]: item for item in rollback["sources"]}

    rows: list[dict[str, Any]] = []
    risk_notes: list[dict[str, str]] = []
    owner_placeholders: list[dict[str, str]] = []

    for source in registry["sources"]:
        source_id = source["source_id"]
        compatibility = matrix_by_source.get(source_id, {})
        smoke = replay_by_source.get(source_id, {})
        rollback_ref = rollback_by_source.get(source_id, {})

        notes: list[str] = []
        if not compatibility.get("agent_api_compatible", False):
            notes.append("agent API compatibility fixture is not green")
        if smoke.get("promotion_state") != "post_promotion_smoke_replay_ready":
            notes.append("post-promotion smoke replay fixture is not ready")
        if not source.get("last_public_registry_refresh_utc"):
            notes.append("current source registry fixture lacks a public refresh timestamp")

        rows.append(
            {
                "source_id": source_id,
                "label": source["label"],
                "public_url": source["public_url"],
                "next_refresh_window": source["next_refresh_window"],
                "last_public_registry_refresh_utc": source.get("last_public_registry_refresh_utc"),
                "agent_api_compatibility": compatibility.get("agent_api_compatible", False),
                "post_promotion_smoke_replay": smoke.get("promotion_state", "missing_fixture"),
                "rollback_reference": rollback_ref.get("rollback_reference", "missing_fixture"),
                "citation_repair_owner_placeholder": source.get("citation_repair_owner_placeholder", "PPD_PUBLIC_CITATION_OWNER_TBD"),
            }
        )
        risk_notes.append(
            {
                "source_id": source_id,
                "stale_source_risk_note": "; ".join(notes) if notes else "fixture inputs indicate public refresh can be prepared offline",
            }
        )
        owner_placeholders.append(
            {
                "source_id": source_id,
                "citation_repair_owner_placeholder": source.get("citation_repair_owner_placeholder", "PPD_PUBLIC_CITATION_OWNER_TBD"),
            }
        )

    return {
        "handoff_id": "public_freshness_watchlist_handoff_v7",
        "mode": "fixture_first_offline_only",
        "fixture_inputs": [
            "agent_api_compatibility_matrix_v7.json",
            "post_promotion_smoke_replay_plan_v7.json",
            "rollback_references_v7.json",
            "current_source_registry_v7.json",
        ],
        "prohibited_actions": PROHIBITED_ACTIONS,
        "next_refresh_watch_rows": rows,
        "stale_source_risk_notes": risk_notes,
        "citation_repair_owner_placeholders": owner_placeholders,
        "guarded_automation_hold_conditions": [
            "Hold if any source lacks agent API compatibility fixture coverage.",
            "Hold if any source lacks post-promotion smoke replay readiness fixture coverage.",
            "Hold if any source lacks a rollback reference fixture.",
            "Hold unless public recrawl authorization prerequisites are satisfied by a human owner outside this handoff.",
        ],
        "public_recrawl_authorization_prerequisites": [
            "Human owner confirms public-only scope.",
            "Human owner confirms no CAPTCHA, MFA, account creation, payment, submission, certification, cancellation, upload, or scheduling path is automated.",
            "Human owner confirms rollback reference remains available before any future authorized public recrawl.",
        ],
        "offline_validation_commands": VALIDATION_COMMANDS,
    }


if __name__ == "__main__":
    print(json.dumps(build_public_freshness_watchlist_handoff_v7(), indent=2, sort_keys=True))
