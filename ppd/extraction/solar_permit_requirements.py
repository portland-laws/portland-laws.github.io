"""Syntax-first sentinel for solar permit requirement extraction.

This module intentionally stays small while the daemon restores broader solar
requirement validation. The dedicated syntax-first test imports only this module
so malformed Python is caught before wider fixture or extractor tests run.
"""

from __future__ import annotations

MODULE_PURPOSE = "syntax_first_solar_permit_requirements_import"
MODULE_STATUS = "syntax_first_import_ready"


def validator_status() -> str:
    """Return the current syntax-first import sentinel status."""
    return MODULE_STATUS
