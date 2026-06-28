"""Deterministic PP&D contract for ppd_surface_registry.

This module is source-backed evidence for a reopened comprehensive PP&D goal
task. It is intentionally side-effect-free and does not perform live DevHub,
official action, upload, payment, or real PDF filling work.
"""

from __future__ import annotations

import json
from typing import Any


CONTRACT_JSON = '{\n  "capability": "ppd_surface_registry",\n  "defaultMode": "fixture_only",\n  "exactConfirmationBeforeOfficialAction": true,\n  "fallbackKind": "surface_registry_taxonomy",\n  "liveCrawlAllowedByDefault": false,\n  "officialDevhubActionAllowedByDefault": false,\n  "privateArtifactPersistence": "forbidden",\n  "requiredOutputs": [\n    "surface_taxonomy",\n    "action_boundary_map",\n    "agent_guardrail_api_index"\n  ],\n  "requiresHumanAttendanceBeforeBrowserUse": true,\n  "schemaVersion": 1,\n  "surfaces": [\n    "public_portland_pages",\n    "devhub_public_entrypoints",\n    "authenticated_read_only",\n    "reversible_drafts"\n  ]\n}'


def contract() -> dict[str, Any]:
    return json.loads(CONTRACT_JSON)
