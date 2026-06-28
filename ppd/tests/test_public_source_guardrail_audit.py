from pathlib import Path

from ppd.traceability.public_source_guardrail_audit import (
    build_audit_packet,
    load_json_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "traceability"


def test_public_source_to_guardrail_traceability_audit_packet() -> None:
    freshness = load_json_packet(FIXTURE_DIR / "public_source_freshness_review_packet.json")
    requirements = load_json_packet(
        FIXTURE_DIR / "requirement_regeneration_promotion_decision_packet.json"
    )
    guardrails = load_json_packet(FIXTURE_DIR / "guardrail_activation_decision_packet.json")

    audit = build_audit_packet(freshness, requirements, guardrails)

    assert audit["side_effects"] == {
        "fetched_urls": False,
        "mutated_active_bundles": False,
    }
    assert audit["cited_source_ids"] == [
        "SRC-PPD-FEE-PAYMENT-GUIDE",
        "SRC-PPD-MISSING-BUNDLE-SOURCE",
        "SRC-PPD-NOT-IN-FRESHNESS-PACKET",
        "SRC-PPD-ONLINE-TOOLS",
    ]
    assert audit["requirement_ids"] == [
        "REQ-DEVHUB-ACCOUNT-SERVICES",
        "REQ-FEE-PAYMENT-BLOCKED",
        "REQ-MISSING-SOURCE-TRACE",
    ]
    assert audit["guardrail_bundle_ids"] == [
        "GB-DEVHUB-READONLY-ACTIONS",
        "GB-FEE-PAYMENT-STOP-GATE",
    ]
    assert audit["stale_source_acknowledgements"] == [
        {
            "source_id": "SRC-PPD-FEE-PAYMENT-GUIDE",
            "reviewer_owner": "ppd-fee-reviewer",
            "acknowledged_at": "2026-05-28",
            "rationale": "Fee payment guardrails remain blocked from payment execution while the source waits for refresh.",
        }
    ]
    assert audit["reviewer_owners"] == [
        "ppd-fee-reviewer",
        "ppd-gap-reviewer",
        "ppd-guardrail-reviewer",
        "ppd-requirements-reviewer",
    ]

    gap_types = {gap["gap_type"] for gap in audit["unresolved_traceability_gaps"]}
    assert gap_types == {
        "guardrail_bundle_cites_unknown_source",
        "guardrail_bundle_references_unpromoted_requirement",
        "requirement_cites_unknown_source",
        "stale_source_without_acknowledgement",
    }


def test_rejects_duplicate_packet_ids() -> None:
    freshness = {
        "sources": [
            {"source_id": "SRC-DUP", "freshness_status": "current"},
            {"source_id": "SRC-DUP", "freshness_status": "current"},
        ]
    }

    try:
        build_audit_packet(freshness, {"requirements": []}, {"guardrail_bundles": []})
    except ValueError as exc:
        assert "duplicate freshness source id: SRC-DUP" in str(exc)
    else:
        raise AssertionError("duplicate source IDs must be rejected")
