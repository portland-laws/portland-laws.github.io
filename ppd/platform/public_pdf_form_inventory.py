"""Deterministic PP&D contract for public_pdf_form_inventory.

This module is source-backed evidence for a reopened comprehensive PP&D goal
task. It is intentionally side-effect-free and does not perform live DevHub,
official action, upload, payment, or real PDF filling work.
"""

from __future__ import annotations

import json
from typing import Any


CONTRACT_JSON = '{\n  "capability": "public_pdf_form_inventory",\n  "defaultMode": "fixture_only",\n  "exactConfirmationBeforeOfficialAction": true,\n  "fallbackKind": "public_pdf_form_inventory",\n  "liveCrawlAllowedByDefault": false,\n  "officialDevhubActionAllowedByDefault": false,\n  "privateArtifactPersistence": "forbidden",\n  "requiredOutputs": [\n    "pdf_inventory_record",\n    "form_field_manifest",\n    "raw_document_persistence_refusal"\n  ],\n  "requiresHumanAttendanceBeforeBrowserUse": true,\n  "schemaVersion": 1,\n  "surfaces": [\n    "permit_applications",\n    "single_pdf_guidance",\n    "fillable_public_forms"\n  ]\n}'


def contract() -> dict[str, Any]:
    return json.loads(CONTRACT_JSON)
