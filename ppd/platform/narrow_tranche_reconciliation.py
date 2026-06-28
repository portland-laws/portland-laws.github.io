"""Deterministic PP&D contract for narrow_tranche_reconciliation.

This module is source-backed evidence for a reopened comprehensive PP&D goal
task. It is intentionally side-effect-free and does not perform live DevHub,
official action, upload, payment, or real PDF filling work.
"""

from __future__ import annotations

import json
from typing import Any


CONTRACT_JSON = '{\n  "capability": "narrow_tranche_reconciliation",\n  "defaultMode": "fixture_only",\n  "exactConfirmationBeforeOfficialAction": true,\n  "fallbackKind": "narrow_tranche_reconciliation",\n  "liveCrawlAllowedByDefault": false,\n  "officialDevhubActionAllowedByDefault": false,\n  "privateArtifactPersistence": "forbidden",\n  "requiredOutputs": [\n    "source_anchor_validation",\n    "public_crawl_preflight_policy",\n    "pdf_form_extraction_contract",\n    "requirement_and_guardrail_normalization",\n    "devhub_surface_map_contract"\n  ],\n  "requiresHumanAttendanceBeforeBrowserUse": true,\n  "schemaVersion": 1,\n  "surfaces": [\n    "validated_fixture_tests",\n    "source_backed_contracts",\n    "supervisor_repaired_task_board"\n  ]\n}'


def contract() -> dict[str, Any]:
    return json.loads(CONTRACT_JSON)
