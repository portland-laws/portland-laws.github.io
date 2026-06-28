"""Fixture-first source registry promotion rehearsal packets.

The rehearsal packet is intentionally metadata-only. It consumes a promotion
review and a public-recrawl operator checklist, then emits a disabled-by-default
promotion decision without mutating live source registry records.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse


DISALLOWED_LIVE_RECORD_FIELDS = {
    "last_seen_at",
    "freshness_status",
    "canonical_url",
    "source_type",
    "owning_surface",
    "allowlist_policy",
    "robots_policy",
    "crawl_frequency",
    "processor_policy",
    "privacy_classification",
}

PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

PRIVATE_URL_MARKERS = (
    "/account",
    "/accounts",
    "/application",
    "/applications",
    "/auth",
    "/cart",
    "/dashboard",
    "/login",
    "/payment",
    "/payments",
    "/permit/",
    "/permits/",
    "/session",
    "/sessions",
    "/signin",
    "/upload",
    "/uploads",
)

PRIVATE_QUERY_MARKERS = (
    "access_token=",
    "auth=",
    "code=",
    "password=",
    "session=",
    "token=",
)

RAW_OR_ARCHIVE_KEYS = {
    "archive_path",
    "archive_manifest_path",
    "archive_tar_path",
    "archive_zip_path",
    "crawl_output_path",
    "raw_archive",
    "raw_archive_path",
    "raw_crawl_output",
    "raw_crawl_output_path",
    "raw_crawl_path",
    "raw_html",
    "raw_warc_path",
    "response_body",
    "warc",
    "warc_path",
}

PRIVATE_OR_DOWNLOADED_KEYS = {
    "auth_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download_path",
    "downloaded_document",
    "downloaded_document_path",
    "har",
    "local_path",
    "password",
    "pdf_path",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
}

LIVE_REPLACEMENT_KEYS = {
    "apply_to_live_registry",
    "live_registry_replacement",
    "production_registry_replacement",
    "replace_live_registry",
    "replace_production_registry",
    "replace_source_registry",
    "replacement_registry",
    "source_registry_replacement",
    "write_to_registry",
}

RAW_OR_ARCHIVE_PATH_PATTERN = re.compile(
    r"(^|/)(raw[-_ ]?crawl|raw[-_ ]?archives?|archive[-_ ]?raw|warc|wget[-_ ]?archive)(/|$)|\\.warc(\\.gz)?$|\\.zip$|\\.tar(\\.gz)?$",
    re.IGNORECASE,
)

DOWNLOADED_DOCUMENT_PATH_PATTERN = re.compile(
    r"(^|/)(downloads?|downloaded[-_ ]?documents?)(/|$)|downloaded[^/\\s]*\\.(pdf|html?)$",
    re.IGNORECASE,
)

LOCAL_PATH_PATTERN = re.compile(r"^(file://|/home/|/users/|/tmp/|/var/folders/|[a-z]:\\\\users\\\\|[a-z]:\\\\temp\\\\)", re.IGNORECASE)

APPROVED_STATUSES = {"approved", "accepted", "cleared", "complete", "resolved"}
UNRESOLVED_STATUSES = {"blocking", "blocked", "open", "pending", "unresolved"}


class RehearsalPacketError(ValueError):
    """Raised when rehearsal inputs are not metadata-only and reviewable."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RehearsalPacketError(f"{path} must contain a JSON object")
    return data


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RehearsalPacketError(f"{field_name} must be a non-empty string")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise RehearsalPacketError(f"{field_name} must be a list")
    return value


def _falsey_claim(value: Any) -> bool:
    if value is False or value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "false", "no", "none", "not_applied", "rehearsal_only", "review_only"}
    return False


def _is_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value)
    path = parsed.path.lower()
    query = parsed.query.lower()
    return any(marker in path for marker in PRIVATE_URL_MARKERS) or any(marker in query for marker in PRIVATE_QUERY_MARKERS)


