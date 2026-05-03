from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ppd.source_lineage_validation import validate_lineage_rollup

_FIXTURES = Path(__file__).parent / "fixtures" / "source_lineage"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_accepts_public_citation_backed_lineage_edges() -> None:
    result = validate_lineage_rollup(
        _load_fixture("valid_rollup.json"),
        today=date(2026, 5, 3),
    )

    assert result == {"ok": True, "errors": [], "review_needed_edges": []}


def test_rejects_private_devhub_artifacts_and_unstable_identifiers() -> None:
    result = validate_lineage_rollup(
        _load_fixture("private_artifact_rollup.json"),
        today=date(2026, 5, 3),
    )

    assert result["ok"] is False
    assert any("private DevHub artifact" in error for error in result["errors"])
    assert any("stable public identifier" in error for error in result["errors"])


def test_requires_review_needed_for_stale_or_conflicting_evidence() -> None:
    result = validate_lineage_rollup(
        _load_fixture("stale_conflict_rollup.json"),
        today=date(2026, 5, 3),
    )

    assert result["ok"] is False
    assert result["review_needed_edges"] == ["edge-stale-conflict"]
    assert any("not review_needed" in error for error in result["errors"])
