"""Fixture-first public refresh preflight checklist assembly.

This module intentionally consumes only synthetic review-packet rows and official
source-anchor placeholders. It does not crawl, download, authenticate, open
DevHub, activate releases, or persist raw source output.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


CHECKLIST_VERSION = "public-refresh-preflight-v1"
ALLOWED_METHODS = {"GET", "HEAD"}
ALLOWED_DECISIONS = {"allow", "skip"}
PROHIBITED_ROW_KEYS = {
    "crawl_output",
    "downloaded_document",
    "raw_output",
    "raw_html",
    "devhub_session",
    "auth_state",
    "trace",
    "release_activation",
    "official_action",
}


class PreflightError(ValueError):
    """Raised when a synthetic preflight fixture is incomplete or unsafe."""


def load_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise PreflightError("preflight packet must be a JSON object")
    return packet


def assemble_preflight(packet: Mapping[str, Any]) -> dict[str, Any]:
    packet_id = _required_text(packet, "packet_id")
    packet_version = _required_text(packet, "packet_version")
    rows = packet.get("rows")
    if not isinstance(rows, list) or not rows:
        raise PreflightError("packet rows must be a non-empty list")

    seeds = [_assemble_seed(row, index) for index, row in enumerate(rows)]
    return {
        "checklist_version": CHECKLIST_VERSION,
        "packet_id": packet_id,
        "packet_version": packet_version,
        "offline_only": True,
        "input_policy": {
            "allowed_inputs": [
                "synthetic next public refresh seed review packet rows",
                "official source-anchor placeholders",
            ],
            "prohibited_actions": [
                "live crawling",
                "document downloads",
                "raw output storage",
                "DevHub opening",
                "release activation",
                "official submissions or other official actions",
            ],
        },
        "seeds": seeds,
        "validation_commands": [
            ["python3", "-m", "py_compile", "ppd/public_refresh_preflight.py"],
            ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_preflight.py"],
            ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
        ],
    }


def _assemble_seed(row: Any, index: int) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise PreflightError(f"row {index} must be an object")
    unsafe_keys = sorted(PROHIBITED_ROW_KEYS.intersection(row))
    if unsafe_keys:
        raise PreflightError(f"row {index} contains prohibited keys: {', '.join(unsafe_keys)}")

    methods = row.get("request_methods")
    if not isinstance(methods, list) or not methods:
        raise PreflightError(f"row {index} request_methods must be a non-empty list")
    normalized_methods = []
    for method in methods:
        if not isinstance(method, str):
            raise PreflightError(f"row {index} request method must be text")
        upper_method = method.upper()
        if upper_method not in ALLOWED_METHODS:
            raise PreflightError(f"row {index} request method is not allowed: {method}")
        normalized_methods.append(upper_method)

    decision = _required_text(row, "allowlist_decision")
    if decision not in ALLOWED_DECISIONS:
        raise PreflightError(f"row {index} allowlist_decision must be allow or skip")

    archive_manifest = row.get("archive_manifest_expectation")
    if not isinstance(archive_manifest, dict):
        raise PreflightError(f"row {index} archive_manifest_expectation must be an object")
    if archive_manifest.get("metadata_only") is not True:
        raise PreflightError(f"row {index} archive manifest must be metadata-only")
    if archive_manifest.get("raw_document_storage") is not False:
        raise PreflightError(f"row {index} archive manifest must reject raw document storage")

    anchors = row.get("source_anchor_placeholders")
    if not isinstance(anchors, list) or not anchors:
        raise PreflightError(f"row {index} source_anchor_placeholders must be a non-empty list")
    normalized_anchors = [_assemble_anchor(anchor, index) for anchor in anchors]

    return {
        "seed_id": _required_text(row, "seed_id"),
        "seed_url": _required_text(row, "seed_url"),
        "robots_check": {
            "user_agent": _required_text(row, "robots_user_agent"),
            "expected_status": _required_text(row, "robots_expected"),
            "offline_note": "Expectation is reviewed from fixture text only; no robots.txt fetch is permitted.",
        },
        "allowlist_decision": decision,
        "canonical_url_expectation": _required_text(row, "canonical_url_expectation"),
        "request_method_limits": normalized_methods,
        "rate_limit_note": _required_text(row, "rate_limit_note"),
        "archive_manifest_expectation": {
            "metadata_only": True,
            "raw_document_storage": False,
            "expected_fields": _required_text_list(archive_manifest, "expected_fields"),
        },
        "skip_reason_expectation": _required_text(row, "skip_reason_expectation"),
        "reviewer_routing": _required_text(row, "reviewer_routing"),
        "rollback_note": _required_text(row, "rollback_note"),
        "source_anchor_placeholders": normalized_anchors,
    }


def _assemble_anchor(anchor: Any, row_index: int) -> dict[str, str]:
    if not isinstance(anchor, dict):
        raise PreflightError(f"row {row_index} source anchor must be an object")
    kind = _required_text(anchor, "kind")
    if kind != "official_source_anchor_placeholder":
        raise PreflightError(f"row {row_index} source anchor kind must be official_source_anchor_placeholder")
    return {
        "kind": kind,
        "title": _required_text(anchor, "title"),
        "url_placeholder": _required_text(anchor, "url_placeholder"),
        "expected_use": _required_text(anchor, "expected_use"),
    }


def _required_text(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PreflightError(f"{key} must be non-empty text")
    return value


def _required_text_list(data: Mapping[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise PreflightError(f"{key} must be a non-empty list")
    output = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise PreflightError(f"{key} entries must be non-empty text")
        output.append(item)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a fixture-first public refresh preflight checklist.")
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    checklist = assemble_preflight(load_packet(args.packet))
    print(json.dumps(checklist, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
