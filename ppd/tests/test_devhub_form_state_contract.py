#!/usr/bin/env python3
"""Validate committed DevHub Playwright form-state fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ppd.contracts.devhub_form_state import devhub_form_state_fixture_from_dict


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_form_states.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_playwright_form_state_fixture_is_valid() -> None:
    fixture = devhub_form_state_fixture_from_dict(load_fixture())
    errors = fixture.validate()
    assert errors == []


def test_form_fields_include_required_selector_contract_parts() -> None:
    fixture = devhub_form_state_fixture_from_dict(load_fixture())
    assert fixture.fields
    for field in fixture.fields:
        selector = field.selector_basis
        assert selector.accessible_name
        assert selector.label_text
        assert selector.role.value
        assert selector.nearby_heading
        assert selector.url_state.stable_url == fixture.url_state.stable_url
        assert field.requirement_status.value in {"required", "optional", "conditionally_required", "unknown"}
        assert field.redacted_value.value.startswith("[") and field.redacted_value.value.endswith("]")


def test_contract_rejects_missing_accessible_name() -> None:
    data = load_fixture()
    data["fields"][0]["selectorBasis"]["accessibleName"] = ""
    fixture = devhub_form_state_fixture_from_dict(data)
    errors = fixture.validate()
    assert any("accessibleName is required" in error for error in errors)


def test_contract_rejects_unredacted_values() -> None:
    data = load_fixture()
    data["fields"][0]["redactedValue"]["value"] = "1234 SW Example Street"
    fixture = devhub_form_state_fixture_from_dict(data)
    errors = fixture.validate()
    assert any("redactedValue.value must be an approved redaction token" in error for error in errors)


def main() -> int:
    test_playwright_form_state_fixture_is_valid()
    test_form_fields_include_required_selector_contract_parts()
    test_contract_rejects_missing_accessible_name()
    test_contract_rejects_unredacted_values()
    print("DevHub Playwright form-state fixture contracts passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
