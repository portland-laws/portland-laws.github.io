"""Syntax-first sentinel for sign permit requirement extraction.

This module intentionally stays minimal until the sign permit extraction
fixtures and validators are added. The syntax-first test imports only this file
so malformed Python is caught before broader sign requirement validation runs.
"""

from __future__ import annotations

MODULE_PURPOSE = "syntax_first_import_sentinel"
MODULE_STATUS = "syntax_first_import_ready"
TARGET_PERMIT_TYPE = "sign_permit"


def validator_status() -> str:
    """Return the import sentinel status without running extraction behavior."""
    return MODULE_STATUS
