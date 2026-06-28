from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "agent_readiness" / "operator_signoff_readiness.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "operator_signoff_readiness" / "operator_signoff_ledger.json"

spec = importlib.util.spec_from_file_location("operator_signoff_readiness", MODULE_PATH)
assert spec is not None
operator_signoff_readiness = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(operator_signoff_readiness)


def test_operator_signoff_packet_separates_approved_decisions_from_blockers() -> None:
    packet = operator_signoff_readiness.build_operator_signoff_readiness_packet(FIXTURE_PATH)

    assert packet["schema_version"] == "operator-signoff-implementation-readiness-packet.v1"
    assert packet["fixture_first"] is True
    assert packet["live_systems_touched"] is False
    assert packet["production_promotion_enabled"] is False
    assert packet["implementation_ready"] is False
    assert [decision["id"] for decision in packet["approved_review_decisions"]] == ["review-decision-001"]
    assert [blocker["id"] for blocker in packet["unresolved_blockers"]] == ["review-decision-002"]


def test_operator_signoff_packet_lists_exact_prerequisite_versions() -> None:
    packet = operator_signoff_readiness.build_operator_signoff_readiness_packet(
        FIXTURE_PATH,
        prerequisite_packet_versions={"implementation_readiness_packet": "operator-signoff-implementation-readiness-packet.v1"},
    )

    versions = packet["exact_prerequisite_packet_versions"]
    assert versions["crawl_scope_packet"] == "ppd-crawl-scope-packet.v1"
    assert versions["fixture_validation_packet"] == "ppd-fixture-validation-packet.v1"
    assert versions["operator_signoff_ledger"] == "operator-signoff-ledger.v1"
    assert versions["implementation_readiness_packet"] == "operator-signoff-implementation-readiness-packet.v1"
