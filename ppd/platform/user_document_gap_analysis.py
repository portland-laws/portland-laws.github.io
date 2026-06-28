"""Deterministic PP&D contract for user_document_gap_analysis.

This module is source-backed evidence for a reopened comprehensive PP&D goal
task. It is intentionally side-effect-free and does not perform live DevHub,
official action, upload, payment, or real PDF filling work.
"""

from __future__ import annotations

import json
from typing import Any


CONTRACT_JSON = '{\n  "capability": "user_document_gap_analysis",\n  "defaultMode": "fixture_only",\n  "exactConfirmationBeforeOfficialAction": true,\n  "fallbackKind": "user_document_gap_analysis",\n  "liveCrawlAllowedByDefault": false,\n  "officialDevhubActionAllowedByDefault": false,\n  "privateArtifactPersistence": "forbidden",\n  "requiredOutputs": [\n    "missing_fact_list",\n    "stale_evidence_flag",\n    "exact_confirmation_blocker"\n  ],\n  "requiresHumanAttendanceBeforeBrowserUse": true,\n  "schemaVersion": 1,\n  "surfaces": [\n    "known_user_facts",\n    "source_requirements",\n    "document_placeholders"\n  ]\n}'


def contract() -> dict[str, Any]:
    return json.loads(CONTRACT_JSON)
