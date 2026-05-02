"""Syntax-first sentinel for Urban Forestry permit requirement extraction.

This module is intentionally small while the Urban Forestry requirement
extractor is being built out. The dedicated syntax-first test imports only this
module so malformed Python is caught before broader fixture validation runs.
"""

MODULE_STATUS = "syntax_first_import_ready"
MODULE_PURPOSE = "urban_forestry_permit_requirements"


def module_status():
    """Return the import sentinel status for narrow syntax-first tests."""
    return MODULE_STATUS
