"""Prompt preflight for solar extractor implementation requests.

The PP&D daemon should fail closed before asking the model to implement the
solar extractor unless the daemon prompt explicitly carries the constraints that
kept prior repair attempts narrow and syntax-valid.
"""

from __future__ import annotations

import re
from typing import Any


MODULE_STATUS = "solar_extractor_prompt_preflight_ready"

REQUIRED_SOLAR_EXTRACTOR_CONSTRAINTS = {
    "one_file": ("one-file", "one file"),
    "no_dataclass": ("no-dataclass", "no dataclass", "no dataclasses"),
    "syntax_sentinel_preserving": (
        "syntax-sentinel-preserving",
        "syntax sentinel preserving",
        "preserve the syntax sentinel",
        "preserves the syntax sentinel",
    ),
    "seven_record_expected_output": (
        "seven-record expected-output",
        "seven record expected output",
        "seven-record expected output",
        "seven record expected-output",
    ),
}


def check_solar_extractor_prompt_preflight(prompt: str) -> dict[str, Any]:
    """Return a deterministic allow/refuse decision for a daemon prompt."""

    normalized = _normalize_prompt(prompt)
    if not _is_solar_extractor_implementation_prompt(normalized):
        return {
            "ok": True,
            "reason": "not_solar_extractor_implementation_prompt",
            "missing_constraints": [],
        }

    missing = [
        constraint
        for constraint, variants in REQUIRED_SOLAR_EXTRACTOR_CONSTRAINTS.items()
        if not any(variant in normalized for variant in variants)
    ]
    if missing:
        return {
            "ok": False,
            "reason": "solar_extractor_prompt_constraints_missing",
            "missing_constraints": missing,
        }

    return {
        "ok": True,
        "reason": "solar_extractor_prompt_constraints_present",
        "missing_constraints": [],
    }


def require_solar_extractor_prompt_preflight(prompt: str) -> None:
    """Raise ValueError when a solar extractor implementation prompt is unsafe."""

    result = check_solar_extractor_prompt_preflight(prompt)
    if result["ok"]:
        return
    missing = ", ".join(result["missing_constraints"])
    raise ValueError(f"solar extractor implementation prompt missing constraints: {missing}")


def _normalize_prompt(prompt: str) -> str:
    lowered = prompt.lower().replace("_", "-")
    return re.sub(r"\s+", " ", lowered).strip()


def _is_solar_extractor_implementation_prompt(normalized_prompt: str) -> bool:
    names_solar_extractor = "solar extractor" in normalized_prompt or "solar-extractor" in normalized_prompt
    asks_for_implementation = any(
        marker in normalized_prompt
        for marker in (
            "implement",
            "implementation",
            "add the solar extractor",
            "replace ppd/contracts/solar",
            "extractor implementation",
        )
    )
    return names_solar_extractor and asks_for_implementation
