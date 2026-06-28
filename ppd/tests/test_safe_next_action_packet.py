from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.release_notes.safe_next_action_packet import build_safe_next_action_packet, load_packet_input

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "safe_next_action_packet"


def test_build_safe_next_action_packet_matches_fixture() -> None:
    source = load_packet_input(FIXTURE_DIR / "input.json")
    expected = json.loads((FIXTURE_DIR / "expected.json").read_text(encoding="utf-8"))

    assert build_safe_next_action_packet(source) == expected


def test_build_safe_next_action_packet_requires_all_sources() -> None:
    source = load_packet_input(FIXTURE_DIR / "input.json")
    source.pop("public_crawl_metadata_dry_run")

    with pytest.raises(ValueError, match="public_crawl_metadata_dry_run"):
        build_safe_next_action_packet(source)


def test_build_safe_next_action_packet_rejects_uncited_sources() -> None:
    source = load_packet_input(FIXTURE_DIR / "input.json")
    source["public_crawl_metadata_dry_run"].pop("source_id")

    with pytest.raises(ValueError, match="citation"):
        build_safe_next_action_packet(source)
