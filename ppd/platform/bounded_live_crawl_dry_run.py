"""Deterministic PP&D contract for bounded_live_crawl_dry_run.

This module is source-backed evidence for a reopened comprehensive PP&D goal
task. It is intentionally side-effect-free and does not perform live DevHub,
official action, upload, payment, or real PDF filling work.
"""

from __future__ import annotations

import json
from typing import Any


CONTRACT_JSON = '{\n  "capability": "bounded_live_crawl_dry_run",\n  "defaultMode": "fixture_only",\n  "exactConfirmationBeforeOfficialAction": true,\n  "fallbackKind": "bounded_live_crawl_dry_run",\n  "liveCrawlAllowedByDefault": false,\n  "officialDevhubActionAllowedByDefault": false,\n  "privateArtifactPersistence": "forbidden",\n  "requiredOutputs": [\n    "metadata_manifest",\n    "validation_summary",\n    "raw_body_persistence_refusal"\n  ],\n  "requiresHumanAttendanceBeforeBrowserUse": true,\n  "schemaVersion": 1,\n  "surfaces": [\n    "small_public_seed_set",\n    "allowlist",\n    "processor_preflight"\n  ]\n}'


def contract() -> dict[str, Any]:
    return json.loads(CONTRACT_JSON)
