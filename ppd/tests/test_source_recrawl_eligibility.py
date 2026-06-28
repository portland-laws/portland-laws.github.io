from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ppd.crawler.recrawl_eligibility import load_fixture_bundle, select_recrawl_candidates


def test_fixture_first_public_recrawl_candidates_are_deterministic() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "recrawl_eligibility"
    bundle = load_fixture_bundle(fixture_dir)

    candidates = select_recrawl_candidates(
        bundle["sources"],
        bundle["archive_manifests"],
        bundle["deferred_sources"],
        as_of=datetime(2026, 5, 14, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert candidates == [
        {
            "source_id": "devhub-faq",
            "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
            "source_type": "devhub_public",
            "crawl_frequency": "every_few_days",
            "last_seen_at": "2026-05-09T00:00:00Z",
            "freshness_status": "fresh",
            "prior_content_hash": "sha256:faq-old",
            "eligibility_reason": "crawl_frequency_due:every_few_days",
            "no_raw_body_persisted": True,
        },
        {
            "source_id": "forms-index",
            "canonical_url": "https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications",
            "source_type": "public_html",
            "crawl_frequency": "weekly",
            "last_seen_at": "2026-05-13T00:00:00Z",
            "freshness_status": "stale",
            "prior_content_hash": "sha256:forms-old",
            "eligibility_reason": "freshness_status:stale",
            "no_raw_body_persisted": True,
        },
        {
            "source_id": "submit-plans-online",
            "canonical_url": "https://www.portland.gov/ppd/get-permit/submit-plans-online",
            "source_type": "public_html",
            "crawl_frequency": "weekly",
            "last_seen_at": "2026-05-13T00:00:00Z",
            "freshness_status": "fresh",
            "prior_content_hash": None,
            "eligibility_reason": "missing_prior_archive_hash",
            "no_raw_body_persisted": True,
        },
    ]

    assert [candidate["source_id"] for candidate in candidates] == sorted(
        candidate["source_id"] for candidate in candidates
    )


def test_fixture_excludes_deferred_private_disallowed_and_fresh_sources() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "recrawl_eligibility"
    bundle = load_fixture_bundle(fixture_dir)

    candidates = select_recrawl_candidates(
        bundle["sources"],
        bundle["archive_manifests"],
        bundle["deferred_sources"],
        as_of=datetime(2026, 5, 14, 0, 0, 0, tzinfo=timezone.utc),
    )
    candidate_ids = {candidate["source_id"] for candidate in candidates}

    assert "fee-payment-guide" not in candidate_ids
    assert "devhub-auth-home" not in candidate_ids
    assert "outside-reference" not in candidate_ids
    assert "robots-blocked-example" not in candidate_ids
    assert "ppd-landing" not in candidate_ids
