"""Fixture privacy checks for mocked DevHub workflow data.

The checks are deterministic and local. They do not open DevHub, read browser
state, inspect screenshots, or process live user data.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REDACTED = "[REDACTED]"

SENSITIVE_KEY_PARTS = (
    "password",
    "passcode",
    "secret",
    "token",
    "cookie",
    "credential",
    "auth",
    "session",
    "storage_state",
    "storage-state",
    "storagestate",
    "trace",
    "screenshot",
)

SENSITIVE_VALUE_MARKERS = (
    "password=",
    "cookie:",
    "set-cookie",
    "bearer ",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    ".png",
    ".jpg",
    ".jpeg",
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def validate_devhub_fixture_privacy(value: Any) -> list[str]:
    errors: list[str] = []
    _scan(value, path="$", errors=errors)
    return errors


def validate_devhub_fixture_privacy_file(path: Path) -> list[str]:
    return validate_devhub_fixture_privacy(json.loads(path.read_text(encoding="utf-8")))


def _scan(value: Any, *, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            lowered_key = key_text.lower()
            if any(part in lowered_key for part in SENSITIVE_KEY_PARTS):
                _validate_sensitive_key_value(child_path, nested, errors)
            _scan(nested, path=child_path, errors=errors)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _scan(nested, path=f"{path}[{index}]", errors=errors)
        return
    if isinstance(value, str):
        _validate_string_value(path, value, errors)


def _validate_sensitive_key_value(path: str, value: Any, errors: list[str]) -> None:
    if value in (None, "", REDACTED, [], {}):
        return
    errors.append(f"{path} contains sensitive DevHub/session artifact data")


def _validate_string_value(path: str, value: str, errors: list[str]) -> None:
    if value == REDACTED:
        return
    lowered = value.lower()
    for marker in SENSITIVE_VALUE_MARKERS:
        if marker in lowered:
            errors.append(f"{path} contains sensitive artifact marker {marker!r}")
            break
    if EMAIL_RE.search(value):
        errors.append(f"{path} contains unredacted email address")
    if PHONE_RE.search(value):
        errors.append(f"{path} contains unredacted US phone number")
    if SSN_RE.search(value):
        errors.append(f"{path} contains unredacted SSN-like value")
