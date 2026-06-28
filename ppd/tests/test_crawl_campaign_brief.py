from __future__ import annotations

from pathlib import Path

from ppd.crawler.crawl_campaign_brief import campaign_batch_summary, load_campaign_brief, validate_campaign_brief


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "crawl_campaigns" / "portland_ppd_campaign_brief.json"


def test_campaign_brief_fixture_validates_without_network_access() -> None:
    brief = load_campaign_brief(FIXTURE_PATH)

    errors = validate_campaign_brief(brief)

    assert errors == []
    assert brief["scope"]["requires_authentication"] is False
    assert brief["campaign_defaults"]["body_retention"] == "forbidden"
    assert brief["campaign_defaults"]["respect_robots_txt"] is True


def test_campaign_brief_summary_is_deterministic() -> None:
    brief = load_campaign_brief(FIXTURE_PATH)

    summary = campaign_batch_summary(brief)

    assert summary == {
        "batch_count": 5,
        "public_html_seed_count": 16,
        "public_pdf_seed_count": 6,
        "devhub_public_route_count": 4,
    }


def test_campaign_brief_rejects_private_or_consequential_paths() -> None:
    brief = load_campaign_brief(FIXTURE_PATH)
    brief["permit_family_batches"][0]["public_html_seeds"].append("https://devhub.portlandoregon.gov/login")

    errors = validate_campaign_brief(brief)

    assert any("private or consequential path marker" in error for error in errors)

