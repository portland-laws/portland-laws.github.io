"""Fixture test for repeated syntax-failure prompt narrowing.

This test is intentionally fixture-only. It proves the daemon recovery contract
for SyntaxError, py_compile, TS1005, TS1109, and TS1128 failures without touching
live crawl state, DevHub sessions, or broad PP&D domain contracts.
"""

from __future__ import annotations

import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon"
    / "repeated_syntax_failure_one_file_repair.json"
)
SYNTAX_TOKENS = ("SyntaxError", "py_compile", "TS1005", "TS1109", "TS1128")


def _load_fixture() -> dict[str, object]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise AssertionError("fixture root must be an object")
    return loaded


def _as_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError(f"{label} must be an object")
    return value


def _as_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise AssertionError(f"{label} must be a list")
    return value


def validate_repeated_syntax_failure_one_file_repair_fixture() -> None:
    fixture = _load_fixture()
    failures = _as_list(fixture.get("recent_failures"), "recent_failures")
    prompt = _as_dict(fixture.get("expected_next_prompt"), "expected_next_prompt")

    diagnostics = "\n".join(str(_as_dict(item, "failure").get("diagnostic", "")) for item in failures)
    missing_tokens = [token for token in SYNTAX_TOKENS if token not in diagnostics]
    if missing_tokens:
        raise AssertionError(f"fixture is missing syntax diagnostics: {missing_tokens}")

    if prompt.get("mode") != "one_file_syntax_repair":
        raise AssertionError("next prompt mode must be one_file_syntax_repair")
    if prompt.get("max_files") != 1:
        raise AssertionError("syntax-recovery prompt must allow exactly one file")

    required_fragments = [str(item) for item in _as_list(prompt.get("required_instruction_fragments"), "required_instruction_fragments")]
    forbidden_fragments = [str(item) for item in _as_list(prompt.get("forbidden_instruction_fragments"), "forbidden_instruction_fragments")]
    required_text = "\n".join(required_fragments).lower()
    forbidden_text = "\n".join(forbidden_fragments).lower()

    for expected in ("replace exactly one file", "repair the syntax failure first"):
        if expected not in required_text:
            raise AssertionError(f"missing required prompt fragment: {expected}")
    for forbidden in ("rewrite ppd/contracts/documents.py", "add crawler code"):
        if forbidden not in forbidden_text:
            raise AssertionError(f"missing forbidden prompt fragment: {forbidden}")

    for item in failures:
        failure = _as_dict(item, "failure")
        changed_files = [str(path) for path in _as_list(failure.get("changed_files"), "changed_files")]
        if not changed_files:
            raise AssertionError("each failure must name changed files for prompt repair targeting")
        for path in changed_files:
            if not path.startswith("ppd/"):
                raise AssertionError(f"changed file must stay under ppd/: {path}")


if __name__ == "__main__":
    validate_repeated_syntax_failure_one_file_repair_fixture()
