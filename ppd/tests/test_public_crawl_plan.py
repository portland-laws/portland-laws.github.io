from pathlib import Path

from ppd.public_crawl_plan import generate_public_crawl_plan, load_seed_metadata


FIXTURE = Path(__file__).parent / "fixtures" / "public_crawl_plan" / "official_seed_metadata.json"


def test_generate_public_crawl_plan_is_offline_and_ordered():
    metadata = load_seed_metadata(FIXTURE)
    plan = generate_public_crawl_plan(metadata)

    assert plan["mode"] == "dry_run_public_crawl_plan"
    assert plan["network_requests_made"] is False
    assert plan["crawl_output_created"] is False

    intentions = plan["intentions"]
    assert [item["seed_id"] for item in intentions] == ["devhub-permits", "audit-report", "outside-domain"]
    assert all(item["no_raw_body_persisted"] is True for item in intentions)


def test_fetch_intentions_include_required_decisions():
    plan = generate_public_crawl_plan(load_seed_metadata(FIXTURE))
    by_id = {item["seed_id"]: item for item in plan["intentions"]}

    devhub = by_id["devhub-permits"]
    assert devhub["allowlist_decision"] == "allow"
    assert devhub["robots_preflight_status"] == "requires_live_check"
    assert devhub["crawl_frequency"] == "daily"
    assert devhub["processor_capability"] == "html_public_page"
    assert devhub["rate_limit_bucket"] == "portland-devhub-public"

    audit = by_id["audit-report"]
    assert audit["allowlist_decision"] == "allow"
    assert audit["processor_capability"] == "pdf_document"

    outside = by_id["outside-domain"]
    assert outside["allowlist_decision"] == "deny"
    assert outside["robots_preflight_status"] == "skipped_not_allowlisted"
