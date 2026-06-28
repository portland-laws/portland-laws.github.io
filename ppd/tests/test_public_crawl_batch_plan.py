from __future__ import annotations

from pathlib import Path

from ppd.crawler.public_crawl_batch_plan import (
    ALLOWED_PUBLIC_HOSTS,
    canonicalize_public_url,
    load_seed_fixture,
    normalize_public_crawl_batch_plan,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_crawl_batch_plan" / "seeds.json"


def _fixture_plan() -> dict:
    return normalize_public_crawl_batch_plan(load_seed_fixture(FIXTURE_PATH))


def test_normalizer_uses_only_committed_fixture_and_no_network_or_raw_body_policy() -> None:
    plan = _fixture_plan()

    assert plan["plan_version"] == "ppd-public-crawl-batch-plan-v1"
    assert plan["network_io_permitted"] is False
    assert plan["raw_body_persistence_permitted"] is False
    assert plan["allowed_hosts"] == sorted(ALLOWED_PUBLIC_HOSTS)
    assert plan["summary"] == {
        "total_unique_records": 9,
        "included_records": 6,
        "skipped_records": 3,
        "duplicate_records": 1,
    }

    for record in plan["records"]:
        assert record["fetch_mode"] == "not_fetched_fixture_plan_only"
        assert record["no_raw_body_persisted"] is True
        assert record["raw_body_ref"] is None
        assert record["processor_policy"] == "metadata_and_normalized_text_only"
        assert record["privacy_classification"] == "public"


def test_normalizer_deduplicates_and_canonicalizes_urls_deterministically() -> None:
    plan = _fixture_plan()

    canonical_urls = [record["canonical_url"] for record in plan["records"]]
    assert canonical_urls == sorted(canonical_urls)
    assert canonical_urls.count("https://www.portland.gov/ppd") == 1
    assert plan["skipped_duplicates"] == [
        {
            "canonical_url": "https://www.portland.gov/ppd",
            "skipped_reason": "duplicate_canonical_url",
        }
    ]
    assert (
        canonicalize_public_url(
            "https://www.portland.gov/ppd/devhub-guide-submit-permit-application?b=2&a=1#steps"
        )
        == "https://www.portland.gov/ppd/devhub-guide-submit-permit-application?a=1&b=2"
    )


def test_normalizer_keeps_the_public_source_allowlist_narrow() -> None:
    plan = _fixture_plan()

    assert set(plan["allowed_hosts"]) == {
        "devhub.portlandoregon.gov",
        "www.portland.gov",
        "www.portlandmaps.com",
        "www.portlandoregon.gov",
    }
    records = {record["canonical_url"]: record for record in plan["records"]}
    assert records["https://example.com/not-allowed"]["decision"] == "skip"
    assert records["https://example.com/not-allowed"]["skipped_reason"] == "outside_allowlist"
    assert records["ftp://www.portland.gov/ppd/file.pdf"]["decision"] == "skip"
    assert records["ftp://www.portland.gov/ppd/file.pdf"]["skipped_reason"] == "unsupported_scheme"


def test_normalizer_marks_private_or_authenticated_paths_as_skipped() -> None:
    plan = _fixture_plan()
    records = {record["canonical_url"]: record for record in plan["records"]}

    private_record = records["https://devhub.portlandoregon.gov/login"]
    assert private_record["decision"] == "skip"
    assert private_record["skipped_reason"] == "private_or_authenticated"
    assert private_record["requires_authentication"] is True


def test_normalizer_classifies_public_source_types_without_downloading_pdfs() -> None:
    plan = _fixture_plan()
    records = {record["canonical_url"]: record for record in plan["records"]}

    assert records["https://www.portland.gov/ppd"]["source_type"] == "public_html"
    assert records["https://devhub.portlandoregon.gov/"]["source_type"] == "devhub_public"
    assert records["https://www.portlandmaps.com/detail/property/1234"]["source_type"] == "external_reference"

    pdf_record = records["https://www.portland.gov/ppd/documents/how-pay-fees/download"]
    assert pdf_record["source_type"] == "public_pdf"
    assert pdf_record["decision"] == "include"
    assert pdf_record["fetch_mode"] == "not_fetched_fixture_plan_only"
    assert pdf_record["no_raw_body_persisted"] is True
