import json
from pathlib import Path

import pytest

from ppd.contracts.planned_crawl_manifest import planned_crawl_manifest_from_dict


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "planned_crawl_manifests" / "public_ppd_planned_fetches.json"


def test_planned_crawl_manifest_fixture_validates_without_response_bodies() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    manifest = planned_crawl_manifest_from_dict(data)

    assert manifest.stores_raw_response_bodies is False
    assert manifest.validate() == []
    assert [planned_fetch.id for planned_fetch in manifest.planned_fetches] == [
        "ppd-home",
        "devhub-public-home",
        "devhub-private-path-skipped",
    ]


def test_planned_crawl_manifest_rejects_response_body_keys() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["planned_fetches"][0]["response_body"] = "raw body must not be stored"

    with pytest.raises(ValueError, match="forbidden response/private keys"):
        planned_crawl_manifest_from_dict(data)


def test_planned_crawl_manifest_flags_private_devhub_paths() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    manifest = planned_crawl_manifest_from_dict(data)

    skipped = next(planned_fetch for planned_fetch in manifest.planned_fetches if planned_fetch.id == "devhub-private-path-skipped")

    assert skipped.decision.value == "skipped"
    assert any("private DevHub" in error for error in skipped.validate())
