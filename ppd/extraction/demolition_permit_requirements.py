"""Syntax-first sentinel for demolition permit requirement extraction.

The behavioral demolition requirement extractor is intentionally deferred to a
later fixture-backed task. This module exists so narrow import validation can
catch malformed Python in this target before broader demolition requirement
validation runs.
"""

from __future__ import annotations

MODULE_STATUS = "syntax_first_import_ready"
MODULE_PURPOSE = "demolition_permit_requirements_syntax_sentinel"


def module_status() -> str:
    """Return the current narrow implementation status."""
    return MODULE_STATUS
