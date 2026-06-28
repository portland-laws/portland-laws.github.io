"""Fixture-first public freshness watchlist handoff v6.

This module intentionally reads only committed fixture inputs. It does not crawl,
download, authenticate, upload, submit, schedule, certify, pay, or make legal or
permitting guarantees.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

REQUIRED_FIXTURES = (
    "current_source_registry",
    "re_extraction",
    "guardrail_recompile",
    "inactive_activation_rehearsal",
    "smoke_replay",
    "rollback_drill",
    "agent_compatibility",
)

REQUIRED_FIXTURE_REFERENCES = {
    name: f"fixture:{name}.json" for name in REQUIRED_FIXTURES
}

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/public_freshness_watchlist_handoff_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_freshness_watchlist_handoff_v6.py"],
]

EXCLUDED_ACTIONS = [
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

BLOCKED_KEY_PARTS = (
    "live_crawl_executed",
    "crawl_executed",
    "downloaded",
    "raw_crawl",
    "raw_artifact",
    "raw_body",
    "raw_html",
    "raw_pdf",
    "session",
    "cookie",
    "auth",
    "storage_state",
    "browser_state",
    "trace",
    "har",
    "screenshot",
    "private_document",
    "official_action_completion",
    "completion_claim",
    "submitted",
    "uploaded",
    "certified",
    "paid",
    "scheduled",
    "legal_guarantee",
    "permitting_guarantee",
    "legal_or_permitting_guarantee",
    "active_mutation",
    "mutation_enabled",
    "mutations_enabled",
    "write_enabled",
)

ALLOWED_BLOCKED_KEY_PARTS = {
    "excluded_actions",
}


class PublicFreshnessWatchlistHandoffV6ValidationError(ValueError):
    """Raised when a public freshness watchlist handoff v6 packet is invalid."""


def load_fixture_bundle(fixture_dir: Path) -> dict[str, Any]:
    """Load the required fixture bundle from a local directory."""
    bundle: dict[str, Any] = {}
    for name in REQUIRED_FIXTURES:
        path = fixture_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing required fixture: {path}")
        with path.open("r", encoding="utf-8") as handle:
            bundle[name] = json.load(handle)
    return bundle


def assemble_public_freshness_watchlist_handoff_v6(bundle: dict[str, Any]) -> dict[str, Any]:
    """Assemble a deterministic public watchlist handoff from fixture data only."""
    missing = [name for name in REQUIRED_FIXTURES if name not in bundle]
    if missing:
        raise ValueError(f"missing fixture sections: {', '.join(missing)}")

    registry_sources = bundle["current_source_registry"].get("sources", [])
    re_extraction = bundle["re_extraction"].get("sources", {})
    smoke_replay = bundle["smoke_replay"].get("sources", {})
    rollback_drill = bundle["rollback_drill"].get("sources", {})
    compatibility = bundle["agent_compatibility"].get("sources", {})

    guardrail = bundle["guardrail_recompile"]
    rehearsal = bundle["inactive_activation_rehearsal"]

    guardrail_ok = guardrail.get("status") == "passed"
    rehearsal_ok = rehearsal.get("status") == "passed"

    rows: list[dict[str, Any]] = []
    risk_notes: list[dict[str, str]] = []
    repair_placeholders: list[dict[str, str]] = []

    for source in sorted(registry_sources, key=lambda item: item["source_id"]):
        source_id = source["source_id"]
        extraction_status = re_extraction.get(source_id, {}).get("status", "missing")
        smoke_status = smoke_replay.get(source_id, {}).get("status", "missing")
        rollback_status = rollback_drill.get(source_id, {}).get("status", "missing")
        agent_status = compatibility.get(source_id, {}).get("status", "missing")
        stale_days = int(source.get("stale_days", 0))
        citation_state = source.get("citation_state", "unknown")

        hold_reasons: list[str] = []
        if not guardrail_ok:
            hold_reasons.append("guardrail_recompile_not_passed")
        if not rehearsal_ok:
            hold_reasons.append("inactive_activation_rehearsal_not_passed")
        if extraction_status != "passed":
            hold_reasons.append("re_extraction_not_passed")
        if smoke_status != "passed":
            hold_reasons.append("smoke_replay_not_passed")
        if rollback_status != "passed":
            hold_reasons.append("rollback_drill_not_passed")
        if agent_status != "passed":
            hold_reasons.append("agent_compatibility_not_passed")

        if stale_days >= 30:
            risk_notes.append(
                {
                    "source_id": source_id,
                    "risk_note": f"Public source fixture is {stale_days} days old; refresh review remains fixture-only until holds clear.",
                }
            )

        if citation_state != "current":
            repair_placeholders.append(
                {
                    "source_id": source_id,
                    "owner_placeholder": "citation_repair_owner_tbd",
                    "reason": citation_state,
                }
            )

        rows.append(
            {
                "source_id": source_id,
                "public_url": source["public_url"],
                "next_refresh_after": source["next_refresh_after"],
                "stale_days": stale_days,
                "citation_state": citation_state,
                "automation_hold": bool(hold_reasons),
                "hold_reasons": hold_reasons,
            }
        )

    guarded_conditions = []
    if not guardrail_ok:
        guarded_conditions.append("guardrail_recompile_must_pass")
    if not rehearsal_ok:
        guarded_conditions.append("inactive_activation_rehearsal_must_pass")
    if any(row["automation_hold"] for row in rows):
        guarded_conditions.append("all_source_fixture_replays_must_pass")
    guarded_conditions.append("no_live_crawl_or_authenticated_automation_in_this_handoff")

    packet = {
        "handoff_version": "public_freshness_watchlist_v6",
        "mode": "fixture_first_offline_only",
        "consumed_fixture_references": dict(REQUIRED_FIXTURE_REFERENCES),
        "next_refresh_watch_rows": rows,
        "stale_source_risk_notes": risk_notes,
        "citation_repair_owner_placeholders": repair_placeholders,
        "guarded_automation_hold_conditions": guarded_conditions,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "excluded_actions": EXCLUDED_ACTIONS,
    }
    validate_public_freshness_watchlist_handoff_v6(packet)
    return packet


def validate_public_freshness_watchlist_handoff_v6(packet: Mapping[str, Any]) -> None:
    """Reject incomplete or unsafe public freshness watchlist handoff v6 packets."""
    if packet.get("handoff_version") != "public_freshness_watchlist_v6":
        raise PublicFreshnessWatchlistHandoffV6ValidationError("unexpected handoff_version")
    if packet.get("mode") != "fixture_first_offline_only":
        raise PublicFreshnessWatchlistHandoffV6ValidationError("handoff mode must be fixture_first_offline_only")

    _reject_blocked_claims_and_artifacts(packet, "$packet")

    references = packet.get("consumed_fixture_references")
    if references != REQUIRED_FIXTURE_REFERENCES:
        raise PublicFreshnessWatchlistHandoffV6ValidationError(
            "consumed_fixture_references must include registry, re-extraction, guardrail recompile, activation, smoke, rollback, and compatibility fixture references"
        )

    rows = packet.get("next_refresh_watch_rows")
    if not isinstance(rows, list) or not rows:
        raise PublicFreshnessWatchlistHandoffV6ValidationError("next_refresh_watch_rows must be a non-empty list")
    for row in rows:
        _validate_watch_row(row)

    _validate_source_note_rows(packet.get("stale_source_risk_notes"), "stale_source_risk_notes", "risk_note")
    _validate_citation_repair_placeholders(packet.get("citation_repair_owner_placeholders"))
    _require_non_empty_string_list(packet, "guarded_automation_hold_conditions")
    if "no_live_crawl_or_authenticated_automation_in_this_handoff" not in packet["guarded_automation_hold_conditions"]:
        raise PublicFreshnessWatchlistHandoffV6ValidationError("guarded automation hold conditions must include no-live-crawl/authenticated-automation hold")
    if packet.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        raise PublicFreshnessWatchlistHandoffV6ValidationError("offline validation commands must match the exact v6 command set")
    if packet.get("excluded_actions") != EXCLUDED_ACTIONS:
        raise PublicFreshnessWatchlistHandoffV6ValidationError("excluded_actions must match the required v6 safety exclusions")


def assemble_from_fixture_dir(fixture_dir: Path) -> dict[str, Any]:
    return assemble_public_freshness_watchlist_handoff_v6(load_fixture_bundle(fixture_dir))


def _validate_watch_row(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise PublicFreshnessWatchlistHandoffV6ValidationError("next refresh watch row must be an object")
    for key in ("source_id", "public_url", "next_refresh_after", "citation_state"):
        if not isinstance(value.get(key), str) or not value[key]:
            raise PublicFreshnessWatchlistHandoffV6ValidationError(f"watch row missing string field: {key}")
    if not isinstance(value.get("stale_days"), int):
        raise PublicFreshnessWatchlistHandoffV6ValidationError("watch row missing integer stale_days")
    if not isinstance(value.get("automation_hold"), bool):
        raise PublicFreshnessWatchlistHandoffV6ValidationError("watch row missing boolean automation_hold")
    hold_reasons = value.get("hold_reasons")
    if not isinstance(hold_reasons, list) or not all(isinstance(item, str) and item for item in hold_reasons):
        raise PublicFreshnessWatchlistHandoffV6ValidationError("watch row hold_reasons must be a list of strings")
    if value["automation_hold"] and not hold_reasons:
        raise PublicFreshnessWatchlistHandoffV6ValidationError("watch row with automation_hold must include hold_reasons")


def _validate_source_note_rows(value: Any, key: str, text_key: str) -> None:
    if not isinstance(value, list) or not value:
        raise PublicFreshnessWatchlistHandoffV6ValidationError(f"{key} must be a non-empty list")
    for row in value:
        if not isinstance(row, Mapping):
            raise PublicFreshnessWatchlistHandoffV6ValidationError(f"{key} row must be an object")
        for required_key in ("source_id", text_key):
            if not isinstance(row.get(required_key), str) or not row[required_key]:
                raise PublicFreshnessWatchlistHandoffV6ValidationError(f"{key} row missing {required_key}")


def _validate_citation_repair_placeholders(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise PublicFreshnessWatchlistHandoffV6ValidationError("citation_repair_owner_placeholders must be a non-empty list")
    for row in value:
        if not isinstance(row, Mapping):
            raise PublicFreshnessWatchlistHandoffV6ValidationError("citation repair placeholder row must be an object")
        for key in ("source_id", "owner_placeholder", "reason"):
            if not isinstance(row.get(key), str) or not row[key]:
                raise PublicFreshnessWatchlistHandoffV6ValidationError(f"citation repair placeholder missing {key}")
        if row["owner_placeholder"] != "citation_repair_owner_tbd":
            raise PublicFreshnessWatchlistHandoffV6ValidationError("citation repair owner placeholder must remain unassigned")


def _require_non_empty_string_list(parent: Mapping[str, Any], key: str) -> None:
    value = parent.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise PublicFreshnessWatchlistHandoffV6ValidationError(f"{key} must be a non-empty list of strings")


def _reject_blocked_claims_and_artifacts(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}"
            if key_text not in ALLOWED_BLOCKED_KEY_PARTS:
                if any(part in key_text for part in BLOCKED_KEY_PARTS) and child not in (None, False, "", []):
                    raise PublicFreshnessWatchlistHandoffV6ValidationError(
                        f"live crawl, raw/downloaded/private/auth artifact, official action, guarantee, or mutation claim is not allowed at {child_path}"
                    )
            _reject_blocked_claims_and_artifacts(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_blocked_claims_and_artifacts(child, f"{path}[{index}]")


def main() -> None:
    fixture_dir = Path(__file__).parent / "tests" / "fixtures" / "public_freshness_watchlist_v6"
    print(json.dumps(assemble_from_fixture_dir(fixture_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
