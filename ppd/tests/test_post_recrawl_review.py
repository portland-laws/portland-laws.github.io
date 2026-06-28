from __future__ import annotations

from pathlib import Path
import json

from ppd.extraction.post_recrawl_review import validate_post_recrawl_review_packet

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_recrawl_review"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _issue_codes(packet: dict) -> set[str]:
    return {issue.code for issue in validate_post_recrawl_review_packet(packet).issues}


def test_accepts_metadata_only_review_packet() -> None:
    report = validate_post_recrawl_review_packet(_load_fixture("valid_metadata_packet.json"))

    assert report.ok is True
    assert report.issues == ()


def test_rejects_raw_html_and_pdf_excerpts() -> None:
    packet = _load_fixture("valid_metadata_packet.json")
    packet["review_notes"] = [
        "raw public page body",
        "%PDF-1.7 xref startxref",
    ]

    assert "raw_excerpt_forbidden" in _issue_codes(packet)


def test_rejects_private_authenticated_evidence_and_downloaded_paths() -> None:
    packet = _load_fixture("valid_metadata_packet.json")
    packet["evidence"] = [
        {
            "source_type": "devhub_authenticated",
            "privacy_classification": "private",
            "url": "https://devhub.portlandoregon.gov/account/my-permits",
        },
        {"downloaded_path": "/home/example/Downloads/permit-guide.pdf"},
    ]

    codes = _issue_codes(packet)

    assert "authenticated_evidence_forbidden" in codes
    assert "private_evidence_forbidden" in codes
    assert "downloaded_path_forbidden" in codes


def test_rejects_uncited_changed_hash_claim() -> None:
    packet = _load_fixture("valid_metadata_packet.json")
    packet["changed_sources"] = [{"content_hash_changed": True}]

    assert "uncited_changed_hash_claim" in _issue_codes(packet)


def test_rejects_missing_skipped_reason_code() -> None:
    packet = _load_fixture("valid_metadata_packet.json")
    packet["skipped_sources"] = [{"source_id": "src-devhub-private"}]

    assert "missing_skipped_reason_code" in _issue_codes(packet)


def test_rejects_missing_downstream_invalidation_links() -> None:
    packet = _load_fixture("valid_metadata_packet.json")
    packet["downstream_invalidations"] = []

    assert "missing_downstream_invalidation_links" in _issue_codes(packet)


def test_rejects_direct_guardrail_or_process_promotion() -> None:
    packet = _load_fixture("valid_metadata_packet.json")
    packet["review_decisions"] = [
        {
            "action": "promote guardrail bundle after recrawl",
            "status": "approved process model",
        }
    ]

    assert "direct_promotion_forbidden" in _issue_codes(packet)