def _assert_public_url(value: str, field_name: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RehearsalPacketError(f"{field_name} must be an http(s) URL")
    if parsed.netloc not in PUBLIC_HOSTS:
        raise RehearsalPacketError(f"{field_name} is outside the PP&D public allowlist")
    if _is_private_or_authenticated_url(value):
        raise RehearsalPacketError(f"{field_name} must not be private or authenticated")


def _assert_no_unsafe_artifacts(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_lower in RAW_OR_ARCHIVE_KEYS:
                raise RehearsalPacketError(f"raw crawl or archive path is not allowed: {child_path}")
            if key_lower in PRIVATE_OR_DOWNLOADED_KEYS:
                raise RehearsalPacketError(f"private, authenticated, or downloaded document artifact is not allowed: {child_path}")
            if key_lower in LIVE_REPLACEMENT_KEYS and not _falsey_claim(child):
                raise RehearsalPacketError(f"direct live registry replacement is not allowed: {child_path}")
            if key_lower in {"registry_target", "target_registry"} and isinstance(child, str) and child.strip().lower() in {"live", "prod", "production"}:
                raise RehearsalPacketError(f"direct live registry replacement is not allowed: {child_path}")
            _assert_no_unsafe_artifacts(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_unsafe_artifacts(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if RAW_OR_ARCHIVE_PATH_PATTERN.search(value):
            raise RehearsalPacketError(f"raw crawl or archive path is not allowed: {path}")
        if DOWNLOADED_DOCUMENT_PATH_PATTERN.search(value) or LOCAL_PATH_PATTERN.search(value):
            raise RehearsalPacketError(f"downloaded document path is not allowed: {path}")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and _is_private_or_authenticated_url(value):
            raise RehearsalPacketError(f"private or authenticated URL is not allowed: {path}")


def _assert_no_unresolved_blocker_approval(packet: Mapping[str, Any]) -> None:
    unresolved_ids = packet.get("unresolved_blockers", [])
    unresolved_id_set = {str(item) for item in unresolved_ids if isinstance(item, str)} if isinstance(unresolved_ids, list) else set()
    blockers = packet.get("release_blockers", packet.get("blockers", []))
    if not isinstance(blockers, list):
        return
    for index, blocker in enumerate(blockers):
        if not isinstance(blocker, Mapping):
            continue
        blocker_id = str(blocker.get("id") or blocker.get("blocker_id") or "")
        status = str(blocker.get("status", "")).strip().lower()
        review_status = str(blocker.get("review_status") or blocker.get("approval_status") or "").strip().lower()
        resolved = blocker.get("resolved") is True
        unresolved = blocker_id in unresolved_id_set or status in UNRESOLVED_STATUSES or not resolved
        approved = status in APPROVED_STATUSES or review_status in APPROVED_STATUSES
        if unresolved and approved:
            raise RehearsalPacketError(f"unresolved blocker cannot be marked approved: release_blockers[{index}]")


def _normalize_acknowledgements(review: dict[str, Any]) -> list[dict[str, Any]]:
    acknowledgements = _require_list(review.get("reviewer_acknowledgements"), "reviewer_acknowledgements")
    normalized: list[dict[str, Any]] = []
    for index, acknowledgement in enumerate(acknowledgements):
        if not isinstance(acknowledgement, dict):
            raise RehearsalPacketError(f"reviewer_acknowledgements[{index}] must be an object")
        normalized.append(
            {
                "reviewer_role": _require_string(acknowledgement.get("reviewer_role"), f"reviewer_acknowledgements[{index}].reviewer_role"),
                "acknowledged_at": _require_string(acknowledgement.get("acknowledged_at"), f"reviewer_acknowledgements[{index}].acknowledged_at"),
                "acknowledged_scope": _require_string(acknowledgement.get("acknowledged_scope"), f"reviewer_acknowledgements[{index}].acknowledged_scope"),
                "notes": str(acknowledgement.get("notes", "")),
            }
        )
    return normalized


def _normalize_metadata_diffs(review: dict[str, Any]) -> list[dict[str, Any]]:
    diffs = _require_list(review.get("candidate_metadata_diffs"), "candidate_metadata_diffs")
    normalized: list[dict[str, Any]] = []
    for index, diff in enumerate(diffs):
        if not isinstance(diff, dict):
            raise RehearsalPacketError(f"candidate_metadata_diffs[{index}] must be an object")
        canonical_url = _require_string(diff.get("canonical_url"), f"candidate_metadata_diffs[{index}].canonical_url")
        _assert_public_url(canonical_url, f"candidate_metadata_diffs[{index}].canonical_url")
        metadata_field_diffs = _require_list(diff.get("metadata_field_diffs"), f"candidate_metadata_diffs[{index}].metadata_field_diffs")
        fields: list[dict[str, Any]] = []
        for field_index, field_diff in enumerate(metadata_field_diffs):
            if not isinstance(field_diff, dict):
                raise RehearsalPacketError(f"candidate_metadata_diffs[{index}].metadata_field_diffs[{field_index}] must be an object")
            field_name = _require_string(field_diff.get("field"), f"candidate_metadata_diffs[{index}].metadata_field_diffs[{field_index}].field")
            if field_name in DISALLOWED_LIVE_RECORD_FIELDS:
                raise RehearsalPacketError(f"metadata rehearsal cannot propose direct live source record field edit: {field_name}")
            fields.append(
                {
                    "field": field_name,
                    "before": field_diff.get("before"),
                    "after": field_diff.get("after"),
                    "reason": _require_string(field_diff.get("reason"), f"candidate_metadata_diffs[{index}].metadata_field_diffs[{field_index}].reason"),
                }
            )
        normalized.append(
            {
                "source_id": _require_string(diff.get("source_id"), f"candidate_metadata_diffs[{index}].source_id"),
                "canonical_url": canonical_url,
                "metadata_field_diffs": fields,
            }
        )
    return normalized


def _normalize_rollback_checkpoints(review: dict[str, Any]) -> list[dict[str, Any]]:
    checkpoints = _require_list(review.get("rollback_checkpoints"), "rollback_checkpoints")
    if not checkpoints:
        raise RehearsalPacketError("rollback_checkpoints must include at least one checkpoint")
    normalized: list[dict[str, Any]] = []
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, dict):
            raise RehearsalPacketError(f"rollback_checkpoints[{index}] must be an object")
        required = checkpoint.get("required_before_promotion", True)
        if required is not True:
            raise RehearsalPacketError(f"rollback_checkpoints[{index}].required_before_promotion must be true")
        normalized.append(
            {
                "checkpoint_id": _require_string(checkpoint.get("checkpoint_id"), f"rollback_checkpoints[{index}].checkpoint_id"),
                "description": _require_string(checkpoint.get("description"), f"rollback_checkpoints[{index}].description"),
                "required_before_promotion": True,
            }
        )
    return normalized


def _normalize_downstream_notes(review: dict[str, Any]) -> list[dict[str, Any]]:
    notes = _require_list(review.get("downstream_invalidation_notes"), "downstream_invalidation_notes")
    normalized: list[dict[str, Any]] = []
    for index, note in enumerate(notes):
        if not isinstance(note, dict):
            raise RehearsalPacketError(f"downstream_invalidation_notes[{index}] must be an object")
        normalized.append(
            {
                "consumer": _require_string(note.get("consumer"), f"downstream_invalidation_notes[{index}].consumer"),
                "invalidation_scope": _require_string(note.get("invalidation_scope"), f"downstream_invalidation_notes[{index}].invalidation_scope"),
                "recommended_action": _require_string(note.get("recommended_action"), f"downstream_invalidation_notes[{index}].recommended_action"),
            }
        )
    return normalized


def _normalize_checklist(checklist: dict[str, Any]) -> dict[str, Any]:
    items = _require_list(checklist.get("completed_items"), "completed_items")
    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise RehearsalPacketError(f"completed_items[{index}] must be an object")
        normalized_items.append(
            {
                "item_id": _require_string(item.get("item_id"), f"completed_items[{index}].item_id"),
                "status": _require_string(item.get("status"), f"completed_items[{index}].status"),
                "evidence": _require_string(item.get("evidence"), f"completed_items[{index}].evidence"),
            }
        )
    return {
        "checklist_id": _require_string(checklist.get("checklist_id"), "checklist_id"),
        "public_recrawl_run_id": _require_string(checklist.get("public_recrawl_run_id"), "public_recrawl_run_id"),
        "operator": _require_string(checklist.get("operator"), "operator"),
        "completed_items": normalized_items,
    }


def validate_rehearsal_packet(packet: Mapping[str, Any]) -> None:
    """Fail closed when a source registry promotion rehearsal packet is unsafe."""

    if packet.get("packet_type") != "source_registry_promotion_rehearsal":
        raise RehearsalPacketError("packet_type must be source_registry_promotion_rehearsal")
    if packet.get("packet_version") != "1.0":
        raise RehearsalPacketError("packet_version must be 1.0")

    consumes = packet.get("consumes")
    if not isinstance(consumes, Mapping):
        raise RehearsalPacketError("consumes must be an object")
    if not consumes.get("promotion_review_id"):
        raise RehearsalPacketError("missing promotion-review link")
    if not consumes.get("operator_checklist_id"):
        raise RehearsalPacketError("missing operator-checklist link")

    input_links = packet.get("input_artifact_links")
    if not isinstance(input_links, Mapping):
        raise RehearsalPacketError("input_artifact_links must be an object")
    if input_links.get("promotion_review_id") != consumes.get("promotion_review_id"):
        raise RehearsalPacketError("input_artifact_links must include matching promotion-review link")
    if input_links.get("operator_checklist_id") != consumes.get("operator_checklist_id"):
        raise RehearsalPacketError("input_artifact_links must include matching operator-checklist link")

    safety = packet.get("safety")
    if not isinstance(safety, Mapping):
        raise RehearsalPacketError("safety must be an object")
    expected_safety = {
        "fixture_first": True,
        "metadata_only": True,
        "live_source_records_edited": False,
        "raw_crawl_output_included": False,
        "authenticated_state_included": False,
    }
    for key, expected in expected_safety.items():
        if safety.get(key) is not expected:
            raise RehearsalPacketError(f"safety.{key} must be {str(expected).lower()}")

    rollback_checkpoints = packet.get("rollback_checkpoints")
    if not isinstance(rollback_checkpoints, list) or not rollback_checkpoints:
        raise RehearsalPacketError("rollback_checkpoints must include at least one checkpoint")
    for index, checkpoint in enumerate(rollback_checkpoints):
        if not isinstance(checkpoint, Mapping):
            raise RehearsalPacketError(f"rollback_checkpoints[{index}] must be an object")
        if checkpoint.get("required_before_promotion") is not True:
            raise RehearsalPacketError(f"rollback_checkpoints[{index}].required_before_promotion must be true")

    decision = packet.get("promotion_decision")
    if not isinstance(decision, Mapping):
        raise RehearsalPacketError("promotion_decision must be an object")
    if decision.get("enabled") is not False:
        raise RehearsalPacketError("promotion_decision.enabled must be false")
    if decision.get("decision") != "rehearsal_only_defer_promotion":
        raise RehearsalPacketError("promotion_decision.decision must defer promotion")
    if decision.get("requires_human_enablement") is not True:
        raise RehearsalPacketError("promotion_decision.requires_human_enablement must be true")

    for diff_index, diff in enumerate(packet.get("metadata_only_field_diffs", [])):
        if isinstance(diff, Mapping):
            canonical_url = diff.get("canonical_url")
            if isinstance(canonical_url, str):
                _assert_public_url(canonical_url, f"metadata_only_field_diffs[{diff_index}].canonical_url")

    _assert_no_unresolved_blocker_approval(packet)
    _assert_no_unsafe_artifacts(packet, "packet")


def build_rehearsal_packet(review: dict[str, Any], checklist: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic disabled-by-default promotion rehearsal packet."""

    _assert_no_unsafe_artifacts(review, "promotion_review")
    _assert_no_unsafe_artifacts(checklist, "operator_checklist")
    _assert_no_unresolved_blocker_approval(review)

    review_id = _require_string(review.get("review_id"), "review_id")
    generated_at = _require_string(review.get("generated_at"), "generated_at")
    source_registry_version = _require_string(review.get("source_registry_version"), "source_registry_version")
    normalized_checklist = _normalize_checklist(checklist)

    packet = {
        "packet_type": "source_registry_promotion_rehearsal",
        "packet_version": "1.0",
        "generated_at": generated_at,
        "consumes": {
            "promotion_review_id": review_id,
            "source_registry_version": source_registry_version,
            "operator_checklist_id": normalized_checklist["checklist_id"],
            "public_recrawl_run_id": normalized_checklist["public_recrawl_run_id"],
        },
        "input_artifact_links": {
            "promotion_review_id": review_id,
            "promotion_review_kind": "source_registry_promotion_review",
            "operator_checklist_id": normalized_checklist["checklist_id"],
            "operator_checklist_kind": "public_recrawl_operator_checklist",
        },
        "safety": {
            "fixture_first": True,
            "metadata_only": True,
            "live_source_records_edited": False,
            "raw_crawl_output_included": False,
            "authenticated_state_included": False,
        },
        "public_recrawl_operator_checklist": normalized_checklist,
        "metadata_only_field_diffs": _normalize_metadata_diffs(review),
        "reviewer_acknowledgements": _normalize_acknowledgements(review),
        "rollback_checkpoints": _normalize_rollback_checkpoints(review),
        "downstream_invalidation_notes": _normalize_downstream_notes(review),
        "release_blockers": list(review.get("release_blockers", [])) if isinstance(review.get("release_blockers", []), list) else [],
        "unresolved_blockers": list(review.get("unresolved_blockers", [])) if isinstance(review.get("unresolved_blockers", []), list) else [],
        "promotion_decision": {
            "enabled": False,
            "decision": "rehearsal_only_defer_promotion",
            "requires_human_enablement": True,
            "reason": "Fixture rehearsal packets must not promote or edit live source registry records.",
        },
    }
    validate_rehearsal_packet(packet)
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PP&D source registry promotion rehearsal packet.")
    parser.add_argument("review", type=Path)
    parser.add_argument("checklist", type=Path)
    args = parser.parse_args()

    packet = build_rehearsal_packet(load_json(args.review), load_json(args.checklist))
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
