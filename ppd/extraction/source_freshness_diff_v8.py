"""Fixture-first source freshness diff intake v8.

This module is intentionally offline-only. It consumes committed fixture JSON for a
processor handoff dry-run manifest v8 and a prior source registry fixture, then
assembles deterministic freshness diff intake rows for reviewer and downstream
requirement extraction workflows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/extraction/source_freshness_diff_v8.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_source_freshness_diff_v8.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_FORBIDDEN_ARTIFACT_KEYS = {
    "archive_artifact_ref",
    "auth_state",
    "auth_state_path",
    "cookie_jar",
    "cookies",
    "credentials",
    "downloaded_document_path",
    "har_path",
    "private_artifact_ref",
    "raw_artifact_path",
    "raw_body",
    "raw_body_path",
    "screenshot_path",
    "session_artifact_ref",
    "session_storage",
    "trace_path",
}

_FALSE_REQUIRED_CLAIMS = {
    "active_mutation_flags",
    "devhub_opened",
    "legal_or_permitting_guarantees_made",
    "live_crawl_performed",
    "official_action_completed",
    "official_action_completion_claimed",
    "private_documents_read",
    "raw_artifacts_downloaded",
    "uploads_or_submissions_performed",
}

_REQUIRED_PACKET_LIST_FIELDS = {
    "changed_source_hash_rows": "changed-source hash rows",
    "unchanged_source_rows": "unchanged-source rows",
    "added_link_observations": "added link observations",
    "removed_link_observations": "removed link observations",
    "affected_citation_placeholders": "affected citation placeholders",
    "downstream_requirement_reextraction_candidate_refs": "downstream requirement re-extraction candidate references",
    "reviewer_hold_notes": "reviewer hold notes",
    "offline_validation_commands": "validation commands",
}


def load_fixture_json(path: Path | str) -> dict[str, Any]:
    """Load a JSON fixture from disk."""
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return value


def assemble_source_freshness_diff_v8(
    processor_handoff_manifest: dict[str, Any],
    prior_source_registry: dict[str, Any],
) -> dict[str, Any]:
    """Assemble an offline freshness diff from v8 fixtures only."""
    _validate_processor_handoff_manifest(processor_handoff_manifest)
    _validate_prior_source_registry(prior_source_registry)

    manifest_rows = _manifest_sources(processor_handoff_manifest)
    prior_rows = _prior_sources(prior_source_registry)

    manifest_by_source_id = {row["source_id"]: row for row in manifest_rows}
    prior_by_source_id = {row["source_id"]: row for row in prior_rows}

    changed_hash_rows: list[dict[str, Any]] = []
    unchanged_rows: list[dict[str, Any]] = []
    added_link_observations: list[dict[str, Any]] = []
    removed_link_observations: list[dict[str, Any]] = []
    affected_citation_placeholders: list[dict[str, Any]] = []
    candidate_refs: list[dict[str, Any]] = []
    hold_notes: list[dict[str, Any]] = []

    all_source_ids = sorted(set(manifest_by_source_id) | set(prior_by_source_id))

    for source_id in all_source_ids:
        current = manifest_by_source_id.get(source_id)
        prior = prior_by_source_id.get(source_id)

        if current is None and prior is not None:
            hold_notes.append(
                {
                    "source_id": source_id,
                    "hold_code": "source_absent_from_dry_run_manifest_v8",
                    "note": "Prior source registry fixture includes this source, but the dry-run handoff fixture does not. Reviewer should confirm whether it was intentionally removed before downstream guardrails are changed.",
                }
            )
            affected_citation_placeholders.extend(
                _citation_rows(prior, "removed_source_needs_review")
            )
            candidate_refs.extend(
                _candidate_rows(prior, "source_removed_from_manifest_fixture")
            )
            continue

        if current is not None and prior is None:
            hold_notes.append(
                {
                    "source_id": source_id,
                    "hold_code": "new_source_in_dry_run_manifest_v8",
                    "note": "Dry-run handoff fixture includes a source that is not in the prior source registry fixture. Reviewer should approve registry onboarding before it influences guardrails.",
                }
            )
            changed_hash_rows.append(_changed_hash_row(current, None, "new_source"))
            affected_citation_placeholders.extend(
                _citation_rows(current, "new_source_needs_review")
            )
            candidate_refs.extend(_candidate_rows(current, "new_source"))
            _append_link_deltas(
                source_id,
                old_links=[],
                new_links=current.get("links", []),
                added_link_observations=added_link_observations,
                removed_link_observations=removed_link_observations,
            )
            continue

        if current is None or prior is None:
            continue

        current_hash = _optional_text(current.get("content_hash"))
        prior_hash = _optional_text(prior.get("content_hash"))
        if current_hash is None or prior_hash is None:
            hold_notes.append(
                {
                    "source_id": source_id,
                    "hold_code": "missing_content_hash_for_diff",
                    "note": "One fixture row lacks a content hash, so the intake records a reviewer hold instead of inferring freshness.",
                }
            )
            changed_hash_rows.append(_changed_hash_row(current, prior, "missing_hash_review"))
            affected_citation_placeholders.extend(
                _citation_rows(current, "hash_missing_needs_review")
            )
            candidate_refs.extend(_candidate_rows(current, "hash_missing_review"))
        elif current_hash == prior_hash:
            unchanged_rows.append(
                {
                    "source_id": source_id,
                    "canonical_url": current["canonical_url"],
                    "content_hash": current_hash,
                    "freshness_status": "unchanged",
                    "prior_last_seen_at": prior.get("last_seen_at"),
                    "dry_run_seen_at": current.get("capture_finished_at"),
                }
            )
        else:
            changed_hash_rows.append(_changed_hash_row(current, prior, "hash_changed"))
            affected_citation_placeholders.extend(
                _citation_rows(current, "source_hash_changed")
            )
            candidate_refs.extend(_candidate_rows(current, "source_hash_changed"))

        old_links = prior.get("links", prior.get("observed_links", []))
        new_links = current.get("links", [])
        _append_link_deltas(
            source_id,
            old_links=old_links,
            new_links=new_links,
            added_link_observations=added_link_observations,
            removed_link_observations=removed_link_observations,
        )

    link_delta_source_ids = {
        row["source_id"] for row in added_link_observations + removed_link_observations
    }
    for source_id in sorted(link_delta_source_ids):
        current = manifest_by_source_id.get(source_id) or prior_by_source_id.get(source_id)
        if current is None:
            continue
        affected_citation_placeholders.extend(
            _citation_rows(current, "source_link_observations_changed")
        )
        candidate_refs.extend(_candidate_rows(current, "source_link_observations_changed"))

    intake = {
        "intake_version": "source_freshness_diff_v8",
        "processor_handoff_manifest_ref": _required_packet_ref(
            processor_handoff_manifest,
            ("manifest_id", "processor_handoff_manifest_id"),
            "processor handoff manifest reference",
        ),
        "prior_source_registry_ref": _required_packet_ref(
            prior_source_registry,
            ("registry_id", "source_registry_id"),
            "source registry reference",
        ),
        "input_constraints": {
            "fixture_first": True,
            "accepted_inputs": [
                "processor_handoff_dry_run_manifest_v8_fixture",
                "prior_source_registry_fixture",
            ],
            "live_crawl_performed": False,
            "raw_artifacts_downloaded": False,
            "devhub_opened": False,
            "private_documents_read": False,
            "uploads_or_submissions_performed": False,
            "official_action_completed": False,
            "legal_or_permitting_guarantees_made": False,
            "active_mutation_flags": False,
        },
        "changed_source_hash_rows": _dedupe_dicts(changed_hash_rows),
        "unchanged_source_rows": _dedupe_dicts(unchanged_rows),
        "added_link_observations": _dedupe_dicts(added_link_observations),
        "removed_link_observations": _dedupe_dicts(removed_link_observations),
        "affected_citation_placeholders": _dedupe_dicts(affected_citation_placeholders),
        "downstream_requirement_reextraction_candidate_refs": _dedupe_dicts(candidate_refs),
        "reviewer_hold_notes": _dedupe_dicts(hold_notes),
        "offline_validation_commands": _OFFLINE_VALIDATION_COMMANDS,
    }
    validate_source_freshness_diff_v8_packet(intake)
    return intake


def assemble_from_fixture_paths(
    processor_handoff_manifest_path: Path | str,
    prior_source_registry_path: Path | str,
) -> dict[str, Any]:
    """Load v8 fixtures and assemble the freshness diff intake."""
    return assemble_source_freshness_diff_v8(
        load_fixture_json(processor_handoff_manifest_path),
        load_fixture_json(prior_source_registry_path),
    )


def validate_source_freshness_diff_v8_packet(packet: dict[str, Any]) -> None:
    """Fail closed on incomplete or unsafe source freshness diff intake v8 packets."""
    if packet.get("intake_version") != "source_freshness_diff_v8":
        raise ValueError("source freshness diff intake v8 packet must declare intake_version")

    _required_text(packet, "processor_handoff_manifest_ref")
    _required_text(packet, "prior_source_registry_ref")

    for field, label in _REQUIRED_PACKET_LIST_FIELDS.items():
        value = packet.get(field)
        if not isinstance(value, list) or not value:
            raise ValueError(f"source freshness diff intake v8 packet missing {label}")

    if packet.get("offline_validation_commands") != _OFFLINE_VALIDATION_COMMANDS:
        raise ValueError("source freshness diff intake v8 packet must include approved offline validation commands")

    _reject_live_artifact_fields(packet)
    _reject_prohibited_claims(packet)


def _validate_processor_handoff_manifest(manifest: dict[str, Any]) -> None:
    if str(manifest.get("manifest_version", manifest.get("processor_handoff_manifest_version"))) != "8":
        raise ValueError("processor handoff manifest fixture must be version 8")
    _required_packet_ref(
        manifest,
        ("manifest_id", "processor_handoff_manifest_id"),
        "processor handoff manifest reference",
    )
    if manifest.get("dry_run") is not True:
        raise ValueError("processor handoff manifest v8 fixture must set dry_run to true")
    if not isinstance(manifest.get("sources", manifest.get("captures", [])), list):
        raise ValueError("processor handoff manifest v8 fixture must include sources or captures")
    _reject_live_artifact_fields(manifest)
    _reject_prohibited_claims(manifest)


def _validate_prior_source_registry(registry: dict[str, Any]) -> None:
    if str(registry.get("registry_version", registry.get("source_registry_version", "8"))) != "8":
        raise ValueError("prior source registry fixture must be version 8")
    _required_packet_ref(
        registry,
        ("registry_id", "source_registry_id"),
        "source registry reference",
    )
    if not isinstance(registry.get("sources", []), list):
        raise ValueError("prior source registry fixture must include sources")
    _reject_live_artifact_fields(registry)
    _reject_prohibited_claims(registry)


def _reject_live_artifact_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in _FORBIDDEN_ARTIFACT_KEYS and nested:
                raise ValueError(f"fixture contains forbidden live artifact field: {key}")
            _reject_live_artifact_fields(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_live_artifact_fields(item)


def _reject_prohibited_claims(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in _FALSE_REQUIRED_CLAIMS and nested not in (False, None, [], {}):
                raise ValueError(f"source freshness diff intake v8 rejects prohibited claim or active flag: {key}")
            _reject_prohibited_claims(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_prohibited_claims(item)


def _manifest_sources(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = manifest.get("sources", manifest.get("captures", []))
    return [_normalize_source_row(row) for row in rows if isinstance(row, dict)]


def _prior_sources(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [_normalize_source_row(row) for row in registry.get("sources", []) if isinstance(row, dict)]


def _normalize_source_row(row: dict[str, Any]) -> dict[str, Any]:
    source_id = _required_text(row, "source_id")
    canonical_url = _required_text(row, "canonical_url")
    normalized = dict(row)
    normalized["source_id"] = source_id
    normalized["canonical_url"] = canonical_url
    normalized["links"] = _normalize_links(row.get("links", row.get("observed_links", [])))
    normalized["citation_placeholders"] = _normalize_text_list(
        row.get("citation_placeholders", row.get("affected_citation_placeholders", []))
    )
    normalized["requirement_candidate_refs"] = _normalize_text_list(
        row.get(
            "requirement_candidate_refs",
            row.get("downstream_requirement_reextraction_candidate_refs", []),
        )
    )
    return normalized


def _required_packet_ref(
    packet: dict[str, Any],
    keys: tuple[str, ...],
    label: str,
) -> str:
    for key in keys:
        value = packet.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError(f"source freshness diff intake v8 packet missing {label}")


def _required_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"source row must include non-empty {key}")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _normalize_links(value: Any) -> list[dict[str, str | None]]:
    links: list[dict[str, str | None]] = []
    if not isinstance(value, list):
        return links
    for item in value:
        if isinstance(item, str):
            url = item.strip()
            if url:
                links.append({"url": url, "link_text": None})
        elif isinstance(item, dict):
            url = _optional_text(item.get("url") or item.get("href") or item.get("canonical_url"))
            if url:
                links.append({"url": url, "link_text": _optional_text(item.get("link_text"))})
    return sorted(links, key=lambda link: (link["url"] or "", link["link_text"] or ""))


def _normalize_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            ref = _optional_text(item.get("id") or item.get("ref") or item.get("requirement_id"))
            if ref:
                result.append(ref)
    return sorted(set(result))


def _changed_hash_row(
    current: dict[str, Any],
    prior: dict[str, Any] | None,
    status: str,
) -> dict[str, Any]:
    return {
        "source_id": current["source_id"],
        "canonical_url": current["canonical_url"],
        "freshness_status": status,
        "prior_content_hash": None if prior is None else prior.get("content_hash"),
        "dry_run_content_hash": current.get("content_hash"),
        "prior_last_seen_at": None if prior is None else prior.get("last_seen_at"),
        "dry_run_seen_at": current.get("capture_finished_at"),
    }


def _append_link_deltas(
    source_id: str,
    old_links: Any,
    new_links: Any,
    added_link_observations: list[dict[str, Any]],
    removed_link_observations: list[dict[str, Any]],
) -> None:
    old_by_url = {link["url"]: link for link in _normalize_links(old_links)}
    new_by_url = {link["url"]: link for link in _normalize_links(new_links)}

    for url in sorted(set(new_by_url) - set(old_by_url)):
        added_link_observations.append(
            {
                "source_id": source_id,
                "url": url,
                "link_text": new_by_url[url].get("link_text"),
                "observation_status": "added",
            }
        )
    for url in sorted(set(old_by_url) - set(new_by_url)):
        removed_link_observations.append(
            {
                "source_id": source_id,
                "url": url,
                "link_text": old_by_url[url].get("link_text"),
                "observation_status": "removed",
            }
        )


def _citation_rows(source: dict[str, Any], reason: str) -> list[dict[str, Any]]:
    placeholders = source.get("citation_placeholders", [])
    if not placeholders:
        placeholders = [f"citation-placeholder:{source['source_id']}"]
    return [
        {
            "source_id": source["source_id"],
            "canonical_url": source["canonical_url"],
            "citation_placeholder": placeholder,
            "impact_reason": reason,
        }
        for placeholder in placeholders
    ]


def _candidate_rows(source: dict[str, Any], reason: str) -> list[dict[str, Any]]:
    refs = source.get("requirement_candidate_refs", [])
    if not refs:
        refs = [f"requirement-candidate:{source['source_id']}"]
    return [
        {
            "source_id": source["source_id"],
            "canonical_url": source["canonical_url"],
            "candidate_ref": ref,
            "reason": reason,
        }
        for ref in refs
    ]


def _dedupe_dicts(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        key = json.dumps(row, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble PP&D source freshness diff intake v8 from fixtures only.")
    parser.add_argument("processor_handoff_manifest", type=Path)
    parser.add_argument("prior_source_registry", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            assemble_from_fixture_paths(args.processor_handoff_manifest, args.prior_source_registry),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
