"""Fixture-first PP&D public source freshness delta packet v1.

This module compares synthetic prior/current public source metadata rows. It is
metadata-only by design: no network access, raw downloads, processor execution,
DevHub access, official action, guarantees, or active state mutation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

PACKET_VERSION = "source_freshness_delta_packet_v1"

_ALLOWED_HOSTS = frozenset(
    {
        "devhub.portlandoregon.gov",
        "portland.gov",
        "www.portland.gov",
        "portlandmaps.com",
        "www.portlandmaps.com",
    }
)

_ALLOWED_VALIDATION_COMMANDS = (
    ("python3", "-m", "py_compile", "ppd/source_freshness_delta_packet_v1.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_source_freshness_delta_packet_v1.py"),
)

_DELTA_KINDS_REQUIRING_HOLD = frozenset(
    {
        "changed_hash",
        "visible_updated_date_changed",
        "missing_source_row",
        "new_official_link",
        "removed_official_link",
    }
)

_ALL_DELTA_KINDS = _DELTA_KINDS_REQUIRING_HOLD | {"new_source_row"}

_FORBIDDEN_KEYS = frozenset(
    {
        "active_archive_mutation",
        "active_contract_mutation",
        "active_daemon_state_mutation",
        "active_devhub_surface_mutation",
        "active_document_mutation",
        "active_guardrail_mutation",
        "active_mutation",
        "active_process_model_mutation",
        "active_prompt_mutation",
        "active_release_mutation",
        "active_requirement_mutation",
        "active_source_mutation",
        "auth_state",
        "browser_context",
        "browser_state",
        "cookie",
        "cookies",
        "download_path",
        "downloaded_artifact",
        "downloaded_body",
        "downloaded_document",
        "har_path",
        "html_body",
        "local_private_path",
        "raw_body",
        "raw_crawl_output",
        "raw_download",
        "screenshot_path",
        "session_file",
        "session_state",
        "storage_state",
        "trace_path",
    }
)

_FORBIDDEN_TEXT = (
    "active archive mutation",
    "active contract mutation",
    "active daemon-state mutation",
    "active devhub surface mutation",
    "active document mutation",
    "active guardrail mutation",
    "active process-model mutation",
    "active prompt mutation",
    "active release mutation",
    "active requirement mutation",
    "active source mutation",
    "all permits approved",
    "browser state",
    "certificate issued",
    "completed official action",
    "devhub claim verified live",
    "devhub login",
    "downloaded artifact",
    "downloaded body",
    "executed processor",
    "fee paid",
    "fetched live",
    "final approval",
    "guaranteed approval",
    "guaranteed compliant",
    "guaranteed legal",
    "har file",
    "inspection scheduled",
    "legal advice",
    "legal guarantee",
    "live crawl",
    "live devhub",
    "permit guaranteed",
    "permit issued",
    "permitting guarantee",
    "private file",
    "raw crawl",
    "raw download",
    "ran crawler",
    "ran processor",
    "session artifact",
    "submitted application",
    "trace file",
    "uploaded correction",
)

_AUTH_PATH_MARKERS = ("/login", "/signin", "/sign-in", "/oauth", "/saml", "/admin")
_AUTH_QUERY_MARKERS = ("token", "auth", "session", "key", "secret", "password", "cookie")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def build_source_freshness_delta_packet_v1(
    prior_rows: Iterable[Mapping[str, Any]],
    current_rows: Iterable[Mapping[str, Any]],
    *,
    packet_id: str = "fixture-source-freshness-delta-packet-v1",
    generated_at: str = "2026-05-31T00:00:00Z",
    reviewer_owner: str = "ppd-source-freshness-reviewer",
) -> dict[str, Any]:
    """Build a deterministic metadata-only source freshness delta packet."""

    prior_by_id = {_source_id(row): dict(row) for row in prior_rows}
    current_by_id = {_source_id(row): dict(row) for row in current_rows}
    source_ids = sorted(set(prior_by_id) | set(current_by_id))

    hash_comparisons: list[dict[str, Any]] = []
    visible_date_comparisons: list[dict[str, Any]] = []
    link_comparisons: list[dict[str, Any]] = []
    deltas: list[dict[str, Any]] = []

    for source_id in source_ids:
        prior = prior_by_id.get(source_id)
        current = current_by_id.get(source_id)
        if prior is None:
            deltas.append(_new_source_delta(source_id, current))
            continue
        if current is None:
            deltas.append(_missing_source_delta(source_id, prior))
            continue
        hash_comparisons.append(_hash_comparison(source_id, prior, current))
        visible_date_comparisons.append(_visible_date_comparison(source_id, prior, current))
        link_comparison, link_deltas = _link_comparison(source_id, prior, current)
        link_comparisons.append(link_comparison)
        deltas.extend(_comparison_deltas(source_id, current, hash_comparisons[-1], visible_date_comparisons[-1], link_deltas))

    hold_source_ids = sorted({delta["source_id"] for delta in deltas if delta["delta_kind"] in _DELTA_KINDS_REQUIRING_HOLD})
    packet = {
        "packet_version": PACKET_VERSION,
        "packet_id": packet_id,
        "generated_at": generated_at,
        "metadata_only": True,
        "fixture_first": True,
        "network_access_performed": False,
        "raw_downloads_performed": False,
        "processor_execution_performed": False,
        "devhub_access_performed": False,
        "official_action_completed": False,
        "active_mutation_performed": False,
        "comparison_scope": {
            "prior_source_count": len(prior_by_id),
            "current_source_count": len(current_by_id),
            "delta_count": len(deltas),
            "compared_fields": ["content_hash", "visible_updated_date", "official_links", "source_row_presence"],
        },
        "source_row_sets": {
            "prior_source_rows": [_source_row_summary(row) for row in prior_by_id.values()],
            "current_source_rows": [_source_row_summary(row) for row in current_by_id.values()],
        },
        "hash_comparisons": hash_comparisons,
        "visible_date_comparisons": visible_date_comparisons,
        "link_comparisons": link_comparisons,
        "source_deltas": deltas,
        "reviewer_hold_recommendations": [
            {
                "source_id": source_id,
                "reviewer_owner": reviewer_owner,
                "hold_recommended": True,
                "hold_reason": "fixture_metadata_delta_requires_human_freshness_review",
                "allowed_next_step": "offline_reviewer_compare_public_metadata_fixture_only",
                "disallowed_next_steps": [
                    "live_crawl",
                    "raw_download",
                    "processor_execution",
                    "devhub_access",
                    "official_action",
                    "active_source_mutation",
                    "active_requirement_mutation",
                    "active_process_model_mutation",
                    "active_guardrail_mutation",
                ],
            }
            for source_id in hold_source_ids
        ],
        "offline_validation_commands": [list(command) for command in _ALLOWED_VALIDATION_COMMANDS],
    }
    require_valid_source_freshness_delta_packet_v1(packet)
    return packet


def build_source_freshness_delta_packet_v1_from_fixture(path: Path | str) -> dict[str, Any]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    return build_source_freshness_delta_packet_v1(
        fixture["prior_source_metadata_rows"],
        fixture["current_source_metadata_rows"],
        packet_id=fixture.get("packet_id", "fixture-source-freshness-delta-packet-v1"),
        generated_at=fixture.get("generated_at", "2026-05-31T00:00:00Z"),
        reviewer_owner=fixture.get("reviewer_owner", "ppd-source-freshness-reviewer"),
    )


def validate_source_freshness_delta_packet_v1(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(packet, Mapping):
        return [ValidationIssue("packet_type", "packet must be an object")]

    if packet.get("packet_version") != PACKET_VERSION:
        issues.append(ValidationIssue("packet_version", f"packet_version must be {PACKET_VERSION}"))
    if not str(packet.get("packet_id", "")).strip():
        issues.append(ValidationIssue("packet_id", "packet_id is required"))
    if not str(packet.get("generated_at", "")).endswith("Z"):
        issues.append(ValidationIssue("generated_at", "generated_at must be a UTC timestamp ending in Z"))

    for flag in ("metadata_only", "fixture_first"):
        if packet.get(flag) is not True:
            issues.append(ValidationIssue(flag, f"{flag} must be true"))
    for flag in (
        "network_access_performed",
        "raw_downloads_performed",
        "processor_execution_performed",
        "devhub_access_performed",
        "official_action_completed",
        "active_mutation_performed",
    ):
        if packet.get(flag) is not False:
            issues.append(ValidationIssue(flag, f"{flag} must be false"))

    prior_ids, current_ids = _validate_source_row_sets(packet, issues)
    shared_ids = sorted(prior_ids & current_ids)
    _validate_comparison_scope(packet, issues)
    _validate_comparisons(packet, shared_ids, issues)

    deltas = packet.get("source_deltas")
    if not isinstance(deltas, list) or not deltas:
        issues.append(ValidationIssue("source_deltas", "source_deltas must be a non-empty list"))
    else:
        issues.extend(_validate_deltas(deltas))
        issues.extend(_validate_required_delta_kinds(deltas))

    holds = packet.get("reviewer_hold_recommendations")
    if not isinstance(holds, list) or not holds:
        issues.append(ValidationIssue("reviewer_hold_recommendations", "reviewer hold recommendations are required"))
    else:
        issues.extend(_validate_holds(holds, deltas if isinstance(deltas, list) else []))

    issues.extend(_validate_validation_commands(packet))
    issues.extend(_validate_urls_and_forbidden_content(packet))
    return issues


def require_valid_source_freshness_delta_packet_v1(packet: Mapping[str, Any]) -> None:
    issues = validate_source_freshness_delta_packet_v1(packet)
    if issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def _hash_comparison(source_id: str, prior: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "prior_content_hash": str(prior.get("content_hash", "")).strip(),
        "current_content_hash": str(current.get("content_hash", "")).strip(),
        "changed": str(prior.get("content_hash", "")).strip() != str(current.get("content_hash", "")).strip(),
        "metadata_only": True,
    }


def _visible_date_comparison(source_id: str, prior: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "prior_visible_updated_date": str(prior.get("visible_updated_date", "")).strip(),
        "current_visible_updated_date": str(current.get("visible_updated_date", "")).strip(),
        "changed": str(prior.get("visible_updated_date", "")).strip() != str(current.get("visible_updated_date", "")).strip(),
        "metadata_only": True,
    }


def _link_comparison(source_id: str, prior: Mapping[str, Any], current: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prior_links = set(_official_links(prior))
    current_links = set(_official_links(current))
    added = sorted(current_links - prior_links)
    removed = sorted(prior_links - current_links)
    comparison = {
        "source_id": source_id,
        "added_official_links": added,
        "removed_official_links": removed,
        "metadata_only": True,
    }
    deltas: list[dict[str, Any]] = []
    for link in added:
        deltas.append(_base_delta(source_id, current, "new_official_link", "current metadata row contains a new official public link", previous_value=None, current_value=link))
    for link in removed:
        deltas.append(_base_delta(source_id, current, "removed_official_link", "current metadata row no longer contains an official public link from the prior row", previous_value=link, current_value=None))
    return comparison, deltas


def _comparison_deltas(source_id: str, current: Mapping[str, Any], hash_row: Mapping[str, Any], date_row: Mapping[str, Any], link_deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    if hash_row.get("changed"):
        deltas.append(_base_delta(source_id, current, "changed_hash", "content_hash changed between synthetic prior and current metadata rows", previous_value=str(hash_row["prior_content_hash"]), current_value=str(hash_row["current_content_hash"])))
    if date_row.get("changed"):
        deltas.append(_base_delta(source_id, current, "visible_updated_date_changed", "visible updated date changed between synthetic prior and current metadata rows", previous_value=str(date_row["prior_visible_updated_date"]), current_value=str(date_row["current_visible_updated_date"])))
    deltas.extend(link_deltas)
    return deltas


def _new_source_delta(source_id: str, current: Mapping[str, Any] | None) -> dict[str, Any]:
    return _base_delta(source_id, current or {"canonical_url": ""}, "new_source_row", "current metadata fixture contains a source row absent from the prior fixture", previous_value=None, current_value=source_id)


def _missing_source_delta(source_id: str, prior: Mapping[str, Any]) -> dict[str, Any]:
    return _base_delta(source_id, prior, "missing_source_row", "current metadata fixture is missing a source row present in the prior fixture", previous_value=source_id, current_value=None)


def _base_delta(source_id: str, row: Mapping[str, Any], delta_kind: str, description: str, *, previous_value: str | None, current_value: str | None) -> dict[str, Any]:
    hold_recommended = delta_kind in _DELTA_KINDS_REQUIRING_HOLD
    return {
        "delta_id": f"delta::{source_id}::{delta_kind}::{_stable_value(previous_value, current_value)}",
        "source_id": source_id,
        "canonical_url": str(row.get("canonical_url", "")),
        "delta_kind": delta_kind,
        "description": description,
        "previous_value": previous_value,
        "current_value": current_value,
        "metadata_only": True,
        "public_official_source": True,
        "reviewer_hold_recommended": hold_recommended,
        "reviewer_hold_reason": "fixture_metadata_delta_requires_human_freshness_review" if hold_recommended else "new_source_row_requires_source_registry_review_before_promotion",
    }


def _validate_source_row_sets(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> tuple[set[str], set[str]]:
    row_sets = packet.get("source_row_sets")
    if not isinstance(row_sets, Mapping):
        issues.append(ValidationIssue("source_row_sets", "source_row_sets with prior and current source rows is required"))
        return set(), set()
    prior = row_sets.get("prior_source_rows")
    current = row_sets.get("current_source_rows")
    prior_ids = _validate_source_rows(prior, "source_row_sets.prior_source_rows", issues)
    current_ids = _validate_source_rows(current, "source_row_sets.current_source_rows", issues)
    if not prior_ids:
        issues.append(ValidationIssue("prior_source_rows", "prior source rows are required"))
    if not current_ids:
        issues.append(ValidationIssue("current_source_rows", "current source rows are required"))
    return prior_ids, current_ids


def _validate_source_rows(rows: Any, path: str, issues: list[ValidationIssue]) -> set[str]:
    if not isinstance(rows, list):
        issues.append(ValidationIssue("source_rows", f"{path} must be a list"))
        return set()
    ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            issues.append(ValidationIssue("source_row_type", f"{path}[{index}] must be an object"))
            continue
        source_id = str(row.get("source_id", "")).strip()
        if not source_id:
            issues.append(ValidationIssue("source_id", f"{path}[{index}].source_id is required"))
        else:
            ids.add(source_id)
        for field in ("canonical_url", "content_hash", "visible_updated_date"):
            if not str(row.get(field, "")).strip():
                issues.append(ValidationIssue(field, f"{path}[{index}].{field} is required"))
        if not isinstance(row.get("official_links"), list):
            issues.append(ValidationIssue("official_links", f"{path}[{index}].official_links must be a list"))
    return ids


def _validate_comparison_scope(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    scope = packet.get("comparison_scope")
    if not isinstance(scope, Mapping):
        issues.append(ValidationIssue("comparison_scope", "comparison_scope is required"))
        return
    compared = set(scope.get("compared_fields") if isinstance(scope.get("compared_fields"), list) else [])
    for field in ("content_hash", "visible_updated_date", "official_links", "source_row_presence"):
        if field not in compared:
            issues.append(ValidationIssue("compared_fields", f"comparison_scope.compared_fields must include {field}"))


def _validate_comparisons(packet: Mapping[str, Any], shared_ids: list[str], issues: list[ValidationIssue]) -> None:
    _validate_comparison_rows(packet.get("hash_comparisons"), "hash_comparisons", shared_ids, ("prior_content_hash", "current_content_hash"), issues)
    _validate_comparison_rows(packet.get("visible_date_comparisons"), "visible_date_comparisons", shared_ids, ("prior_visible_updated_date", "current_visible_updated_date"), issues)
    link_rows = packet.get("link_comparisons")
    if not isinstance(link_rows, list):
        issues.append(ValidationIssue("link_comparisons", "link_comparisons rows are required"))
        return
    link_ids = {str(row.get("source_id", "")) for row in link_rows if isinstance(row, Mapping)}
    if link_ids != set(shared_ids):
        issues.append(ValidationIssue("link_comparison_source_ids", "link comparisons must exactly cover shared prior/current source rows"))
    has_added = False
    has_removed = False
    for index, row in enumerate(link_rows):
        if not isinstance(row, Mapping):
            issues.append(ValidationIssue("link_comparison_type", f"link_comparisons[{index}] must be an object"))
            continue
        added = row.get("added_official_links")
        removed = row.get("removed_official_links")
        if not isinstance(added, list) or not isinstance(removed, list):
            issues.append(ValidationIssue("link_comparison_rows", f"link_comparisons[{index}] must include added and removed link rows"))
        has_added = has_added or bool(added)
        has_removed = has_removed or bool(removed)
    if not has_added:
        issues.append(ValidationIssue("added_link_rows", "at least one added official link row is required"))
    if not has_removed:
        issues.append(ValidationIssue("removed_link_rows", "at least one removed official link row is required"))


def _validate_comparison_rows(rows: Any, code: str, shared_ids: list[str], required_fields: tuple[str, str], issues: list[ValidationIssue]) -> None:
    if not isinstance(rows, list):
        issues.append(ValidationIssue(code, f"{code} rows are required"))
        return
    row_ids = {str(row.get("source_id", "")) for row in rows if isinstance(row, Mapping)}
    if row_ids != set(shared_ids):
        issues.append(ValidationIssue(f"{code}_source_ids", f"{code} must exactly cover shared prior/current source rows"))
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            issues.append(ValidationIssue(f"{code}_type", f"{code}[{index}] must be an object"))
            continue
        if row.get("metadata_only") is not True:
            issues.append(ValidationIssue("metadata_only", f"{code}[{index}].metadata_only must be true"))
        for field in required_fields:
            if not str(row.get(field, "")).strip():
                issues.append(ValidationIssue(code, f"{code}[{index}].{field} is required"))


def _validate_deltas(deltas: list[Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, delta in enumerate(deltas):
        prefix = f"source_deltas[{index}]"
        if not isinstance(delta, Mapping):
            issues.append(ValidationIssue("delta_type", f"{prefix} must be an object"))
            continue
        delta_id = str(delta.get("delta_id", "")).strip()
        if not delta_id:
            issues.append(ValidationIssue("delta_id", f"{prefix}.delta_id is required"))
        elif delta_id in seen:
            issues.append(ValidationIssue("delta_id_duplicate", f"duplicate delta_id {delta_id}"))
        seen.add(delta_id)
        if not str(delta.get("source_id", "")).strip():
            issues.append(ValidationIssue("source_id", f"{prefix}.source_id is required"))
        if str(delta.get("delta_kind", "")) not in _ALL_DELTA_KINDS:
            issues.append(ValidationIssue("delta_kind", f"{prefix}.delta_kind is unsupported"))
        if delta.get("metadata_only") is not True:
            issues.append(ValidationIssue("metadata_only", f"{prefix}.metadata_only must be true"))
        if delta.get("public_official_source") is not True:
            issues.append(ValidationIssue("public_official_source", f"{prefix}.public_official_source must be true"))
    return issues


def _validate_required_delta_kinds(deltas: list[Any]) -> list[ValidationIssue]:
    kinds = {str(delta.get("delta_kind", "")) for delta in deltas if isinstance(delta, Mapping)}
    required = {"changed_hash", "visible_updated_date_changed", "missing_source_row", "new_official_link", "removed_official_link"}
    return [ValidationIssue("required_delta_kind", f"source_deltas must include {kind}") for kind in sorted(required - kinds)]


def _validate_holds(holds: list[Any], deltas: list[Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_hold_sources = sorted({str(delta.get("source_id", "")) for delta in deltas if isinstance(delta, Mapping) and delta.get("delta_kind") in _DELTA_KINDS_REQUIRING_HOLD})
    hold_sources = sorted(str(hold.get("source_id", "")) for hold in holds if isinstance(hold, Mapping))
    if hold_sources != required_hold_sources:
        issues.append(ValidationIssue("reviewer_hold_source_ids", "reviewer holds must exactly match hold-requiring source deltas"))
    for index, hold in enumerate(holds):
        prefix = f"reviewer_hold_recommendations[{index}]"
        if not isinstance(hold, Mapping):
            issues.append(ValidationIssue("reviewer_hold_type", f"{prefix} must be an object"))
            continue
        if hold.get("hold_recommended") is not True:
            issues.append(ValidationIssue("reviewer_hold", f"{prefix}.hold_recommended must be true"))
        if not str(hold.get("reviewer_owner", "")).strip():
            issues.append(ValidationIssue("reviewer_owner", f"{prefix}.reviewer_owner is required"))
        if str(hold.get("allowed_next_step", "")) != "offline_reviewer_compare_public_metadata_fixture_only":
            issues.append(ValidationIssue("allowed_next_step", f"{prefix}.allowed_next_step must stay offline and fixture-only"))
    return issues


def _validate_validation_commands(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    commands = packet.get("offline_validation_commands")
    if not isinstance(commands, list) or not commands:
        return [ValidationIssue("offline_validation_commands", "offline validation commands are required")]
    normalized = {tuple(str(part) for part in command) for command in commands if isinstance(command, list)}
    missing = [command for command in _ALLOWED_VALIDATION_COMMANDS if command not in normalized]
    if missing:
        return [ValidationIssue("offline_validation_commands", "offline validation commands must include py_compile and focused pytest commands")]
    return []


def _validate_urls_and_forbidden_content(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].replace("-", "_").lower()
        if key in _FORBIDDEN_KEYS:
            issues.append(ValidationIssue("forbidden_key", f"{path} is not allowed in a fixture metadata packet"))
        if isinstance(value, bool) and key.startswith("active_") and value:
            issues.append(ValidationIssue("active_mutation_flag", f"{path} must not be true"))
        if isinstance(value, str):
            lowered = value.lower()
            if any(marker in lowered for marker in _FORBIDDEN_TEXT):
                issues.append(ValidationIssue("forbidden_text", f"{path} contains forbidden execution, guarantee, official-action, or mutation language"))
            if _looks_like_url(value):
                issues.extend(_validate_url(path, value))
    return issues


def _validate_url(path: str, value: str) -> list[ValidationIssue]:
    parsed = urlparse(value)
    host = parsed.netloc.lower().split("@")[-1]
    issues: list[ValidationIssue] = []
    if parsed.scheme != "https":
        issues.append(ValidationIssue("url_scheme", f"{path} must use https"))
    if parsed.username or parsed.password or "@" in parsed.netloc:
        issues.append(ValidationIssue("authenticated_url", f"{path} must not contain URL credentials"))
    if host not in _ALLOWED_HOSTS:
        issues.append(ValidationIssue("url_host", f"{path} host is not allowlisted: {host}"))
    if any(marker in parsed.path.lower() for marker in _AUTH_PATH_MARKERS):
        issues.append(ValidationIssue("authenticated_url", f"{path} must not reference authenticated paths"))
    if any(marker in parsed.query.lower() for marker in _AUTH_QUERY_MARKERS):
        issues.append(ValidationIssue("authenticated_url", f"{path} must not include auth-like query parameters"))
    return issues


def _source_row_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": _source_id(row),
        "canonical_url": str(row.get("canonical_url", "")).strip(),
        "content_hash": str(row.get("content_hash", "")).strip(),
        "visible_updated_date": str(row.get("visible_updated_date", "")).strip(),
        "official_links": list(_official_links(row)),
        "metadata_only": True,
    }


def _source_id(row: Mapping[str, Any]) -> str:
    source_id = str(row.get("source_id", "")).strip()
    if not source_id:
        raise ValueError("source metadata row requires source_id")
    return source_id


def _official_links(row: Mapping[str, Any]) -> tuple[str, ...]:
    links = row.get("official_links", [])
    if not isinstance(links, list):
        return ()
    return tuple(sorted(str(link).strip() for link in links if isinstance(link, str) and str(link).strip()))


def _stable_value(previous_value: str | None, current_value: str | None) -> str:
    value = current_value if current_value is not None else previous_value
    return str(value or "none").replace("https://", "").replace("/", "-").replace(":", "-")[:96]


def _walk(value: Any, path: str = "packet") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _looks_like_url(value: str) -> bool:
    return value.lower().startswith("http://") or value.lower().startswith("https://")
