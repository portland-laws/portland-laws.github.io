"""Mutation coverage for PP&D guardrail mapping confirmation gates.

The fixture is intentionally synthetic and public-only. It does not describe or
automate a real DevHub submission, upload, certification, cancellation,
inspection scheduling, or payment flow.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "confirmation_gate_mapping.json"
GATED_ACTION_CLASSES = {"potentially_consequential", "financial"}


def test_guardrail_mapping_requires_explicit_false_confirmation_for_gated_actions() -> None:
    fixture = _load_fixture()

    assert _validate_confirmation_gates(fixture) == []

    missing_confirmation = copy.deepcopy(fixture)
    missing_confirmation["guardrailMappings"][0].pop("explicitConfirmation")
    assert _validate_confirmation_gates(missing_confirmation) == [
        "guardrail mapping ppd.synthetic.submit-preview-gate: potentially_consequential actions require explicitConfirmation set to false by default"
    ]

    true_confirmation = copy.deepcopy(fixture)
    true_confirmation["guardrailMappings"][1]["explicitConfirmation"] = True
    assert _validate_confirmation_gates(true_confirmation) == [
        "guardrail mapping ppd.synthetic.payment-preview-gate: financial actions require explicitConfirmation set to false by default"
    ]


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    assert isinstance(data, dict)
    return data


def _validate_confirmation_gates(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    mappings = fixture.get("guardrailMappings", [])
    if not isinstance(mappings, list):
        return ["guardrailMappings must be a list"]

    for mapping in mappings:
        if not isinstance(mapping, dict):
            errors.append("guardrail mapping entries must be objects")
            continue
        mapping_id = str(mapping.get("mappingId", ""))
        action_class = str(mapping.get("actionClass", ""))
        if action_class in GATED_ACTION_CLASSES and mapping.get("explicitConfirmation") is not False:
            errors.append(
                f"guardrail mapping {mapping_id}: {action_class} actions require explicitConfirmation set to false by default"
            )

    return errors
