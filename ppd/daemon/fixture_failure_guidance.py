"""Failure-context guidance for JSON fixture shape mismatches.

This module is intentionally daemon-local. It does not validate PP&D domain
semantics; it only recognizes validator failures that are likely caused by a
validator expecting fields absent from a committed JSON fixture and emits a
compact retry instruction for the next worker.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional

try:  # pragma: no cover - script fallback for direct daemon diagnostics
    from .fixture_shape import JsonFixtureShape, describe_json_fixture
except ImportError:  # pragma: no cover
    from fixture_shape import JsonFixtureShape, describe_json_fixture


_JSON_FIXTURE_PATTERN = re.compile(r"ppd/tests/fixtures/[A-Za-z0-9_./-]+\.json")
_MISSING_FIELD_PATTERNS = (
    "missing required field",
    "missing required fields",
    "required field",
    "required fields",
    "absent field",
    "absent fields",
    "missing seed url",
    "missing seed urls",
    "missing preflight",
    "missing allowlist",
    "missing robots",
    "missing timeout",
    "missing no-persist",
    "missing processor-adapter",
    "missing processor adapter",
)


@dataclass(frozen=True)
class FixtureFailureGuidance:
    """Prompt guidance for a fixture-shape retry."""

    fixture_path: Optional[str]
    fixture_shape: Optional[str]
    guidance: str


def build_fixture_failure_guidance(
    failure_text: str,
    *,
    repo_root: PurePosixPath | Path | str = PurePosixPath("."),
) -> Optional[FixtureFailureGuidance]:
    """Return retry guidance when a validator failure mentions absent JSON fields."""

    if not failure_text or not _mentions_missing_fixture_fields(failure_text):
        return None

    fixture_path = _first_json_fixture_path(failure_text)
    fixture_shape = None
    if fixture_path is not None:
        try:
            shape = describe_json_fixture(Path(repo_root), fixture_path)
            fixture_shape = _format_fixture_shape(shape)
        except Exception as exc:  # pragma: no cover - defensive daemon guidance path
            fixture_shape = f"fixture shape diagnostic unavailable for {fixture_path}: {exc}"

    guidance_lines = [
        "Fixture-shape retry guidance:",
        "Inspect the committed JSON fixture shape before writing or changing a validator.",
        "Use the daemon fixture-shape diagnostic to compare expected fields with the fields actually present in the committed fixture.",
        "Constrain the retry to the existing fixture structure unless the selected task explicitly permits fixture replacement.",
        "Do not add broad shared contracts, live crawl code, authenticated automation, or new processor-adapter implementations for this retry.",
    ]
    if fixture_path is not None:
        guidance_lines.append(f"Committed fixture to inspect: {fixture_path}")
    if fixture_shape:
        guidance_lines.append("Committed fixture shape:")
        guidance_lines.append(fixture_shape)

    return FixtureFailureGuidance(
        fixture_path=fixture_path,
        fixture_shape=fixture_shape,
        guidance="\n".join(guidance_lines),
    )


def append_fixture_failure_guidance(
    prompt_parts: Iterable[str],
    failure_text: str,
    *,
    repo_root: PurePosixPath | Path | str = PurePosixPath("."),
) -> list[str]:
    """Append fixture-shape guidance to prompt parts when the failure warrants it."""

    parts = list(prompt_parts)
    guidance = build_fixture_failure_guidance(failure_text, repo_root=repo_root)
    if guidance is not None:
        parts.append(guidance.guidance)
    return parts


def _mentions_missing_fixture_fields(text: str) -> bool:
    normalized = text.lower()
    if ".json" not in normalized and "fixture" not in normalized:
        return False
    return any(pattern in normalized for pattern in _MISSING_FIELD_PATTERNS)


def _first_json_fixture_path(text: str) -> Optional[str]:
    match = _JSON_FIXTURE_PATTERN.search(text)
    if match is None:
        return None
    return match.group(0)


def _format_fixture_shape(shape: JsonFixtureShape) -> str:
    data = shape.to_dict()
    lines = [
        f"fixture_path: {data['fixture_path']}",
        f"top_level_type: {data['top_level_type']}",
        f"top_level_keys: {', '.join(data['top_level_keys']) if data['top_level_keys'] else '(none)'}",
        f"list_fields: {', '.join(data['list_fields']) if data['list_fields'] else '(none)'}",
    ]
    first_object_keys = data["first_object_keys"]
    if first_object_keys:
        for field, keys in sorted(first_object_keys.items()):
            label = field if field else ""
            lines.append(f"first_object_keys[{label}]: {', '.join(keys) if keys else '(none)'}")
    else:
        lines.append("first_object_keys: (none)")
    return "\n".join(lines)


def self_test() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        fixture_path = "ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json"
        fixture = repo_root / fixture_path
        fixture.parent.mkdir(parents=True)
        fixture.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "plannedSeeds": [
                        {
                            "id": "seed-ppd-landing",
                            "url": "https://www.portland.gov/ppd",
                            "preflight": {"robots": "respect", "timeoutSeconds": 20},
                        }
                    ],
                    "skippedUrls": [{"url": "mailto:test@example.invalid", "reasonCode": "unsupported-scheme"}],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        failure_text = (
            "AssertionError: missing required field; expected one of: seedUrls, seeds\n"
            f"fixture path: {fixture_path}\n"
            "missing preflight policy fields"
        )
        guidance = build_fixture_failure_guidance(failure_text, repo_root=repo_root)
        if guidance is None:
            errors.append("missing-field fixture failure did not produce guidance")
        else:
            required_fragments = (
                "Inspect the committed JSON fixture shape",
                "Do not add broad shared contracts",
                fixture_path,
                "top_level_keys: plannedSeeds, schemaVersion, skippedUrls",
                "list_fields: plannedSeeds, skippedUrls",
                "first_object_keys[plannedSeeds]: id, preflight, url",
            )
            for fragment in required_fragments:
                if fragment not in guidance.guidance:
                    errors.append(f"guidance missing fragment: {fragment}")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), flush=True)
        return 1
    print(json.dumps({"ok": True}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
