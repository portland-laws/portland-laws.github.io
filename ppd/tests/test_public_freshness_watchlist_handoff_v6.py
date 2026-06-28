from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "public_freshness_watchlist_handoff_v6.py"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_freshness_watchlist_v6"

spec = importlib.util.spec_from_file_location("public_freshness_watchlist_handoff_v6", MODULE_PATH)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def _expected_packet() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "expected_handoff.json").read_text(encoding="utf-8"))


def test_assembles_expected_fixture_first_handoff() -> None:
    expected = _expected_packet()
    actual = module.assemble_from_fixture_dir(FIXTURE_DIR)
    assert actual == expected
    module.validate_public_freshness_watchlist_handoff_v6(actual)


def test_handoff_excludes_live_or_authenticated_actions() -> None:
    actual = module.assemble_from_fixture_dir(FIXTURE_DIR)
    assert actual["mode"] == "fixture_first_offline_only"
    assert "live_crawl" in actual["excluded_actions"]
    assert "devhub_open" in actual["excluded_actions"]
    assert "private_document_read" in actual["excluded_actions"]
    assert "legal_or_permitting_guarantee" in actual["excluded_actions"]
    assert actual["offline_validation_commands"] == module.OFFLINE_VALIDATION_COMMANDS


@pytest.mark.parametrize(
    "field",
    [
        "consumed_fixture_references",
        "next_refresh_watch_rows",
        "stale_source_risk_notes",
        "citation_repair_owner_placeholders",
        "guarded_automation_hold_conditions",
        "offline_validation_commands",
    ],
)
def test_validation_rejects_missing_required_handoff_sections(field: str) -> None:
    packet = _expected_packet()
    packet.pop(field)

    with pytest.raises(module.PublicFreshnessWatchlistHandoffV6ValidationError):
        module.validate_public_freshness_watchlist_handoff_v6(packet)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "current_source_registry",
        "re_extraction",
        "guardrail_recompile",
        "inactive_activation_rehearsal",
        "smoke_replay",
        "rollback_drill",
        "agent_compatibility",
    ],
)
def test_validation_rejects_missing_consumed_fixture_references(fixture_name: str) -> None:
    packet = _expected_packet()
    del packet["consumed_fixture_references"][fixture_name]

    with pytest.raises(module.PublicFreshnessWatchlistHandoffV6ValidationError):
        module.validate_public_freshness_watchlist_handoff_v6(packet)


def test_validation_rejects_handoff_bundle_missing_required_fixture() -> None:
    bundle = module.load_fixture_bundle(FIXTURE_DIR)
    del bundle["re_extraction"]

    with pytest.raises(ValueError, match="missing fixture sections"):
        module.assemble_public_freshness_watchlist_handoff_v6(bundle)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("next_refresh_watch_rows",), []),
        (("stale_source_risk_notes",), []),
        (("citation_repair_owner_placeholders",), []),
        (("guarded_automation_hold_conditions",), []),
        (("next_refresh_watch_rows", 1, "hold_reasons"), []),
        (("citation_repair_owner_placeholders", 0, "owner_placeholder"), "assigned_reviewer"),
    ],
)
def test_validation_rejects_missing_rows_notes_placeholders_and_holds(path: tuple[object, ...], value: object) -> None:
    packet = _expected_packet()
    cursor: object = packet
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[path[-1]] = value  # type: ignore[index]

    with pytest.raises(module.PublicFreshnessWatchlistHandoffV6ValidationError):
        module.validate_public_freshness_watchlist_handoff_v6(packet)


@pytest.mark.parametrize(
    "blocked_patch",
    [
        {"live_crawl_executed": True},
        {"downloaded_pdf": "ppd/tests/fixtures/raw.pdf"},
        {"raw_crawl_artifact": "crawl-output.warc"},
        {"auth_state": {"token": "redacted"}},
        {"session_cookie": "redacted"},
        {"official_action_completion_claim": "submitted"},
        {"legal_or_permitting_guarantee_claim": "permit will be approved"},
        {"active_mutation": True},
        {"nested": {"storage_state": "state.json"}},
    ],
)
def test_validation_rejects_live_private_raw_official_guarantee_and_mutation_claims(blocked_patch: dict[str, object]) -> None:
    packet = _expected_packet()
    packet.update(copy.deepcopy(blocked_patch))

    with pytest.raises(module.PublicFreshnessWatchlistHandoffV6ValidationError):
        module.validate_public_freshness_watchlist_handoff_v6(packet)
