from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub_accessible_tree_normalizer import (
    UnsafeDevHubFixtureError,
    normalize_devhub_accessible_tree,
)


FIXTURES = Path(__file__).parent / "fixtures" / "devhub_accessible_tree"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_normalizes_redacted_accessible_tree_to_surface_candidates() -> None:
    fixture = _load_fixture("synthetic_redacted_tree.json")

    candidates = normalize_devhub_accessible_tree(fixture)

    assert candidates == [
        {
            "surface_id": "devhub-devhub-permits-heading-apply-for-permits",
            "route": "/devhub/permits",
            "role": "heading",
            "name": "Apply for permits",
            "heading": "Apply for permits",
        },
        {
            "surface_id": "devhub-devhub-permits-link-residential-permit-status",
            "route": "/devhub/permits",
            "role": "link",
            "name": "Residential permit status",
            "heading": "Apply for permits",
        },
        {
            "surface_id": "devhub-devhub-permits-search-button-search-public-records",
            "route": "/devhub/permits/search",
            "role": "button",
            "name": "Search public records",
            "heading": "Find permit information",
        },
        {
            "surface_id": "devhub-devhub-permits-search-textbox-permit-number",
            "route": "/devhub/permits/search",
            "role": "textbox",
            "name": "Permit number",
            "heading": "Find permit information",
            "validation_message": "Use the public permit number format shown on the page.",
        },
    ]


def test_rejects_transactional_actions_and_private_artifacts() -> None:
    fixture = _load_fixture("unsafe_rejected_tree.json")

    with pytest.raises(UnsafeDevHubFixtureError):
        normalize_devhub_accessible_tree(fixture)


@pytest.mark.parametrize(
    "unsafe_fixture",
    [
        {"screenshot": "page.png", "nodes": []},
        {"trace": "trace.zip", "nodes": []},
        {"har": {"entries": []}, "nodes": []},
        {"auth_state": {"origin": "redacted"}, "nodes": []},
        {"cookies": [], "nodes": []},
        {"credentials": "redacted", "nodes": []},
        {"nodes": [{"role": "button", "name": "Upload file", "route": "/devhub"}]},
        {"nodes": [{"role": "button", "name": "Schedule inspection", "route": "/devhub"}]},
        {"nodes": [{"role": "button", "name": "Payment", "route": "/devhub"}]},
    ],
)
def test_rejects_forbidden_fixture_shapes(unsafe_fixture: dict) -> None:
    with pytest.raises(UnsafeDevHubFixtureError):
        normalize_devhub_accessible_tree(unsafe_fixture)
