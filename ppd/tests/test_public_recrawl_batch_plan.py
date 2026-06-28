from pathlib import Path

from ppd.public_recrawl_batch_plan import (
    build_public_recrawl_batch_plan,
    load_reviewed_public_registry,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_recrawl_registry_reviewed.json"


def test_build_public_recrawl_batch_plan_groups_reviewed_public_entries_only():
    entries = load_reviewed_public_registry(FIXTURE_PATH)

    plan = build_public_recrawl_batch_plan(entries)

    assert plan["plan_name"] == "ppd-public-recrawl-dry-run"
    assert plan["network_requests_allowed"] is False
    assert plan["output_mode"] == "metadata_only"
    assert len(plan["groups"]) == 2
    assert [group["cadence"] for group in plan["groups"]] == ["daily", "weekly"]
    daily = plan["groups"][0]
    assert daily == {
        "cadence": "daily",
        "host": "www.portland.gov",
        "rate_limit_bucket": "portland-gov-public-low",
        "robots_policy_evidence": "fixture:robots-reviewed-2026-05-08",
        "processor_contract": "ppd.contracts.documents:MetadataOnlyPublicRecord",
        "metadata_output_location": "ppd/output/metadata/public-recrawl/portland-gov/",
        "dry_run_execution_window": "2026-06-01T09:00:00Z/2026-06-01T09:15:00Z",
        "source_ids": ["ppd-inspections-public", "ppd-permit-search-public"],
        "network_requests_allowed": False,
        "output_mode": "metadata_only",
    }
    all_source_ids = {source_id for group in plan["groups"] for source_id in group["source_ids"]}
    assert "ppd-unreviewed-example" not in all_source_ids


def test_build_public_recrawl_batch_plan_requires_policy_and_contract_metadata():
    entries = load_reviewed_public_registry(FIXTURE_PATH)
    entries[0] = dict(entries[0])
    entries[0].pop("robots_policy_evidence")

    try:
        build_public_recrawl_batch_plan(entries)
    except ValueError as exc:
        assert "robots_policy_evidence" in str(exc)
    else:
        raise AssertionError("missing robots policy evidence should fail validation")
