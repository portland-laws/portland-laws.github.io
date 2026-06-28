"""Fixture-first public source refresh dry-run acceptance checklist packet.

The builder in this module consumes already-committed fixture packets only. It
creates an acceptance checklist for a public source refresh dry run without
fetching URLs, downloading documents, invoking processors, mutating registries,
or changing source schedules.
"""

from __future__ import annotations

import shlex
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

REQUIRED_ATTESTATIONS = (
    "no_fetch",
    "no_download",
    "no_processor",
    "no_registry_mutation",
    "no_schedule_mutation",
)

RAW_REFERENCE_KEYS = {
    "archive_artifact_ref",
    "archive_ref",
    "artifact_ref",
    "artifact_uri",
    "download_path",
    "download_ref",
    "raw_artifact_ref",
    "raw_body",
    "raw_body_path",
    "raw_body_ref",
    "warc_ref",
}

RAW_REFERENCE_MARKERS = (
    "archive-artifacts/",
    "downloaded-documents/",
    "raw-artifacts/",
    "raw_body",
    "raw-body",
    "warc://",
    ".warc",
)

UNSAFE_TRUE_FLAGS = {
    "download_allowed",
    "fetch_allowed",
    "live_fetch_allowed",
    "mutate_registry",
    "mutate_schedule",
    "network_io_allowed",
    "processor_executed",
    "processor_invocation_allowed",
    "registry_mutation_allowed",
    "schedule_mutation_allowed",
}

ACTIVE_MUTATION_KEYS = {
    "apply_registry_update",
    "apply_schedule_update",
    "registry_mutation",
    "registry_mutation_flag",
    "registry_update_enabled",
    "schedule_mutation",
    "schedule_mutation_flag",
    "schedule_update_enabled",
}

ACTIVE_MUTATION_VALUES = {
    "active",
    "apply",
    "enabled",
    "execute",
    "live",
    "mutate",
    "mutating",
    "true",
    "update",
}

COMMAND_KEYS = {
    "command",
    "command_string",
    "dry_run_command",
    "operator_command",
    "proposed_command",
    "shell_command",
}

LIVE_COMMAND_TOKENS = {
    "aria2c",
    "curl",
    "fetch",
    "ftp",
    "http",
    "https",
    "playwright",
    "requests.get",
    "scrapy",
    "wget",
}

DOWNLOAD_COMMAND_TOKENS = {
    "--output",
    "--remote-name",
    "-O",
    "download",
    "download_file",
    "save_as",
}

AUTHENTICATED_URL_MARKERS = (
    "/account",
    "/auth",
    "/checkout",
    "/dashboard",
    "/login",
    "/my-permits",
    "/oauth",
    "/payment",
    "/register",
    "/sign-in",
    "/signin",
)

UNSAFE_LIVE_TEXT_MARKERS = (
    "downloaded document",
    "live fetch",
    "network crawl",
    "processor executed",
    "processor invoked",
    "registry was updated",
    "schedule was updated",
)

LEGAL_OR_PERMITTING_GUARANTEE_MARKERS = (
    "approved permit outcome",
    "guaranteed permit approval",
    "guarantees approval",
    "guarantees issuance",
    "legal approval guaranteed",
    "permit approval is guaranteed",
    "permit is guaranteed",
    "permit will be approved",
    "will be legally accepted",
    "will pass plan review",
)


class PublicSourceRefreshDryRunAcceptanceChecklistError(ValueError):
    """Raised when an acceptance checklist packet is incomplete or unsafe."""


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _collect_refs(packet: Mapping[str, Any], *keys: str) -> list[str]:
    refs: list[str] = []
    for key in keys:
        for item in _items(packet.get(key)):
            ref = ""
            if isinstance(item, str):
                ref = item
            elif isinstance(item, Mapping):
                ref = _text(item.get("ref") or item.get("id") or item.get("url"))
            if ref and ref not in refs:
                refs.append(ref)
    return refs


