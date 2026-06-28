from pathlib import Path

import pytest

from ppd.evidence_pack import assemble_evidence_pack, load_fixture_documents


FIXTURES = Path(__file__).parent / "fixtures" / "evidence_pack"


def test_load_fixture_documents_uses_committed_fixture_path() -> None:
    documents = load_fixture_documents(FIXTURES)

    assert [document.id for document in documents] == ["ppd-fixture-appeal", "ppd-fixture-permit"]


def test_assemble_evidence_pack_is_deterministic_and_freshness_aware() -> None:
    first = assemble_evidence_pack(FIXTURES, generated_at="2026-05-12T00:00:00Z", max_age_days=30)
    second = assemble_evidence_pack(FIXTURES, generated_at="2026-05-12T00:00:00Z", max_age_days=30)

    assert first == second
    assert first["source_mode"] == "committed-fixtures-only"
    assert first["freshness"] == {
        "max_age_days": 30,
        "oldest_captured_at": "2026-05-01T12:00:00Z",
        "newest_captured_at": "2026-05-03T09:30:00Z",
        "is_stale": False,
    }
    assert [claim["id"] for claim in first["claims"]] == [
        "claim:ppd-fixture-appeal",
        "claim:ppd-fixture-permit",
    ]


def test_custom_claims_must_be_citation_backed() -> None:
    claims = [
        {
            "id": "claim:zoning-review",
            "text": "The fixture states that zoning review is required before permit issuance.",
            "citations": [
                {
                    "document_id": "ppd-fixture-permit",
                    "quote": "Zoning review must be completed before permit issuance.",
                }
            ],
        }
    ]

    pack = assemble_evidence_pack(FIXTURES, claims=claims)

    assert pack["claims"] == claims


def test_rejects_uncited_claims() -> None:
    with pytest.raises(ValueError, match="requires at least one citation"):
        assemble_evidence_pack(
            FIXTURES,
            claims=[{"id": "claim:bad", "text": "Unsupported claim", "citations": []}],
        )


def test_rejects_quotes_missing_from_fixture_text() -> None:
    with pytest.raises(ValueError, match="quote is not present"):
        assemble_evidence_pack(
            FIXTURES,
            claims=[
                {
                    "id": "claim:bad-quote",
                    "text": "Unsupported quote",
                    "citations": [
                        {"document_id": "ppd-fixture-permit", "quote": "This text is not in the fixture."}
                    ],
                }
            ],
        )
