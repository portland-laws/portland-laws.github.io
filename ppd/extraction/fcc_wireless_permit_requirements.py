"""Syntax-first placeholder for FCC wireless permit requirement extraction.

The broader FCC wireless requirement extractor should be added only after this
module can be imported in isolation. Keeping this file intentionally small gives
PP&D validation a stable sentinel for Python syntax regressions.
"""

from __future__ import annotations

MODULE_STATUS = "syntax_first_import_ready"
MODULE_PURPOSE = "fcc_wireless_permit_requirements"


def validator_status() -> str:
    """Return the syntax-first readiness status for import-only tests."""
    return MODULE_STATUS
