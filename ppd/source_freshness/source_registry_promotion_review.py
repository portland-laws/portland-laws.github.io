"""Build fixture-first SourceRegistry promotion review packets.

The packet produced here is a review artifact only. It consumes an existing
release readiness snapshot and a SourceRegistry update candidate packet, then
summarizes the metadata-only changes that need human review before any future
promotion decision. It never crawls, fetches, or edits live registry records.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from ppd.source_freshness.invalidation_packet import PUBLIC_SOURCE_HOSTS, _looks_private_or_authenticated_url

REVIEW_PACKET_VERSION = 1
REQUIRED_CANDIDATE_FIELDS = frozenset(
    {
        "candidate_id",
        "source_id",
        "prior_registry_id",
        "canonical_url",
        "candidate_status",
        "registry_edit_status",
        "prior_fields",
        "proposed_fields",
        "changed_fields",
    }
)
APPROVED_BLOCKER_STATUSES = frozenset({"approved", "accepted", "cleared", "complete", "resolved"})
FALSEY_REVIEW_VALUES = frozenset({"", "false", "no", "none", "not_applied", "proposed_only", "review_packet_only"})
PRIVATE_ARTIFACT_KEYS = frozenset(
    {
        "auth_state",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "download_path",
        "downloaded_document",
        "downloaded_document_path",
        "downloadeddocumentpath",
        "downloaded_path",
        "har",
        "local_path",
        "password",
        "payment_details",
        "screenshot",
        "session_state",
        "storage_state",
        "trace",
    }
)
RAW_BODY_KEYS = frozenset(
    {
        "body",
        "body_text",
        "content_body",
        "document_bytes",
        "document_text",
        "html",
        "page_body",
        "pdf_body",
        "pdf_bytes",
        "rawbody",
        "raw_body",
        "raw_crawl_output",
        "raw_html",
        "raw_page_body",
        "response_body",
        "text_content",
    }
)
RAW_OR_ARCHIVE_PATH_KEYS = frozenset(
    {
        "archive_path",
        "archive_manifest_path",
        "archive_tar_path",
        "archive_zip_path",
        "crawl_output_path",
        "raw_archive",
        "raw_archive_path",
        "raw_crawl_path",
        "raw_crawl_output_path",
        "raw_warc_path",
        "warc",
        "warc_path",
        "wget_archive_path",
    }
)
LIVE_EDIT_KEYS = frozenset(
    {
        "apply_to_live_registry",
        "applied_to_live_registry",
        "edit_live_registry",
        "live_registry_edit",
        "live_registry_edited",
        "live_registry_records_edited",
        "live_registry_updated",
        "registry_mutated",
        "write_to_registry",
    }
)
LIVE_REPLACEMENT_KEYS = frozenset(
    {
        "live_registry_replacement",
        "production_registry",
        "production_registry_replacement",
        "production_source_registry",
        "replace_live_registry",
        "replace_production_registry",
        "replace_source_registry",
        "replacement_registry",
        "replacement_source_registry",
        "source_registry_replacement",
    }
)
RAW_OR_ARCHIVE_PATH_PATTERN = re.compile(
    r"(^|/)(raw[-_ ]?crawl|raw[-_ ]?archives?|archive[-_ ]?raw|warc|wget[-_ ]?archive)(/|$)|\\.warc(\\.gz)?$|\\.zip$|\\.tar(\\.gz)?$",
    re.IGNORECASE,
)
DOWNLOADED_DOCUMENT_PATH_PATTERN = re.compile(
    r"(^|/)(downloads?|downloaded[-_ ]?documents?)(/|$)|downloaded[^/\\s]*\\.(pdf|html?)$",
    re.IGNORECASE,
)
LOCAL_PATH_PATTERN = re.compile(r"^(file://|/home/|/users/|/tmp/|/var/folders/|[a-z]:\\\\users\\\\|[a-z]:\\\\temp\\\\)", re.IGNORECASE)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object fixture at {path}")
    return data


def _stable_id(*parts: str) -> str:
    joined = "|".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()[:16]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return sorted(set(value))


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _falsey_claim(value: Any) -> bool:
    if value is False or value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in FALSEY_REVIEW_VALUES
    return False


def _assert_public_url(url: str, label: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an http(s) URL")
    if parsed.netloc not in PUBLIC_SOURCE_HOSTS:
        raise ValueError(f"{label} is outside the PP&D public allowlist")
    if _looks_private_or_authenticated_url(url):
        raise ValueError(f"{label} is a private or authenticated URL")


def _assert_review_safe_artifacts(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_lower in RAW_BODY_KEYS:
                raise ValueError(f"raw crawl body field is not allowed in promotion review packets: {path}.{key_text}")
            if key_lower in PRIVATE_ARTIFACT_KEYS:
                raise ValueError(f"private artifact or downloaded document path is not allowed in promotion review packets: {path}.{key_text}")
            if key_lower in RAW_OR_ARCHIVE_PATH_KEYS:
                raise ValueError(f"raw crawl or archive path field is not allowed in promotion review packets: {path}.{key_text}")
            if key_lower in LIVE_EDIT_KEYS and not _falsey_claim(child):
                raise ValueError(f"live registry edits are not allowed in promotion review packets: {path}.{key_text}")
            if key_lower in LIVE_REPLACEMENT_KEYS and not _falsey_claim(child):
                raise ValueError(f"live registry replacement is not allowed in promotion review packets: {path}.{key_text}")
            if key_lower in {"registry_target", "target_registry"} and isinstance(child, str) and child.lower() in {"live", "prod", "production"}:
                raise ValueError(f"live registry replacement is not allowed in promotion review packets: {path}.{key_text}")
            _assert_review_safe_artifacts(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_review_safe_artifacts(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if RAW_OR_ARCHIVE_PATH_PATTERN.search(value):
            raise ValueError(f"raw crawl or archive path is not allowed in promotion review packets: {path}")
        if LOCAL_PATH_PATTERN.search(value) or DOWNLOADED_DOCUMENT_PATH_PATTERN.search(value):
            raise ValueError(f"downloaded document path is not allowed in promotion review packets: {path}")
        if _looks_private_or_authenticated_url(value):
            raise ValueError(f"private or authenticated URL is not allowed in promotion review packets: {path}")


def _candidate_rows(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = packet.get("source_registry_update_candidates")
    if not isinstance(rows, list) or not rows:
        raise ValueError("source_registry_update_candidates must be a non-empty list")
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("source registry update candidates must be objects")
        missing = sorted(field for field in REQUIRED_CANDIDATE_FIELDS if field not in row)
        if missing:
            raise ValueError(f"candidate {index} is missing required fields: {', '.join(missing)}")
        candidates.append(row)
    return candidates


def _assert_required_review_links(readiness_snapshot: Mapping[str, Any], candidate_packet: Mapping[str, Any]) -> dict[str, str]:
    readiness_packet_id = _text(readiness_snapshot.get("packet_id"))
    candidate_packet_id = _text(candidate_packet.get("packet_id"))
    candidate_fixture_id = _text(candidate_packet.get("fixture_id"))
    if not readiness_packet_id:
        raise ValueError("release readiness snapshot link requires packet_id")
    if not candidate_packet_id or not candidate_fixture_id:
        raise ValueError("source registry candidate link requires packet_id and fixture_id")

    linked_artifacts = _mapping(readiness_snapshot.get("linked_artifacts"), "release readiness snapshot linked_artifacts")
    candidate_link = _mapping(
        linked_artifacts.get("source_registry_update_candidate"),
        "release readiness snapshot source_registry_update_candidate link",
    )
    candidate_fixture = _text(candidate_link.get("fixture"))
    if not candidate_fixture:
        raise ValueError("release readiness snapshot must link the source registry update candidate fixture")

    evidence_catalog = readiness_snapshot.get("evidence_catalog")
    if not isinstance(evidence_catalog, list) or not evidence_catalog:
        raise ValueError("release readiness snapshot must include cited evidence_catalog links")
    cited_candidate = False
    for index, row in enumerate(evidence_catalog):
        evidence = _mapping(row, f"release readiness evidence_catalog[{index}]")
        if not _text(evidence.get("evidence_id")) or not _text(evidence.get("citation")):
            raise ValueError("release readiness evidence_catalog entries require evidence_id and citation")
        if _text(evidence.get("evidence_id")) == "source-registry-candidate-packet":
            cited_candidate = True
    if not cited_candidate:
        raise ValueError("release readiness snapshot must cite the source registry candidate packet")

    return {
        "release_readiness_packet_id": readiness_packet_id,
        "source_registry_candidate_packet_id": candidate_packet_id,
        "source_registry_candidate_fixture_id": candidate_fixture_id,
        "source_registry_candidate_fixture": candidate_fixture,
    }


def _assert_review_only_inputs(readiness_snapshot: Mapping[str, Any], candidate_packet: Mapping[str, Any]) -> dict[str, str]:
    _assert_review_safe_artifacts(readiness_snapshot, "release_readiness_snapshot")
    _assert_review_safe_artifacts(candidate_packet, "source_registry_update_candidate_packet")
    links = _assert_required_review_links(readiness_snapshot, candidate_packet)
    if candidate_packet.get("fixture_first") is not True:
        raise ValueError("source registry update candidate packet must be fixture_first=true")
    if candidate_packet.get("metadata_only") is not True:
        raise ValueError("source registry update candidate packet must be metadata_only=true")
    if candidate_packet.get("network_requests_made") is not False:
        raise ValueError("source registry promotion review cannot include live network evidence")
    if candidate_packet.get("raw_page_bodies_stored") is not False:
        raise ValueError("source registry promotion review cannot include raw page bodies")
    if candidate_packet.get("live_registry_edited") is not False:
        raise ValueError("source registry promotion review requires live_registry_edited=false")
    if readiness_snapshot.get("forbidden_live_evidence_present") is True:
        raise ValueError("release readiness snapshot contains forbidden live evidence")
    if readiness_snapshot.get("production_ready") is True:
        raise ValueError("promotion review packets must not consume a production-ready snapshot")
    return links


def _release_blockers(readiness_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    blocker_rows = readiness_snapshot.get("release_blockers", [])
    if blocker_rows is None:
        blocker_rows = []
    if not isinstance(blocker_rows, list):
        raise ValueError("release_blockers must be a list when present")
    unresolved_ids = set(_string_list(readiness_snapshot.get("unresolved_blockers"), "unresolved_blockers"))
    seen_ids: set[str] = set()
    blockers: list[dict[str, Any]] = []
    for row in blocker_rows:
        blocker = _mapping(row, "release blocker")
        blocker_id = _text(blocker.get("id"))
        if not blocker_id:
            raise ValueError("release blockers require id")
        seen_ids.add(blocker_id)
        status = (_text(blocker.get("status")) or "blocking").lower()
        if blocker_id in unresolved_ids and status in APPROVED_BLOCKER_STATUSES:
            raise ValueError(f"unresolved blocker {blocker_id} cannot be marked {status}")
        if not unresolved_ids or blocker_id in unresolved_ids or status == "blocking":
            blockers.append(
                {
                    "blocker_id": blocker_id,
                    "status": status,
                    "summary": _text(blocker.get("summary")),
                    "source_evidence_ids": _string_list(blocker.get("source_evidence_ids"), "source_evidence_ids"),
                }
            )
    missing_unresolved = sorted(unresolved_ids - seen_ids)
    if missing_unresolved:
        raise ValueError("unresolved_blockers references unknown release blockers: " + ", ".join(missing_unresolved))
    return sorted(blockers, key=lambda item: item["blocker_id"])


def _has_downstream_links(candidate: Mapping[str, Any]) -> bool:
    links = candidate.get("downstream_invalidation_links")
    if not isinstance(links, Mapping):
        return False
    for value in links.values():
        if isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value):
            return True
    return False


def _exact_field_changes(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    prior_fields = _mapping(candidate.get("prior_fields"), "candidate prior_fields")
    proposed_fields = _mapping(candidate.get("proposed_fields"), "candidate proposed_fields")
    changed_fields = _string_list(candidate.get("changed_fields"), "changed_fields")
    review_evidence_id = _text(candidate.get("review_evidence_id"))
    if changed_fields and not review_evidence_id:
        raise ValueError(f"candidate {_text(candidate.get('candidate_id'))} has uncited field changes and requires review_evidence_id")
    if changed_fields and not _has_downstream_links(candidate):
        raise ValueError(f"candidate {_text(candidate.get('candidate_id'))} field changes require downstream candidate links")
    exact_changes: list[dict[str, Any]] = []
    for field in changed_fields:
        prior_value = prior_fields.get(field)
        proposed_value = proposed_fields.get(field)
        if prior_value == proposed_value:
            raise ValueError(f"changed field {field} has identical prior and proposed values")
        exact_changes.append(
            {
                "field_name": field,
                "prior_value": prior_value,
                "proposed_value": proposed_value,
                "review_evidence_id": review_evidence_id,
                "change_status": "reviewed_metadata_only_candidate_change",
            }
        )
    return exact_changes


def _reviewed_change_rows(candidate_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in sorted(_candidate_rows(candidate_packet), key=lambda row: _text(row.get("source_id"))):
        if _text(candidate.get("candidate_status")) != "proposed_only":
            raise ValueError("source registry candidates must remain proposed_only")
        if _text(candidate.get("registry_edit_status")) != "not_applied":
            raise ValueError("source registry candidates must have registry_edit_status=not_applied")
        canonical_url = _text(candidate.get("canonical_url"))
        _assert_public_url(canonical_url, f"candidate {_text(candidate.get('candidate_id'))} canonical_url")
        exact_changes = _exact_field_changes(candidate)
        rows.append(
            {
                "candidate_id": _text(candidate.get("candidate_id")),
                "source_id": _text(candidate.get("source_id")),
                "prior_registry_id": _text(candidate.get("prior_registry_id")),
                "canonical_url": canonical_url,
                "review_evidence_id": _text(candidate.get("review_evidence_id")) or None,
                "changed_field_count": len(exact_changes),
                "exact_metadata_field_changes": exact_changes,
                "downstream_invalidation_links": deepcopy(candidate.get("downstream_invalidation_links", {})),
                "registry_edit_status": "not_applied",
            }
        )
    return rows


def _reviewer_prompts(change_rows: list[Mapping[str, Any]], blockers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    for row in change_rows:
        source_id = _text(row.get("source_id"))
        changed_fields = [change["field_name"] for change in row.get("exact_metadata_field_changes", [])]
        prompts.append(
            {
                "prompt_id": "review-source-registry-candidate-" + _stable_id(source_id, ",".join(changed_fields)),
                "source_id": source_id,
                "candidate_id": _text(row.get("candidate_id")),
                "prompt": "Confirm that the listed metadata-only SourceRegistry field changes are supported by the cited review evidence and should remain candidates until a separate promotion step is approved.",
                "fields_to_review": changed_fields,
                "required_response": "approve_candidate_change_or_request_rework",
            }
        )
    if blockers:
        prompts.append(
            {
                "prompt_id": "review-release-blockers-" + _stable_id(*(blocker["blocker_id"] for blocker in blockers)),
                "source_id": None,
                "candidate_id": None,
                "prompt": "Resolve or explicitly defer every unresolved release blocker before production SourceRegistry promotion can be reconsidered.",
                "fields_to_review": [],
                "required_response": "resolve_blockers_or_keep_promotion_disabled",
            }
        )
    return prompts


def _rollback_notes(change_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for row in change_rows:
        prior_fields = {change["field_name"]: change["prior_value"] for change in row.get("exact_metadata_field_changes", [])}
        notes.append(
            {
                "note_id": "rollback-source-registry-candidate-" + _stable_id(_text(row.get("candidate_id"))),
                "source_id": _text(row.get("source_id")),
                "candidate_id": _text(row.get("candidate_id")),
                "rollback_action": "discard_review_packet_and_candidate_changes_only",
                "prior_fields_to_preserve": prior_fields,
                "live_registry_action_required": False,
                "notes": "No production rollback is required because this packet does not edit live SourceRegistry records.",
            }
        )
    return notes


def build_source_registry_promotion_review_packet(
    release_readiness_snapshot: Mapping[str, Any],
    source_registry_update_candidate_packet: Mapping[str, Any],
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    """Build a review-only SourceRegistry promotion packet from fixtures."""
    readiness = deepcopy(dict(release_readiness_snapshot))
    candidate_packet = deepcopy(dict(source_registry_update_candidate_packet))
    input_links = _assert_review_only_inputs(readiness, candidate_packet)

    blockers = _release_blockers(readiness)
    change_rows = _reviewed_change_rows(candidate_packet)
    packet = {
        "packet_id": "source-registry-promotion-review-"
        + _stable_id(
            _text(readiness.get("packet_id")),
            _text(candidate_packet.get("packet_id")),
            generated_at,
        ),
        "packet_version": REVIEW_PACKET_VERSION,
        "generated_at": generated_at,
        "fixture_first": True,
        "metadata_only": True,
        "network_requests_made": False,
        "raw_page_bodies_stored": False,
        "live_registry_edited": False,
        "review_mode": "promotion_review_only",
        "input_artifact_links": input_links,
        "release_readiness_snapshot": {
            "packet_id": _text(readiness.get("packet_id")),
            "readiness_status": _text(readiness.get("readiness_status")),
            "production_status": _text(readiness.get("production_status")),
            "production_ready": readiness.get("production_ready") is True,
        },
        "source_registry_update_candidate": {
            "packet_id": _text(candidate_packet.get("packet_id")),
            "fixture_id": _text(candidate_packet.get("fixture_id")),
            "candidate_count": candidate_packet.get("candidate_count"),
            "changed_candidate_count": candidate_packet.get("changed_candidate_count"),
            "live_registry_edited": False,
        },
        "production_promotion_status": {
            "enabled": False,
            "status": "disabled_review_packet_only",
            "reason": "release readiness snapshot still has unresolved blockers and candidate changes have not been approved for live SourceRegistry mutation",
            "live_registry_records_edited": False,
        },
        "unresolved_blockers": blockers,
        "reviewed_metadata_only_field_changes": change_rows,
        "reviewer_prompts": _reviewer_prompts(change_rows, blockers),
        "rollback_notes": _rollback_notes(change_rows),
        "validation_notes": [
            "packet consumes committed readiness and source-registry candidate fixtures only",
            "exact prior and proposed metadata field values are listed for review",
            "every changed field is tied to review_evidence_id and downstream candidate links",
            "production SourceRegistry promotion remains disabled",
            "no live registry records are edited by this packet",
        ],
    }
    _assert_review_safe_artifacts(packet)
    return packet


def load_source_registry_promotion_review_packet(
    release_readiness_snapshot_path: Path,
    source_registry_update_candidate_packet_path: Path,
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    return build_source_registry_promotion_review_packet(
        _read_json(release_readiness_snapshot_path),
        _read_json(source_registry_update_candidate_packet_path),
        generated_at=generated_at,
    )
