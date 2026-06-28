from __future__ import annotations

import json
from pathlib import Path

from ppd.validation.post_recrawl_invalidation import validate_decision_queue


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_recrawl_invalidation"


def _messages(queue_name: str) -> list[str]:
    queue = json.loads((FIXTURE_DIR / queue_name).read_text(encoding="utf-8"))
    return [error.message for error in validate_decision_queue(queue)]


def test_accepts_public_cited_review_queue() -> None:
    assert _messages("valid_queue.json") == []


def test_rejects_missing_metadata_review_link() -> None:
    assert "missing metadata-review link" in _messages("missing_metadata_review_link.json")


def test_rejects_uncited_risk_decision() -> None:
    assert "risk decision must include at least one citation" in _messages("uncited_risk_decision.json")


def test_rejects_private_or_authenticated_evidence() -> None:
    assert "private or authenticated evidence is not allowed" in _messages("private_evidence.json")


def test_rejects_raw_body_excerpts_and_downloaded_paths() -> None:
    messages = _messages("raw_excerpt_and_download_path.json")
    assert "raw body excerpts are not allowed" in messages
    assert "downloaded document paths are not allowed" in messages


def test_rejects_skipped_reason_without_policy_code() -> None:
    assert "skipped decisions must include a policy code" in _messages("skipped_without_policy_code.json")


def test_rejects_direct_production_promotion() -> None:
    assert "direct production promotion is not allowed" in _messages("direct_production_promotion.json")
