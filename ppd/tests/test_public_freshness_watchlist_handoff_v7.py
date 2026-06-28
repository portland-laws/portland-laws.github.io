from __future__ import annotations

from pathlib import Path

from ppd.public_freshness_watchlist_handoff_v7 import build_public_freshness_watchlist_handoff_v7


def test_public_freshness_watchlist_handoff_v7_is_fixture_first() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "public_freshness_watchlist_v7"

    handoff = build_public_freshness_watchlist_handoff_v7(fixture_dir)

    assert handoff["handoff_id"] == "public_freshness_watchlist_handoff_v7"
    assert handoff["mode"] == "fixture_first_offline_only"
    assert handoff["fixture_inputs"] == [
        "agent_api_compatibility_matrix_v7.json",
        "post_promotion_smoke_replay_plan_v7.json",
        "rollback_references_v7.json",
        "current_source_registry_v7.json",
    ]
    assert "live_crawl" in handoff["prohibited_actions"]
    assert "devhub_open" in handoff["prohibited_actions"]
    assert "legal_or_permitting_guarantee" in handoff["prohibited_actions"]
    assert len(handoff["next_refresh_watch_rows"]) == 2
    assert len(handoff["stale_source_risk_notes"]) == 2
    assert len(handoff["citation_repair_owner_placeholders"]) == 2
    assert handoff["offline_validation_commands"] == [
        ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
        ["python3", "-m", "pytest", "ppd/tests/test_public_freshness_watchlist_handoff_v7.py"],
    ]


def test_public_freshness_watchlist_rows_include_guards_and_references() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "public_freshness_watchlist_v7"

    handoff = build_public_freshness_watchlist_handoff_v7(fixture_dir)
    rows = {row["source_id"]: row for row in handoff["next_refresh_watch_rows"]}

    permits = rows["portland_maps_public_permits"]
    assert permits["agent_api_compatibility"] is True
    assert permits["post_promotion_smoke_replay"] == "post_promotion_smoke_replay_ready"
    assert permits["rollback_reference"].startswith("rollback://ppd/public-fixtures/")
    assert permits["citation_repair_owner_placeholder"] == "PPD_PUBLIC_CITATION_OWNER_TBD"
    assert handoff["public_recrawl_authorization_prerequisites"]
    assert handoff["guarded_automation_hold_conditions"]
