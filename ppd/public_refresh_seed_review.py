"""Fixture-first public refresh seed review packet builder and validator.

This module is intentionally offline-only. It consumes synthetic post-activation
monitoring rows and official source-anchor placeholders, then emits a review
packet for humans to decide what the next public refresh seed should include.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BLOCKED_ACTIONS = (
    "live_crawling",
    "document_downloads",
    "raw_output_storage",
    "devhub_open",
    "release_activation",
    "official_actions",
)

VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/public_refresh_seed_review.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_seed_review.py"],
]

_REQUIRED_CANDIDATE_FIELDS = (
    "seed_id",
    "title",
    "official_source_anchor",
    "monitoring_plan_reference",
    "rank",
    "rank_score",
    "rank_inputs",
    "robots_allowlist_preflight_needs",
    "expected_metadata_only_archive_manifest_impact",
    "citation_span_refresh_need",
    "stale_source_guardrail_hold_impact",
    "human_review_routing",
    "rollback_notes",
)

_REQUIRED_REVIEW_ROUTING_FIELDS = ("queue", "anchor_owner", "review_note")

_FORBIDDEN_STRING_MARKERS = (
    "auth_state",
    "session_state",
    "credential",
    "cookie",
    "screenshot",
    "trace.zip",
    "har file",
    "file://",
    "/home/",
    "raw crawl output",
    "raw_body",
    "downloaded document",
    "downloaded artifact",
    "private artifact",
    "private case file",
    "live crawl completed",
    "live crawler ran",
    "opened devhub",
    "devhub session",
    "release activated",
    "activation completed",
    "official action completed",
    "submitted permit",
    "paid fees",
    "scheduled inspection",
    "certified application",
    "guarantee permit",
    "permit guaranteed",
    "legal guarantee",
    "permitting guarantee",
    "active mutation enabled",
)

_ACTIVE_MUTATION_KEYS = (
    "active_mutation",
    "active_mutation_enabled",
    "mutates_sources",
    "mutates_guardrails",
    "mutates_release_state",
    "release_activation_enabled",
    "official_action_enabled",
    "live_crawl_enabled",
    "devhub_enabled",
)


class PublicRefreshSeedReviewValidationError(ValueError):
    """Raised when a public refresh seed review packet is incomplete or unsafe."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("next public refresh seed review packet v1 rejected: " + "; ".join(errors))


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_non_empty(value: Any, path: str, errors: list[str]) -> None:
    if value is None or value == "" or value == [] or value == {}:
        errors.append(f"missing {path}")


