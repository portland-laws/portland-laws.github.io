from __future__ import annotations

from pathlib import Path

import pytest

from ppd.extraction.source_lineage import (
    SourceLineageError,
    lineage_index,
    load_public_source_lineage,
    public_source_lineage_dicts,
)


FIXTURES = Path(__file__).parent / "fixtures" / "public_source_lineage"


def test_load_public_source_lineage_from_committed_fixture() -> None:
    lineage = load_public_source_lineage(FIXTURES / "public_sources.json", fixtures_root=FIXTURES)

    assert [item.source_id for item in lineage] == ["ppd-online-tools", "devhub-public-portal"]
    assert lineage[0].fixture_path == "public_sources.json"
    assert lineage[0].content_hash.startswith("sha256:")
    assert lineage[0].evidence_id.startswith("evidence:")
    assert lineage[1].source_type == "devhub_public"


def test_public_source_lineage_dicts_are_json_ready() -> None:
    records = public_source_lineage_dicts(FIXTURES / "public_sources.json", fixtures_root=FIXTURES)

    assert records[0]["canonical_url"] == "https://www.portland.gov/ppd/how-use-online-permitting-tools"
    assert set(records[0]) == {
        "source_id",
        "canonical_url",
        "source_type",
        "title",
        "content_hash",
        "fixture_path",
        "evidence_id",
    }


def test_rejects_private_devhub_source_type(tmp_path: Path) -> None:
    fixture = tmp_path / "private_devhub.json"
    fixture.write_text(
        """
        {
          "sources": [
            {
              "source_id": "devhub-private-case",
              "canonical_url": "https://devhub.portlandoregon.gov/mypermits",
              "source_type": "devhub_authenticated",
              "title": "Private case list",
              "normalized_text": "private authenticated account data"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(SourceLineageError, match="non-public source type rejected"):
        load_public_source_lineage(fixture)


def test_rejects_sensitive_devhub_public_url(tmp_path: Path) -> None:
    fixture = tmp_path / "devhub_session.json"
    fixture.write_text(
        """
        {
          "sources": [
            {
              "source_id": "devhub-session",
              "canonical_url": "https://devhub.portlandoregon.gov/?session=abc123",
              "source_type": "devhub_public",
              "title": "DevHub session URL",
              "normalized_text": "session-bearing URL must not be accepted"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(SourceLineageError, match="sensitive query parameter rejected"):
        load_public_source_lineage(fixture)


def test_rejects_fixture_outside_supplied_root(tmp_path: Path) -> None:
    fixture = tmp_path / "public_sources.json"
    fixture.write_text("[]", encoding="utf-8")

    with pytest.raises(SourceLineageError, match="under the supplied fixtures root"):
        load_public_source_lineage(fixture, fixtures_root=FIXTURES)


def test_lineage_index_rejects_duplicate_source_ids() -> None:
    lineage = load_public_source_lineage(FIXTURES / "public_sources.json", fixtures_root=FIXTURES)

    with pytest.raises(SourceLineageError, match="duplicate source_id"):
        lineage_index([lineage[0], lineage[0]])

    assert set(lineage_index(lineage)) == {"ppd-online-tools", "devhub-public-portal"}
