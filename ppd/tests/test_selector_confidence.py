from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.selector_confidence import (
    SelectorConfidenceError,
    assert_draft_fill_selector_confidence,
    check_draft_fill_selector_confidence,
)


FIXTURES = Path(__file__).parent / "fixtures" / "selector_confidence"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_clear_surface_map_allows_draft_fill() -> None:
    result = assert_draft_fill_selector_confidence(_fixture("clear_surface_map.json"))

    assert result.allowed is True
    assert result.problems == ()


def test_ambiguous_surface_map_blocks_draft_fill() -> None:
    result = check_draft_fill_selector_confidence(_fixture("ambiguous_surface_map.json"))

    assert result.allowed is False
    assert "ambiguous label evidence: project name" in result.problems
    assert "ambiguous heading evidence: permit draft" in result.problems
    assert "ambiguous route evidence: /permits/draft" in result.problems


def test_assert_raises_for_ambiguous_surface_map() -> None:
    with pytest.raises(SelectorConfidenceError) as excinfo:
        assert_draft_fill_selector_confidence(_fixture("ambiguous_surface_map.json"))

    assert "ambiguous label evidence" in str(excinfo.value)