def _source_entries(proposal: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_sources = proposal.get("ordered_sources") or proposal.get("source_entries") or proposal.get("sources")
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(_items(raw_sources), start=1):
        if not isinstance(item, Mapping):
            continue
        source_id = _text(item.get("source_id") or item.get("id"))
        canonical_url = _text(item.get("canonical_url") or item.get("url"))
        abort_checks = [str(check) for check in _items(item.get("abort_criteria") or item.get("abort_checks")) if str(check).strip()]
        allowlist_refs = _collect_refs(item, "allowlist_evidence_refs", "allowlist_refs")
        robots_refs = _collect_refs(item, "robots_evidence_refs", "robots_refs")
        entries.append(
            {
                "order": int(item.get("order") or index),
                "source_id": source_id,
                "canonical_url": canonical_url,
                "allowlist_evidence_refs": allowlist_refs,
                "robots_evidence_refs": robots_refs,
                "abort_checks": abort_checks,
            }
        )
    return entries


def _owner_fields(*packets: Mapping[str, Any]) -> dict[str, str]:
    for packet in packets:
        fields = packet.get("reviewer_owner_fields") or packet.get("reviewer_owner")
        if isinstance(fields, Mapping):
            reviewer = _text(fields.get("reviewer"))
            owner = _text(fields.get("owner"))
            if reviewer and owner:
                return {"reviewer": reviewer, "owner": owner}
        reviewer = _text(packet.get("reviewer"))
        owner = _text(packet.get("owner"))
        if reviewer and owner:
            return {"reviewer": reviewer, "owner": owner}
    return {"reviewer": "", "owner": ""}


def _attestation_value(packet: Mapping[str, Any], key: str) -> bool:
    attestations = packet.get("attestations")
    if isinstance(attestations, Mapping) and attestations.get(key) is True:
        return True
    return packet.get(key) is True


def build_public_source_refresh_dry_run_acceptance_checklist_packet(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Build a metadata-only acceptance checklist from fixture input packets."""

    proposal = inputs.get("public_source_refresh_tranche_proposal_packet")
    runbook = inputs.get("source_refresh_runbook_candidate")
    transcript = inputs.get("public_source_refresh_operator_dry_run_transcript")
    if not isinstance(proposal, Mapping) or not isinstance(runbook, Mapping) or not isinstance(transcript, Mapping):
        raise PublicSourceRefreshDryRunAcceptanceChecklistError("missing_required_input_packet")

    sources = _source_entries(proposal)
    reviewer_owner = _owner_fields(inputs, proposal, runbook, transcript)
    runbook_gates = [str(gate) for gate in _items(runbook.get("preflight_gates") or runbook.get("operator_gates")) if str(gate).strip()]
    transcript_steps = [step for step in _items(transcript.get("steps")) if isinstance(step, Mapping)]

    preflight_gates = [
        {
            "order": 1,
            "gate_id": "consume-refresh-tranche-proposal",
            "input_packet": "public_source_refresh_tranche_proposal_packet",
            "expected_metadata_only_output": "Refresh source order, allowlist evidence, robots evidence, and proposed abort criteria are visible from fixture metadata.",
            "evidence_refs": _collect_refs(proposal, "evidence_refs", "allowlist_evidence_refs", "robots_evidence_refs") or ["fixture://public-source-refresh-tranche-proposal"],
        },
        {
            "order": 2,
            "gate_id": "consume-runbook-candidate",
            "input_packet": "source_refresh_runbook_candidate",
            "expected_metadata_only_output": "Runbook preflight gates and operator stop points are readable without invoking a crawler or processor.",
            "evidence_refs": _collect_refs(runbook, "evidence_refs", "runbook_step_refs") or ["fixture://source-refresh-runbook-candidate"],
            "runbook_gate_names": runbook_gates,
        },
        {
            "order": 3,
            "gate_id": "consume-operator-dry-run-transcript",
            "input_packet": "public_source_refresh_operator_dry_run_transcript",
            "expected_metadata_only_output": "Operator dry-run transcript steps are ordered and simulation-only.",
            "evidence_refs": _collect_refs(transcript, "evidence_refs", "observation_citations") or ["fixture://public-source-refresh-operator-dry-run-transcript"],
            "transcript_step_count": len(transcript_steps),
        },
        {
            "order": 4,
            "gate_id": "reviewer-owner-acceptance",
            "input_packet": "acceptance_checklist_builder",
            "expected_metadata_only_output": "Reviewer and owner fields are attached before any refresh tranche can leave dry-run review.",
            "evidence_refs": ["fixture://reviewer-owner-fields"],
        },
    ]

    per_source_abort_checks = []
    for source in sources:
        per_source_abort_checks.append(
            {
                "order": source["order"],
                "source_id": source["source_id"],
                "canonical_url": source["canonical_url"],
                "abort_checks": source["abort_checks"],
                "allowlist_evidence_refs": source["allowlist_evidence_refs"],
                "robots_evidence_refs": source["robots_evidence_refs"],
                "expected_metadata_only_output": "Accept or abort decision remains a fixture-only metadata review; no source URL is fetched.",
            }
        )

    packet = {
        "packet_type": "ppd_public_source_refresh_dry_run_acceptance_checklist",
        "mode": "fixture_first_metadata_only_acceptance",
        "generated_from": [
            "public_source_refresh_tranche_proposal_packet",
            "source_refresh_runbook_candidate",
            "public_source_refresh_operator_dry_run_transcript",
        ],
        "preflight_gates": preflight_gates,
        "per_source_abort_checks": per_source_abort_checks,
        "expected_metadata_only_outputs": [gate["expected_metadata_only_output"] for gate in preflight_gates]
        + [check["expected_metadata_only_output"] for check in per_source_abort_checks],
        "reviewer_owner_fields": reviewer_owner,
        "attestations": {
            "no_fetch": True,
            "no_download": True,
            "no_processor": True,
            "no_registry_mutation": True,
            "no_schedule_mutation": True,
        },
    }
    require_public_source_refresh_dry_run_acceptance_checklist_packet(packet)
    return packet


def validate_public_source_refresh_dry_run_acceptance_checklist_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return validation issue codes for a dry-run acceptance checklist packet."""

    issues: list[str] = []
    if packet.get("packet_type") != "ppd_public_source_refresh_dry_run_acceptance_checklist":
        issues.append("invalid_packet_type")
    if packet.get("mode") != "fixture_first_metadata_only_acceptance":
        issues.append("invalid_mode")

    gates = [gate for gate in _items(packet.get("preflight_gates")) if isinstance(gate, Mapping)]
    if not gates:
        issues.append("missing_preflight_gates")
    gate_orders = [gate.get("order") for gate in gates]
    if gate_orders != list(range(1, len(gates) + 1)):
        issues.append("unordered_preflight_gates")
    for gate in gates:
        if not _text(gate.get("gate_id")):
            issues.append("missing_gate_id")
        if not _text(gate.get("expected_metadata_only_output")):
            issues.append("missing_gate_metadata_output")
        if not _items(gate.get("evidence_refs")):
            issues.append("uncited_preflight_gate")

    abort_checks = [check for check in _items(packet.get("per_source_abort_checks")) if isinstance(check, Mapping)]
    if not abort_checks:
        issues.append("missing_per_source_abort_checks")
    abort_orders = [check.get("order") for check in abort_checks]
    if abort_orders != list(range(1, len(abort_checks) + 1)):
        issues.append("unordered_per_source_abort_checks")
    for check in abort_checks:
        if not _text(check.get("source_id")):
            issues.append("missing_abort_source_id")
        if not _text(check.get("canonical_url")):
            issues.append("missing_abort_canonical_url")
        if not _items(check.get("abort_checks")):
            issues.append("missing_abort_checks")
        if not _items(check.get("allowlist_evidence_refs")):
            issues.append("missing_allowlist_evidence")
        if not _items(check.get("robots_evidence_refs")):
            issues.append("missing_robots_evidence")
        if not _text(check.get("expected_metadata_only_output")):
            issues.append("missing_abort_metadata_output")

    outputs = [output for output in _items(packet.get("expected_metadata_only_outputs")) if _text(output)]
    if not outputs:
        issues.append("missing_expected_metadata_only_outputs")

    owners = packet.get("reviewer_owner_fields")
    if not isinstance(owners, Mapping) or not _text(owners.get("reviewer")) or not _text(owners.get("owner")):
        issues.append("missing_reviewer_owner_fields")

    for key in REQUIRED_ATTESTATIONS:
        if not _attestation_value(packet, key):
            issues.append(f"missing_{key}_attestation")

    _append_unsafe_content_issues(packet, issues)
    return sorted(set(issues))


def require_public_source_refresh_dry_run_acceptance_checklist_packet(packet: Mapping[str, Any]) -> None:
    """Raise if the packet is not acceptable as fixture-first dry-run evidence."""

    issues = validate_public_source_refresh_dry_run_acceptance_checklist_packet(packet)
    if issues:
        raise PublicSourceRefreshDryRunAcceptanceChecklistError(",".join(issues))


def _append_unsafe_content_issues(value: Any, issues: list[str], parent_key: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in RAW_REFERENCE_KEYS and item:
                issues.append("raw_body_download_or_archive_reference")
            if key_text in UNSAFE_TRUE_FLAGS and item is True:
                issues.append("unsafe_live_or_mutation_flag")
            if key_text in ACTIVE_MUTATION_KEYS and _is_active_mutation_value(item):
                issues.append("active_registry_or_schedule_mutation_flag")
            if key_text in COMMAND_KEYS and isinstance(item, str) and _command_requests_live_fetch_or_download(item):
                issues.append("command_string_performs_live_fetch_or_download")
            _append_unsafe_content_issues(item, issues, key_text)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _append_unsafe_content_issues(item, issues, parent_key)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if parent_key in COMMAND_KEYS and _command_requests_live_fetch_or_download(value):
            issues.append("command_string_performs_live_fetch_or_download")
        if any(marker in lowered for marker in RAW_REFERENCE_MARKERS):
            issues.append("raw_body_download_or_archive_reference")
        if any(marker in lowered for marker in UNSAFE_LIVE_TEXT_MARKERS):
            issues.append("unsafe_live_mutation_or_guarantee_claim")
        if any(marker in lowered for marker in LEGAL_OR_PERMITTING_GUARANTEE_MARKERS):
            issues.append("legal_or_permitting_outcome_guarantee")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            if parsed.hostname not in ALLOWED_HOSTS:
                issues.append("non_allowlisted_url")
            if any(marker in parsed.path.lower() for marker in AUTHENTICATED_URL_MARKERS):
                issues.append("authenticated_url")


def _is_active_mutation_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in ACTIVE_MUTATION_VALUES
    return False


def _command_requests_live_fetch_or_download(command: str) -> bool:
    lowered = command.lower()
    try:
        tokens = [token.lower() for token in shlex.split(command)]
    except ValueError:
        tokens = lowered.split()
    if any(token in LIVE_COMMAND_TOKENS for token in tokens):
        return True
    if any(token in DOWNLOAD_COMMAND_TOKENS for token in tokens):
        return True
    if "http://" in lowered or "https://" in lowered:
        return True
    return False
