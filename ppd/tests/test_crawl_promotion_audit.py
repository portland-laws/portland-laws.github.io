from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.crawl_promotion_audit import audit_fixture_records, eligible_source_ids


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "crawl_promotion_audit" / "synthetic_fixture.json"


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_first_audit_promotes_only_complete_metadata_only_sources() -> None:
    fixture = load_fixture()

    rows = {row.source_id: row for row in audit_fixture_records(fixture)}

    promoted = rows["synthetic-permit-index"]
    assert promoted.eligible is True
    assert promoted.reasons == ()
    assert promoted.rate_limit_bucket == "synthetic-public-low-rate"
    assert promoted.processor == "html_metadata"
    assert promoted.metadata_only is True

    blocked = rows["synthetic-raw-document-risk"]
    assert blocked.eligible is False
    assert "output policy is not metadata-only" in blocked.reasons
    assert "output policy must reject raw document storage" in blocked.reasons

    assert eligible_source_ids(fixture) == ["synthetic-permit-index"]


def test_audit_rejects_missing_joined_gate_before_public_fetch_eligibility() -> None:
    fixture = load_fixture()
    fixture["robots_preflight"] = [
        record for record in fixture["robots_preflight"] if record["source_id"] != "synthetic-permit-index"
    ]

    rows = {row.source_id: row for row in audit_fixture_records(fixture)}

    assert rows["synthetic-permit-index"].eligible is False
    assert "missing joined records: robots_preflight" in rows["synthetic-permit-index"].reasons


def test_audit_requires_explicit_synthetic_fixture_kind() -> None:
    fixture = load_fixture()
    fixture["fixture_kind"] = "live_crawl"

    with pytest.raises(ValueError, match="fixture_kind"):
        audit_fixture_records(fixture)
