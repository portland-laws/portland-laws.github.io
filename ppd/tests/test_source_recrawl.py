from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from ppd.crawler.source_recrawl import load_recrawl_decisions, source_recrawl_decision


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_recrawl" / "source_registry.json"
AS_OF = datetime(2026, 5, 14, tzinfo=UTC)


def test_recrawl_decisions_preserve_source_identity_frequency_and_skip_reasons() -> None:
    decisions = {decision.source_id: decision for decision in load_recrawl_decisions(FIXTURE_PATH, as_of=AS_OF)}

    devhub_faq = decisions["ppd:public:devhub-faq"]
    assert devhub_faq.eligible is True
    assert devhub_faq.reason == "stale:daily"
    assert devhub_faq.citation_source_id == "ppd:public:devhub-faq"
    assert devhub_faq.crawl_frequency == "daily"

    file_standards = decisions["ppd:public:file-standards"]
    assert file_standards.eligible is False
    assert file_standards.reason == "fresh:weekly"
    assert file_standards.next_recrawl_after == "2026-05-17T00:00:00Z"

    private_devhub = decisions["ppd:devhub:account-home"]
    assert private_devhub.eligible is False
    assert private_devhub.reason == "private/authenticated"
    assert private_devhub.skip_reason == "private/authenticated"
    assert private_devhub.crawl_frequency == "manual"


def test_never_seen_public_source_is_eligible_without_raw_body() -> None:
    decisions = {decision.source_id: decision for decision in load_recrawl_decisions(FIXTURE_PATH, as_of=AS_OF)}

    forms_index = decisions["ppd:public:forms-index"]
    as_dict = forms_index.to_dict()
    assert forms_index.eligible is True
    assert forms_index.reason == "never_seen"
    assert forms_index.last_seen_at is None
    assert forms_index.no_raw_body_persisted is True
    assert "raw_body" not in as_dict
    assert "body" not in as_dict
    assert "html" not in as_dict
    assert "text" not in as_dict


def test_raw_body_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="raw body"):
        source_recrawl_decision(
            {
                "source_id": "ppd:public:bad-raw-fixture",
                "canonical_url": "https://www.portland.gov/ppd",
                "crawl_frequency": "daily",
                "last_seen_at": "2026-05-01T00:00:00Z",
                "no_raw_body_persisted": True,
                "raw_body": "not commit safe",
            },
            as_of=AS_OF,
        )


def test_source_ids_must_be_citation_ready() -> None:
    with pytest.raises(ValueError, match="citation-ready"):
        source_recrawl_decision(
            {
                "source_id": "DevHub FAQ",
                "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
                "crawl_frequency": "daily",
                "last_seen_at": "2026-05-01T00:00:00Z",
                "no_raw_body_persisted": True,
            },
            as_of=AS_OF,
        )


def test_no_raw_body_persistence_must_be_explicitly_preserved_when_false_is_seen() -> None:
    with pytest.raises(ValueError, match="no raw body"):
        source_recrawl_decision(
            {
                "source_id": "ppd:public:false-no-raw-guarantee",
                "canonical_url": "https://www.portland.gov/ppd",
                "crawl_frequency": "daily",
                "last_seen_at": "2026-05-01T00:00:00Z",
                "no_raw_body_persisted": False,
            },
            as_of=AS_OF,
        )
