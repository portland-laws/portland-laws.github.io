"""Syntax-first import sentinel for PP&D public source inventory validation.

This module intentionally exposes only the stable import guard used by the
syntax-first repair tests. Public source inventory validator behavior should be
added in a later, separate task after this sentinel passes validation.
"""

from __future__ import annotations


MODULE_PURPOSE = "syntax_first_public_source_inventory_validation"


def validator_status():
    """Return the stable syntax-first status record expected by import guards."""
    return {
        "module": "ppd.contracts.public_source_inventory",
        "syntax_first_probe": True,
        "validator_ready": False,
    }


__all__ = ["MODULE_PURPOSE", "validator_status"]
