from __future__ import annotations

import json
from pathlib import Path

from ppd.process_model_compiler import compile_archived_requirement_set


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "process_model"
    / "archived_ppd_simple_trade_permit_requirement_set.json"
)


def test_archived_requirement_set_compiles_to_expected_process_model() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    compiled = compile_archived_requirement_set(fixture)

    assert compiled == fixture["expected_process_model"]


def test_compiled_process_model_includes_required_validation_surfaces() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    compiled = compile_archived_requirement_set(fixture)

    assert compiled["eligibility_rules"]
    assert compiled["required_user_facts"]
    assert compiled["required_documents"]
    assert compiled["file_rules"]
    assert compiled["fees"]
    assert compiled["stages"]
    assert compiled["unsupported_paths"]
    assert compiled["guardrail_bundle_refs"]

    assert all("requirement_id" in item for item in compiled["eligibility_rules"])
    assert all("requirement_id" in item for item in compiled["required_user_facts"])
    assert all("requirement_id" in item for item in compiled["required_documents"])
    assert all("requirement_id" in item for item in compiled["file_rules"])
    assert all("requirement_id" in item for item in compiled["fees"])
    assert all("requirement_id" in item for item in compiled["stages"])
    assert all("requirement_id" in item for item in compiled["unsupported_paths"])
