"""Fixture-first public source refresh operator dry-run transcript helpers.

This module intentionally performs no network, processor, download, registry, or
schedule mutation work. It only combines already-captured candidate packets into
a deterministic operator transcript and validates that transcript before it can
be used as rehearsal evidence.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


DEFAULT_ALLOWED_HOSTS = (
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
)

_AUTH_URL_MARKERS = (
    "/login",
    "/sign-in",
    "/signin",
    "/register",
    "/account",
    "/dashboard",
    "/my-permits",
    "/mypermits",
    "/checkout",
    "/payment",
    "/oauth",
    "/auth",
)

_RAW_REFERENCE_KEYS = {
    "archive_artifact_ref",
    "archive_ref",
    "body_ref",
    "download_path",
    "download_ref",
    "downloaded_file_ref",
    "raw_body",
    "raw_body_path",
    "raw_body_ref",
    "warc_ref",
}

_RAW_REFERENCE_MARKERS = (
    "warc://",
    ".warc",
    "raw_body",
    "raw-body",
    "raw crawl",
    "raw_crawl",
    "raw-crawl",
    "downloaded_documents",
    "downloaded-documents",
    "/downloads/",
    "archive_artifact",
    "archive-artifact",
    "archive_artifacts",
    "archive-artifacts",
    "archive output",
)

_LIVE_TRUE_FIELDS = {
    "crawl_executed",
    "fetch_urls",
    "live_crawl_executed",
    "live_crawl_performed",
    "live_fetch_allowed",
    "network_io_allowed",
    "processor_executed",
    "processor_execution_allowed",
    "processor_invocation_allowed",
    "processor_invoked",
}

_MUTATION_TRUE_FIELDS = {
    "active_registry_mutation",
    "active_registry_mutation_allowed",
    "active_schedule_mutation",
    "active_schedule_mutation_allowed",
    "mutate_registries",
    "mutate_schedules",
    "registry_mutation_allowed",
    "schedule_mutation_allowed",
}

_LIVE_TEXT_MARKERS = (
    "live crawl executed",
    "live crawl performed",
    "live fetch",
    "network crawl executed",
    "processor executed",
    "processor invoked",
)

_LEGAL_GUARANTEE_MARKERS = (
    "guarantee permit approval",
    "guaranteed permit approval",
    "permit will be approved",
    "approval is guaranteed",
    "legally guaranteed",
    "legal outcome guaranteed",
    "permitting outcome guaranteed",
)

_URL_RE = re.compile(r"https?://[^\s\]})>'\"]+", re.IGNORECASE)


class PublicSourceRefreshOperatorDryRunValidationError(ValueError):
    """Raised when a public source refresh dry-run transcript is unsafe."""


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _evidence_refs(*packets: Mapping[str, Any], key: str) -> list[str]:
    refs: list[str] = []
    for packet in packets:
        for item in _list(packet.get(key)):
            if isinstance(item, str) and item not in refs:
                refs.append(item)
            elif isinstance(item, Mapping):
                ref = item.get("ref") or item.get("id") or item.get("url")
                if isinstance(ref, str) and ref not in refs:
                    refs.append(ref)
    return refs


def _source_ids(*packets: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for packet in packets:
        for key in ("source_id", "source_ids"):
            for item in _list(packet.get(key)):
                if isinstance(item, str) and item not in ids:
                    ids.append(item)
        for item in _list(packet.get("sources")):
            if isinstance(item, Mapping):
                source_id = item.get("source_id") or item.get("id")
                if isinstance(source_id, str) and source_id not in ids:
                    ids.append(source_id)
    return ids


def build_public_source_refresh_operator_dry_run_transcript(
    source_refresh_runbook_candidate: dict[str, Any],
    public_source_refresh_batch_packet: dict[str, Any],
    public_source_refresh_intake_evidence_packet: dict[str, Any],
    source_registry_schedule_update_candidate: dict[str, Any],
    *,
    reviewer: str,
    owner: str,
) -> dict[str, Any]:
    """Return an ordered simulated operator transcript from fixture packets."""

    sources = _source_ids(
        source_refresh_runbook_candidate,
        public_source_refresh_batch_packet,
        public_source_refresh_intake_evidence_packet,
        source_registry_schedule_update_candidate,
    )
    allowlist_refs = _evidence_refs(
        source_refresh_runbook_candidate,
        public_source_refresh_batch_packet,
        public_source_refresh_intake_evidence_packet,
        source_registry_schedule_update_candidate,
        key="allowlist_evidence_refs",
    )
    robots_refs = _evidence_refs(
        source_refresh_runbook_candidate,
        public_source_refresh_batch_packet,
        public_source_refresh_intake_evidence_packet,
        source_registry_schedule_update_candidate,
        key="robots_evidence_refs",
    )

    steps = [
        {
            "order": 1,
            "name": "load-runbook-candidate",
            "simulation_only": True,
            "inputs": ["source_refresh_runbook_candidate"],
            "expected_metadata_only_observation": "Runbook candidate identifier, scope, and declared operator gates are readable from fixture metadata.",
            "observation_citations": ["source_refresh_runbook_candidate"],
        },
        {
            "order": 2,
            "name": "load-public-source-refresh-batch",
            "simulation_only": True,
            "inputs": ["public_source_refresh_batch_packet"],
            "expected_metadata_only_observation": "Batch packet source identifiers and refresh intent are readable without fetching source URLs.",
            "observation_citations": ["public_source_refresh_batch_packet"],
        },
        {
            "order": 3,
            "name": "verify-intake-evidence",
            "simulation_only": True,
            "inputs": ["public_source_refresh_intake_evidence_packet"],
            "allowlist_evidence_refs": allowlist_refs,
            "robots_evidence_refs": robots_refs,
            "expected_metadata_only_observation": "Allowlist and robots references are present as fixture references only.",
            "observation_citations": ["public_source_refresh_intake_evidence_packet"],
        },
        {
            "order": 4,
            "name": "preview-schedule-update-candidate",
            "simulation_only": True,
            "inputs": ["source_registry_schedule_update_candidate"],
            "expected_metadata_only_observation": "Schedule update candidate can be reviewed without mutating registry schedules.",
            "observation_citations": ["source_registry_schedule_update_candidate"],
        },
        {
            "order": 5,
            "name": "record-reviewer-owner-attestation",
            "simulation_only": True,
            "reviewer": reviewer,
            "owner": owner,
            "expected_metadata_only_observation": "Reviewer and owner fields are attached to the dry-run transcript.",
            "observation_citations": ["operator_transcript_reviewer_owner_fields"],
        },
    ]

    transcript = {
        "packet_type": "public_source_refresh_operator_dry_run_transcript",
        "mode": "fixture_first_dry_run",
        "sources": sources,
        "reviewer": reviewer,
        "owner": owner,
        "ordered_simulated_operator_steps": steps,
        "allowlist_evidence_refs": allowlist_refs,
        "robots_evidence_refs": robots_refs,
        "abort_or_rollback_checkpoints": [
            {
                "checkpoint": "missing-allowlist-or-robots-reference",
                "operator_action": "abort before any live source interaction",
            },
            {
                "checkpoint": "unexpected-non-metadata-observation",
                "operator_action": "rollback transcript draft and require fixture repair",
            },
            {
                "checkpoint": "schedule-mutation-requested",
                "operator_action": "abort dry-run and return schedule candidate to review queue",
            },
        ],
        "attestations": {
            "no_fetch": True,
            "no_processor": True,
            "no_download": True,
            "no_schedule_mutation": True,
            "no_registry_mutation": True,
            "metadata_only_observations": True,
        },
    }
    errors = validate_public_source_refresh_operator_dry_run_transcript(transcript)
    if errors:
        raise PublicSourceRefreshOperatorDryRunValidationError("; ".join(errors))
    return transcript


def validate_public_source_refresh_operator_dry_run_transcript(
    packet: Mapping[str, Any],
    *,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> list[str]:
    """Return validation errors for unsafe or incomplete dry-run transcripts."""

    if not isinstance(packet, Mapping):
        return ["packet_not_mapping"]

    errors: list[str] = []
    errors.extend(_validate_ordered_steps(packet))
    errors.extend(_validate_required_evidence(packet))
    errors.extend(_validate_reviewer_owner(packet))
    errors.extend(_validate_checkpoints(packet))
    errors.extend(_validate_attestations(packet))
    errors.extend(_scan_forbidden_values(packet, allowed_hosts=allowed_hosts))
    return _dedupe(errors)


def assert_valid_public_source_refresh_operator_dry_run_transcript(packet: Mapping[str, Any]) -> None:
    """Raise when a dry-run transcript violates PP&D safety guardrails."""

    errors = validate_public_source_refresh_operator_dry_run_transcript(packet)
    if errors:
        raise PublicSourceRefreshOperatorDryRunValidationError("; ".join(errors))


def _validate_ordered_steps(packet: Mapping[str, Any]) -> list[str]:
    steps = packet.get("ordered_simulated_operator_steps")
    if not isinstance(steps, list) or not steps:
        return ["ordered_steps_missing"]

    errors: list[str] = []
    orders: list[int] = []
    for index, step in enumerate(steps):
        if not isinstance(step, Mapping):
            errors.append(f"ordered_steps[{index}]_not_mapping")
            continue
        order = step.get("order")
        if not isinstance(order, int):
            errors.append(f"ordered_steps[{index}].order_missing")
        else:
            orders.append(order)
        if step.get("simulation_only") is not True:
            errors.append(f"ordered_steps[{index}].simulation_only_not_true")
        if _text(step.get("expected_metadata_only_observation")):
            citations = step.get("observation_citations", step.get("citations"))
            if not _string_list(citations):
                errors.append(f"ordered_steps[{index}].metadata_observation_uncited")
    if orders != list(range(1, len(steps) + 1)):
        errors.append("ordered_steps_unordered")
    return errors


def _validate_required_evidence(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _string_list(packet.get("allowlist_evidence_refs")):
        errors.append("allowlist_evidence_refs_missing")
    if not _string_list(packet.get("robots_evidence_refs")):
        errors.append("robots_evidence_refs_missing")
    return errors


def _validate_reviewer_owner(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _text(packet.get("reviewer")):
        errors.append("reviewer_missing")
    if not _text(packet.get("owner")):
        errors.append("owner_missing")
    return errors


def _validate_checkpoints(packet: Mapping[str, Any]) -> list[str]:
    checkpoints = packet.get("abort_or_rollback_checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        return ["abort_or_rollback_checkpoints_missing"]

    rendered = " ".join(str(checkpoint).lower() for checkpoint in checkpoints)
    errors: list[str] = []
    if "abort" not in rendered:
        errors.append("abort_checkpoint_missing")
    if "rollback" not in rendered:
        errors.append("rollback_checkpoint_missing")
    return errors


def _validate_attestations(packet: Mapping[str, Any]) -> list[str]:
    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        return ["attestations_missing"]
    errors: list[str] = []
    required_true = (
        "no_fetch",
        "no_processor",
        "no_download",
        "no_schedule_mutation",
        "no_registry_mutation",
        "metadata_only_observations",
    )
    for key in required_true:
        if attestations.get(key) is not True:
            errors.append(f"attestations.{key}_missing")
    return errors


def _scan_forbidden_values(value: Any, *, allowed_hosts: Sequence[str], path: str = "$", key: str = "") -> list[str]:
    errors: list[str] = []
    normalized_key = key.lower()

    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            errors.extend(
                _scan_forbidden_values(
                    child_value,
                    allowed_hosts=allowed_hosts,
                    path=f"{path}.{child_key_text}",
                    key=child_key_text,
                )
            )
        return errors

    if isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_scan_forbidden_values(item, allowed_hosts=allowed_hosts, path=f"{path}[{index}]", key=key))
        return errors

    if value is True:
        if normalized_key in _LIVE_TRUE_FIELDS:
            errors.append(f"live_execution_claim:{path}")
        if normalized_key in _MUTATION_TRUE_FIELDS:
            errors.append(f"active_mutation_flag:{path}")
        return errors

    if isinstance(value, str):
        lowered = value.lower()
        if normalized_key in _RAW_REFERENCE_KEYS:
            errors.append(f"raw_reference_field:{path}")
        if any(marker in lowered for marker in _RAW_REFERENCE_MARKERS):
            errors.append(f"raw_reference_value:{path}")
        if any(marker in lowered for marker in _LIVE_TEXT_MARKERS):
            errors.append(f"live_execution_claim:{path}")
        if any(marker in lowered for marker in _LEGAL_GUARANTEE_MARKERS):
            errors.append(f"legal_or_permitting_outcome_guarantee:{path}")
        for url in _URL_RE.findall(value):
            errors.extend(_url_errors(url, allowed_hosts=allowed_hosts, path=path))
    return errors


def _url_errors(url: str, *, allowed_hosts: Sequence[str], path: str) -> list[str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    url_path = parsed.path.lower()
    errors: list[str] = []
    if parsed.scheme not in {"http", "https"}:
        errors.append(f"unsupported_url_scheme:{path}")
    if host not in set(allowed_hosts):
        errors.append(f"non_allowlisted_url:{path}")
    if any(marker in url_path for marker in _AUTH_URL_MARKERS):
        errors.append(f"authenticated_url:{path}")
    return errors


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _dedupe(errors: Sequence[str]) -> list[str]:
    deduped: list[str] = []
    for error in errors:
        if error not in deduped:
            deduped.append(error)
    return deduped
