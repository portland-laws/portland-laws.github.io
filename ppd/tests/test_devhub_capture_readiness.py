from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub_capture_readiness import load_manifest, validate_manifest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_capture_readiness"


def test_ready_manifest_accepts_attended_accessible_structure_scope() -> None:
    manifest = load_manifest(FIXTURE_DIR / "ready_manifest.json")

    result = validate_manifest(manifest)

    assert result.ok, result.errors


def test_manifest_rejects_session_state_and_transactional_actions() -> None:
    manifest = json.loads((FIXTURE_DIR / "ready_manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"]["cookies"] = true_value()
    manifest["artifacts"]["har_data"] = "capture.har"
    manifest["allowed_actions"].extend(["upload", "submit", "payment", "scheduling"])

    result = validate_manifest(manifest)

    assert not result.ok
    joined = "\n".join(result.errors)
    assert "artifacts.cookies is forbidden" in joined
    assert "artifacts.har_data is forbidden" in joined
    assert "allowed_actions includes forbidden actions" in joined


def test_manifest_requires_exact_boundary_notices() -> None:
    manifest = json.loads((FIXTURE_DIR / "ready_manifest.json").read_text(encoding="utf-8"))
    manifest["boundary_notices"] = list(reversed(manifest["boundary_notices"]))

    result = validate_manifest(manifest)

    assert not result.ok
    assert "boundary_notices must exactly match" in "\n".join(result.errors)


def true_value() -> bool:
    return True
