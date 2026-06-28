"""Agent-facing missing-information fixture API for PP&D cases.

The API intentionally exposes only facts that require user follow-up. Private values
must already be redacted in the committed fixture, and validation rejects local file
paths before data is returned.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_STATUSES = {"missing", "stale", "ambiguous", "conflicting"}
_LOCAL_PATH_PATTERNS = (
    re.compile(r"(?:^|\s)/(?:home|Users|tmp|var|private|mnt|Volumes)/"),
    re.compile(r"[A-Za-z]:\\\\"),
    re.compile(r"file://"),
)
_DEFAULT_FIXTURE = (
    Path(__file__).parent
    / "tests"
    / "fixtures"
    / "missing_information"
    / "synthetic_residential_addition_case.json"
)


class MissingInformationFixtureError(ValueError):
    """Raised when the committed missing-information fixture is unsafe or invalid."""


@dataclass(frozen=True)
class MissingInformationRequest:
    """Lookup request for a deterministic synthetic case fixture."""

    case_id: str = "synthetic_residential_addition_case"


def load_missing_information_fixture(
    request: MissingInformationRequest | None = None,
    *,
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return missing-information facts for the requested synthetic case.

    The returned object is safe for agent prompts: it contains only follow-up facts,
    private values are redacted, and local file paths are rejected.
    """

    active_request = request or MissingInformationRequest()
    path = fixture_path or _DEFAULT_FIXTURE
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("case_id") != active_request.case_id:
        raise MissingInformationFixtureError(
            f"fixture case_id {payload.get('case_id')!r} does not match request {active_request.case_id!r}"
        )

    _validate_missing_information_payload(payload)
    return payload


def _validate_missing_information_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload.get("facts"), list) or not payload["facts"]:
        raise MissingInformationFixtureError("fixture must include at least one follow-up fact")

    for fact in payload["facts"]:
        if fact.get("status") not in _ALLOWED_STATUSES:
            raise MissingInformationFixtureError(
                f"fact {fact.get('fact_id')!r} has unsupported status {fact.get('status')!r}"
            )
        if fact.get("current_value") not in (None, "[REDACTED]"):
            raise MissingInformationFixtureError(
                f"fact {fact.get('fact_id')!r} exposes an unredacted current_value"
            )
        if "local_path" in fact or "file_path" in fact:
            raise MissingInformationFixtureError(
                f"fact {fact.get('fact_id')!r} exposes a local path field"
            )

    serialized = json.dumps(payload, sort_keys=True)
    for pattern in _LOCAL_PATH_PATTERNS:
        if pattern.search(serialized):
            raise MissingInformationFixtureError("fixture exposes a local file path")


__all__ = [
    "MissingInformationFixtureError",
    "MissingInformationRequest",
    "load_missing_information_fixture",
]