def _anchor_map(anchor_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    anchors: dict[str, dict[str, Any]] = {}
    for row in anchor_rows:
        anchor_id = str(row["anchor_id"])
        placeholder = str(row["official_placeholder"])
        if not placeholder.startswith("official://"):
            raise ValueError(f"source anchor {anchor_id} is not an official placeholder")
        if row.get("devhub_open_required") or row.get("auth_required") or row.get("document_download_required"):
            raise ValueError(f"source anchor {anchor_id} requires a prohibited action")
        anchors[anchor_id] = row
    return anchors


def _score(row: dict[str, Any]) -> int:
    stale_score = min(int(row.get("observed_days_stale", 0)), 60) * 3
    citation_score = int(row.get("citation_spans_due", 0)) * 12
    interest_score = int(row.get("public_interest_score", 0)) * 5
    failure_score = int(row.get("failures_7d", 0)) * 4
    guardrail_penalty = 35 if row.get("stale_source_guardrail") == "hold" else 0
    release_penalty = 20 if row.get("release_gate_state") != "metadata_only_ready" else 0
    return stale_score + citation_score + interest_score + failure_score - guardrail_penalty - release_penalty


def _robots_preflight(row: dict[str, Any]) -> list[str]:
    needs: list[str] = []
    if row.get("robots_profile") != "known_allow_placeholder":
        needs.append("confirm robots placeholder remains allowlisted before any future crawl")
    if row.get("allowlist_status") != "approved_placeholder":
        needs.append("route allowlist placeholder for human confirmation")
    return needs or ["no robots or allowlist preflight needed for metadata-only packet"]


def _human_review(row: dict[str, Any], anchor: dict[str, Any]) -> dict[str, str]:
    if row.get("stale_source_guardrail") == "hold":
        queue = "stale-source guardrail review"
    elif row.get("citation_spans_due", 0) > 0:
        queue = "citation span refresh review"
    elif row.get("allowlist_status") != "approved_placeholder":
        queue = "robots and allowlist preflight review"
    else:
        queue = "metadata-only refresh review"
    return {
        "queue": queue,
        "anchor_owner": str(anchor.get("agency", "official source owner placeholder")),
        "review_note": "human review only; do not open DevHub, crawl, download, submit, activate, or certify",
    }


def _scan_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            lowered_key = str(key).lower()
            if lowered_key in _ACTIVE_MUTATION_KEYS and child is True:
                errors.append(f"active mutation flag must be false or absent: {child_path}")
            _scan_forbidden(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in _FORBIDDEN_STRING_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden private, live, official, guarantee, or mutation claim at {path}")
                break


def validate_packet(packet: dict[str, Any]) -> list[str]:
    """Return deterministic validation errors for packet v1."""

    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be an object"]

    if packet.get("packet_version") != "next-public-refresh-seed-review-v1":
        errors.append("packet_version must be next-public-refresh-seed-review-v1")
    if packet.get("mode") != "fixture-first-offline-review":
        errors.append("mode must be fixture-first-offline-review")
    if packet.get("prohibited_actions") != list(BLOCKED_ACTIONS):
        errors.append("prohibited_actions must enumerate all blocked public refresh actions")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        errors.append("validation_commands must be exact offline commands")

    monitoring_refs = packet.get("monitoring_plan_references")
    if not isinstance(monitoring_refs, list) or not monitoring_refs:
        errors.append("missing monitoring_plan_references")

    source_anchor_placeholders = packet.get("official_source_anchor_placeholders")
    if not isinstance(source_anchor_placeholders, list) or not source_anchor_placeholders:
        errors.append("missing official_source_anchor_placeholders")
    elif not all(isinstance(item, str) and item.startswith("official://") for item in source_anchor_placeholders):
        errors.append("official_source_anchor_placeholders must contain only official:// placeholders")

    candidates = packet.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append("missing ranked seed candidates")
    else:
        expected_ranks = list(range(1, len(candidates) + 1))
        actual_ranks = [candidate.get("rank") for candidate in candidates if isinstance(candidate, dict)]
        if actual_ranks != expected_ranks:
            errors.append("ranked seed candidates must have contiguous rank values")
        for index, candidate in enumerate(candidates):
            path = f"candidates[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{path} must be an object")
                continue
            for field in _REQUIRED_CANDIDATE_FIELDS:
                _require_non_empty(candidate.get(field), f"{path}.{field}", errors)
            anchor = candidate.get("official_source_anchor")
            if not isinstance(anchor, str) or not anchor.startswith("official://"):
                errors.append(f"{path}.official_source_anchor must be an official:// placeholder")
            if "public_url_placeholder" in candidate:
                errors.append(f"{path} must not include public_url_placeholder")
            routing = candidate.get("human_review_routing")
            if isinstance(routing, dict):
                for field in _REQUIRED_REVIEW_ROUTING_FIELDS:
                    _require_non_empty(routing.get(field), f"{path}.human_review_routing.{field}", errors)
            else:
                errors.append(f"missing {path}.human_review_routing")

    _scan_forbidden(packet, "packet", errors)
    return errors


def assert_valid_packet(packet: dict[str, Any]) -> None:
    errors = validate_packet(packet)
    if errors:
        raise PublicRefreshSeedReviewValidationError(errors)


def build_packet(monitoring_rows: list[dict[str, Any]], source_anchor_rows: list[dict[str, Any]]) -> dict[str, Any]:
    anchors = _anchor_map(source_anchor_rows)
    candidates: list[dict[str, Any]] = []
    monitoring_refs: set[str] = set()
    official_placeholders: set[str] = set()
    for row in monitoring_rows:
        monitoring_ref = str(row.get("monitoring_plan_reference", ""))
        if not monitoring_ref:
            raise ValueError(f"missing monitoring plan reference for seed {row.get('seed_id')}")
        anchor_id = str(row["official_source_anchor_id"])
        if anchor_id not in anchors:
            raise ValueError(f"missing official source anchor placeholder: {anchor_id}")
        anchor = anchors[anchor_id]
        monitoring_refs.add(monitoring_ref)
        official_placeholders.add(str(anchor["official_placeholder"]))
        candidate = {
            "seed_id": row["seed_id"],
            "title": row["title"],
            "official_source_anchor": anchor["official_placeholder"],
            "monitoring_plan_reference": monitoring_ref,
            "rank_score": _score(row),
            "rank_inputs": {
                "observed_days_stale": row.get("observed_days_stale", 0),
                "citation_spans_due": row.get("citation_spans_due", 0),
                "public_interest_score": row.get("public_interest_score", 0),
                "failures_7d": row.get("failures_7d", 0),
                "release_gate_state": row.get("release_gate_state"),
            },
            "robots_allowlist_preflight_needs": _robots_preflight(row),
            "expected_metadata_only_archive_manifest_impact": row.get("metadata_only_archive_delta", "no manifest delta expected"),
            "citation_span_refresh_need": "refresh required" if row.get("citation_spans_due", 0) else "no citation span refresh required",
            "stale_source_guardrail_hold_impact": "hold blocks public refresh seed until reviewed" if row.get("stale_source_guardrail") == "hold" else "no stale-source hold",
            "human_review_routing": _human_review(row, anchor),
            "rollback_notes": "remove this seed from the next metadata-only manifest draft; retain prior public corpus pointers",
        }
        candidates.append(candidate)
    candidates.sort(key=lambda item: (-int(item["rank_score"]), str(item["seed_id"])))
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    packet = {
        "packet_version": "next-public-refresh-seed-review-v1",
        "mode": "fixture-first-offline-review",
        "monitoring_plan_references": sorted(monitoring_refs),
        "official_source_anchor_placeholders": sorted(official_placeholders),
        "prohibited_actions": list(BLOCKED_ACTIONS),
        "validation_commands": VALIDATION_COMMANDS,
        "candidates": candidates,
    }
    assert_valid_packet(packet)
    return packet


def build_packet_from_files(monitoring_path: Path, source_anchor_path: Path) -> dict[str, Any]:
    monitoring_rows = _load_json(monitoring_path)
    source_anchor_rows = _load_json(source_anchor_path)
    if not isinstance(monitoring_rows, list) or not isinstance(source_anchor_rows, list):
        raise ValueError("fixtures must be JSON arrays")
    return build_packet(monitoring_rows, source_anchor_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an offline PP&D public refresh seed review packet.")
    parser.add_argument("--monitoring-fixture", required=True)
    parser.add_argument("--source-anchor-fixture", required=True)
    args = parser.parse_args()
    packet = build_packet_from_files(Path(args.monitoring_fixture), Path(args.source_anchor_fixture))
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
