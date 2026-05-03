from pathlib import Path

import pytest

from ppd.source_lineage import build_public_source_lineage_rollup, load_public_source_lineage_fixture


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_lineage" / "public_lineage_fixture.json"


def test_public_source_lineage_rollup_is_fixture_only() -> None:
    rollup = load_public_source_lineage_fixture(FIXTURE_PATH)

    assert rollup["fixture_only"] is True
    assert rollup["seed_url_count"] == 2
    assert rollup["normalized_document_ids"] == [
        "ppd:building-permit-application",
        "ppd:residential-permits",
    ]
    assert rollup["normalized_document_id_count"] == 2
    assert rollup["processor_handoff_manifests"] == [
        {
            "manifest_id": "fixture-public-guidance-001",
            "processor": "ppd-public-guidance-normalizer",
            "document_ids": [
                "ppd:building-permit-application",
                "ppd:residential-permits",
            ],
            "document_count": 2,
        }
    ]
    assert rollup["skipped_action_reasons"] == {
        "fixture_only_validation": 1,
        "public_lineage_only": 1,
        "raw_bodies_out_of_scope": 1,
    }


def test_public_source_lineage_rollup_rejects_raw_response_bodies() -> None:
    fixture = {
        "seed_urls": ["https://www.portland.gov/ppd/residential-permits"],
        "processor_handoff_manifests": [],
        "source_freshness_records": [],
        "skipped_actions": [],
        "response_body": "not allowed in committed lineage fixtures",
    }

    with pytest.raises(ValueError, match="raw response body field"):
        build_public_source_lineage_rollup(fixture)
