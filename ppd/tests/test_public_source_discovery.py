from pathlib import Path

from ppd.crawler.public_source_discovery import (
    ALLOWED_HOSTS,
    SKIP_REASON_CODES,
    allowed_records,
    canonicalize_url,
    load_discovery_index,
    validate_discovery_index,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_source_discovery"
    / "ppd_seed_discovery_index.json"
)

EXPECTED_OFFICIAL_SEEDS = {
    "https://www.portland.gov/ppd",
    "https://www.portland.gov/ppd/how-use-online-permitting-tools",
    "https://devhub.portlandoregon.gov",
    "https://www.portland.gov/ppd/devhub-faqs",
    "https://www.portland.gov/ppd/devhub-sign-guide",
    "https://www.portland.gov/ppd/get-permit/apply-permits",
    "https://www.portland.gov/ppd/devhub-guide-submit-permit-application",
    "https://www.portland.gov/ppd/get-permit/submit-plans-online",
    "https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications",
    "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
    "https://www.portland.gov/ppd/documents/how-pay-fees/download",
    "https://www.portlandmaps.com",
}


def test_fixture_only_discovery_index_validates() -> None:
    index = load_discovery_index(FIXTURE_PATH)

    assert validate_discovery_index(index) == []
    assert index["metadata"]["fixture_only"] is True
    assert index["metadata"]["no_live_crawl"] is True
    assert index["metadata"]["no_raw_page_bodies"] is True
    assert set(index["metadata"]["allowed_hosts"]) == ALLOWED_HOSTS
    assert set(index["metadata"]["skip_reason_codes"]) == SKIP_REASON_CODES


def test_fixture_records_all_expected_official_seed_urls() -> None:
    index = load_discovery_index(FIXTURE_PATH)
    fixture_urls = {record["canonical_url"] for record in index["records"]}

    assert EXPECTED_OFFICIAL_SEEDS.issubset(fixture_urls)


def test_allowed_records_are_public_allowlisted_sources() -> None:
    index = load_discovery_index(FIXTURE_PATH)
    allowed = allowed_records(index)

    assert allowed
    for record in allowed:
        assert record["decision"] == "allow"
        assert record["skip_reason_code"] is None
        assert canonicalize_url(record["canonical_url"]) == record["canonical_url"]
        assert record["canonical_url"].startswith("https://")


def test_skip_records_preserve_reason_codes_without_raw_bodies() -> None:
    index = load_discovery_index(FIXTURE_PATH)
    skipped = [record for record in index["records"] if record["decision"] == "skip"]

    assert skipped
    assert {record["skip_reason_code"] for record in skipped}.issubset(SKIP_REASON_CODES)
    assert "raw_download_not_permitted" in {record["skip_reason_code"] for record in skipped}
    assert "private_authenticated" in {record["skip_reason_code"] for record in skipped}
    assert "outside_allowlist" in {record["skip_reason_code"] for record in skipped}
    assert "unsupported_scheme" in {record["skip_reason_code"] for record in skipped}
    assert "raw_body" not in index


def test_canonicalize_url_strips_fragments_default_ports_and_trailing_slashes() -> None:
    assert (
        canonicalize_url("HTTPS://WWW.PORTLAND.GOV:443/ppd/devhub-faqs/#account")
        == "https://www.portland.gov/ppd/devhub-faqs"
    )
    assert (
        canonicalize_url("https://devhub.portlandoregon.gov/")
        == "https://devhub.portlandoregon.gov"
    )
