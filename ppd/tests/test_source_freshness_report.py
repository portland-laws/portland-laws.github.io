from pathlib import Path

from ppd.extraction.source_freshness_report import (
    SourceFreshnessPolicy,
    build_source_freshness_report,
    load_source_observations,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_freshness"


def test_build_source_freshness_report_preserves_required_ids_and_statuses() -> None:
    observations = load_source_observations(FIXTURE_DIR / "observations.json")

    report = build_source_freshness_report(
        observations,
        as_of="2026-05-12T00:00:00Z",
        policy=SourceFreshnessPolicy(stale_after_days=30),
    )

    assert report == {
        "as_of": "2026-05-12T00:00:00Z",
        "stale_after_days": 30,
        "source_count": 3,
        "status_counts": {"fresh": 1, "missing": 1, "stale": 1},
        "affected_guardrail_bundle_ids": ["appeals", "inspections"],
        "sources": [
            {
                "source_id": "appeals-board",
                "citation_id": "ppd:citation:appeals-board",
                "last_seen_at": "2026-03-01T00:00:00Z",
                "freshness_status": "stale",
                "age_days": 72,
                "guardrail_bundle_ids": ["appeals"],
            },
            {
                "source_id": "inspection-manual",
                "citation_id": "ppd:citation:inspection-manual",
                "last_seen_at": None,
                "freshness_status": "missing",
                "age_days": None,
                "guardrail_bundle_ids": ["inspections"],
            },
            {
                "source_id": "permit-search",
                "citation_id": "ppd:citation:permit-search",
                "last_seen_at": "2026-05-10T00:00:00Z",
                "freshness_status": "fresh",
                "age_days": 2,
                "guardrail_bundle_ids": ["intake", "permits"],
            },
        ],
    }


def test_build_source_freshness_report_is_deterministic_for_input_order() -> None:
    observations = load_source_observations(FIXTURE_DIR / "observations.json")

    first = build_source_freshness_report(observations, as_of="2026-05-12")
    second = build_source_freshness_report(reversed(observations), as_of="2026-05-12")

    assert first == second
