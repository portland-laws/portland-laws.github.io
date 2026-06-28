"""Fixture-first execution plans for public PP&D metadata recrawls.

The planner is intentionally side-effect free. It consumes a reviewed public
recrawl fixture plus an implementation-readiness packet, validates both, and
returns ordered dry-run steps that can be reviewed before any network client or
processor suite is invoked.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlparse

from ppd.crawler.processor_handoff_dry_run import (
    build_processor_handoff_dry_run_packet,
    validate_processor_handoff_dry_run_packet,
)
from ppd.crawler.public_crawl_readiness import validate_public_crawl_readiness

_ALLOWED_PUBLIC_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

_PRIVATE_DEVHUB_PREFIXES = (
    "/account",
    "/accounts",
    "/application",
    "/applications",
    "/cart",
    "/dashboard",
    "/document",
    "/documents",
    "/inspection",
    "/inspections",
    "/my",
    "/payment",
    "/payments",
    "/permit",
    "/permits",
    "/secure",
    "/session",
    "/sessions",
    "/upload",
    "/uploads",
)

_PRIVATE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "auth",
        "auth_token",
        "code",
        "credential",
        "key",
        "password",
        "session",
        "session_id",
        "state",
        "token",
    }
)

_URL_FIELD_NAMES = frozenset(
    {
        "canonical_url",
        "canonicalurl",
        "requested_url",
        "requestedurl",
        "source_url",
        "sourceurl",
        "url",
    }
)

_LIVE_NETWORK_KEYS = frozenset(
    {
        "allow_live_network",
        "allow_network",
        "execute_live",
        "live_crawl",
        "live_network",
        "network_enabled",
        "network_invoked",
        "networkinvoked",
        "networkallowed",
        "run_live",
        "use_live_network",
    }
)

_RAW_OR_PRIVATE_KEYS = frozenset(
    {
        "archive_path",
        "archivepath",
        "auth_state",
        "authstate",
        "body",
        "bytes",
        "content",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "document_path",
        "documentpath",
        "download_path",
        "downloadpath",
        "downloaded_document_path",
        "downloadeddocumentpath",
        "har_path",
        "harpath",
        "html",
        "local_path",
        "localpath",
        "pdf_path",
        "pdfpath",
        "raw_body",
        "raw_content",
        "raw_html",
        "rawbody",
        "rawcontent",
        "rawhtml",
        "response_body",
        "responsebody",
        "screenshot_path",
        "screenshotpath",
        "session_state",
        "sessionstate",
        "text",
        "trace_path",
        "tracepath",
        "warc_path",
        "warcpath",
    }
)

_REQUIRED_STEP_IDS = (
    "validate_reviewed_recrawl_batch",
    "validate_implementation_readiness_packet",
    "robots_policy_checkpoint",
    "apply_host_rate_limit_windows",
    "prepare_processor_handoff_inputs",
    "stage_metadata_only_outputs",
    "record_rollback_notes",
)


def build_public_metadata_recrawl_execution_plan(
    reviewed_recrawl_batch: Mapping[str, Any],
    implementation_readiness_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build an ordered dry-run execution plan without network side effects."""

    generated_time = _parse_utc_timestamp(generated_at)
    readiness_errors = validate_public_crawl_readiness(
        dict(implementation_readiness_packet),
        now=generated_time,
    )
    if readiness_errors:
        raise ValueError("implementation readiness packet failed validation: " + "; ".join(readiness_errors))

    handoff_packet = build_processor_handoff_dry_run_packet(
        reviewed_recrawl_batch,
        generated_at=generated_at,
    )
    handoff_errors = validate_processor_handoff_dry_run_packet(handoff_packet)
    if handoff_errors:
        raise ValueError("processor handoff packet failed validation: " + "; ".join(handoff_errors))

    documents = list(handoff_packet["documents"])
    host_rate_limit_windows = _host_rate_limit_windows(documents, implementation_readiness_packet)
    robots_policy_checkpoints = _robots_policy_checkpoints(documents, implementation_readiness_packet, generated_at)
    metadata_only_output_paths = _metadata_only_output_paths(documents)
    rollback_notes = _rollback_notes(metadata_only_output_paths)

    plan = {
        "schemaVersion": 1,
        "planType": "ppd_public_metadata_recrawl_execution_plan",
        "generatedAt": generated_at,
        "sourceBatch": handoff_packet["sourceBatch"],
        "executionPolicy": {
            "dryRunOnly": True,
            "networkInvoked": False,
            "processorInvoked": False,
            "metadataOnly": True,
            "persistRawBody": False,
            "downloadDocuments": False,
            "requiresHumanReviewBeforeLiveRun": True,
        },
        "orderedDryRunSteps": _ordered_steps(
            host_rate_limit_windows=host_rate_limit_windows,
            robots_policy_checkpoints=robots_policy_checkpoints,
            metadata_only_output_paths=metadata_only_output_paths,
            rollback_notes=rollback_notes,
        ),
        "hostRateLimitWindows": host_rate_limit_windows,
        "robotsPolicyCheckpoints": robots_policy_checkpoints,
        "processorHandoffInputs": [document["processorInput"] for document in documents],
        "metadataOnlyOutputPaths": metadata_only_output_paths,
        "rollbackNotes": rollback_notes,
    }
    errors = validate_public_metadata_recrawl_execution_plan(plan)
    if errors:
        raise ValueError("public metadata recrawl execution plan failed validation: " + "; ".join(errors))
    return plan


def validate_public_metadata_recrawl_execution_plan(plan: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a public metadata recrawl plan."""

    errors: list[str] = []
    if plan.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if plan.get("planType") != "ppd_public_metadata_recrawl_execution_plan":
        errors.append("planType must be ppd_public_metadata_recrawl_execution_plan")
    if not _is_utc_timestamp(plan.get("generatedAt")):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    policy = _mapping(plan.get("executionPolicy"))
    expected_policy = {
        "dryRunOnly": True,
        "networkInvoked": False,
        "processorInvoked": False,
        "metadataOnly": True,
        "persistRawBody": False,
        "downloadDocuments": False,
        "requiresHumanReviewBeforeLiveRun": True,
    }
    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            errors.append(f"executionPolicy.{key} must be {str(expected).lower()}")

    steps = plan.get("orderedDryRunSteps")
    if not isinstance(steps, list):
        errors.append("orderedDryRunSteps must be a list")
        step_ids: list[str] = []
    else:
        step_ids = [step.get("stepId") for step in steps if isinstance(step, Mapping)]
        if tuple(step_ids) != _REQUIRED_STEP_IDS:
            errors.append("orderedDryRunSteps must use the required dry-run order")
        for index, step in enumerate(steps):
            if not isinstance(step, Mapping):
                errors.append(f"orderedDryRunSteps[{index}] must be an object")
                continue
            if step.get("networkAllowed") is not False:
                errors.append(f"orderedDryRunSteps[{index}].networkAllowed must be false")
            if step.get("processorAllowed") is True and step.get("stepId") != "prepare_processor_handoff_inputs":
                errors.append(f"orderedDryRunSteps[{index}].processorAllowed must be false outside handoff preparation")
            if step.get("stepId") == "prepare_processor_handoff_inputs" and step.get("processorInvocationAllowed") is not False:
                errors.append("orderedDryRunSteps prepare_processor_handoff_inputs must not allow processor invocation")

    checkpoints = plan.get("robotsPolicyCheckpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        errors.append("robotsPolicyCheckpoints must be a non-empty list")
        checkpoint_source_ids: set[str] = set()
    else:
        checkpoint_source_ids = set()
        for index, checkpoint in enumerate(checkpoints):
            if not isinstance(checkpoint, Mapping):
                errors.append(f"robotsPolicyCheckpoints[{index}] must be an object")
                continue
            source_id = checkpoint.get("sourceId")
            if isinstance(source_id, str):
                checkpoint_source_ids.add(source_id)
            if checkpoint.get("robotsStatus") not in {"allowed", "permitted", "public_allowed"}:
                errors.append(f"robotsPolicyCheckpoints[{index}].robotsStatus must be allowed")
            if checkpoint.get("policyStatus") not in {"approved", "allowed", "public", "public_allowed"}:
                errors.append(f"robotsPolicyCheckpoints[{index}].policyStatus must be approved")
            if checkpoint.get("networkInvoked") is not False:
                errors.append(f"robotsPolicyCheckpoints[{index}].networkInvoked must be false")
            if checkpoint.get("requiredBeforeProcessorInvocation") is not True:
                errors.append(f"robotsPolicyCheckpoints[{index}].requiredBeforeProcessorInvocation must be true")

    processor_inputs = plan.get("processorHandoffInputs")
    processor_source_ids: set[str] = set()
    processor_hosts_by_source: dict[str, str] = {}
    if not isinstance(processor_inputs, list) or not processor_inputs:
        errors.append("processorHandoffInputs must be a non-empty list")
    else:
        for index, processor_input in enumerate(processor_inputs):
            if not isinstance(processor_input, Mapping):
                errors.append(f"processorHandoffInputs[{index}] must be an object")
                continue
            source_id = processor_input.get("sourceId")
            if isinstance(source_id, str):
                processor_source_ids.add(source_id)
            for url_key in ("canonicalUrl", "requestedUrl"):
                parsed_url = _public_url_error(processor_input.get(url_key), f"processorHandoffInputs[{index}].{url_key}")
                if parsed_url:
                    errors.append(parsed_url)
            canonical_url = processor_input.get("canonicalUrl")
            if isinstance(source_id, str) and isinstance(canonical_url, str):
                host = urlparse(canonical_url).hostname
                if host:
                    processor_hosts_by_source[source_id] = host
            processor = _mapping(processor_input.get("processor"))
            arguments = _mapping(processor_input.get("arguments"))
            if processor.get("operation") != "capture_url_metadata_only":
                errors.append(f"processorHandoffInputs[{index}].processor.operation must be capture_url_metadata_only")
            if arguments.get("metadataOnly") is not True:
                errors.append(f"processorHandoffInputs[{index}].arguments.metadataOnly must be true")
            if arguments.get("persistRawBody") is not False:
                errors.append(f"processorHandoffInputs[{index}].arguments.persistRawBody must be false")
            if arguments.get("downloadDocuments") is not False:
                errors.append(f"processorHandoffInputs[{index}].arguments.downloadDocuments must be false")

    if processor_source_ids and checkpoint_source_ids and processor_source_ids != checkpoint_source_ids:
        errors.append("robotsPolicyCheckpoints must cover every processor handoff source")

    rate_windows = plan.get("hostRateLimitWindows")
    rate_window_source_ids: set[str] = set()
    if not isinstance(rate_windows, list) or not rate_windows:
        errors.append("hostRateLimitWindows must be a non-empty list")
    else:
        for index, window in enumerate(rate_windows):
            if not isinstance(window, Mapping):
                errors.append(f"hostRateLimitWindows[{index}] must be an object")
                continue
            host = window.get("host")
            if not isinstance(host, str) or not host:
                errors.append(f"hostRateLimitWindows[{index}].host is required")
            elif host not in _ALLOWED_PUBLIC_HOSTS:
                errors.append(f"hostRateLimitWindows[{index}].host is not PP&D allowlisted: {host}")
            source_ids = window.get("appliesToSourceIds")
            if not isinstance(source_ids, list) or not all(isinstance(item, str) and item for item in source_ids):
                errors.append(f"hostRateLimitWindows[{index}].appliesToSourceIds must be a non-empty list of source ids")
            else:
                rate_window_source_ids.update(source_ids)
                for source_id in source_ids:
                    expected_host = processor_hosts_by_source.get(source_id)
                    if expected_host and host != expected_host:
                        errors.append(f"hostRateLimitWindows[{index}] host must match processor source {source_id}")
            if not _positive_number(window.get("minDelaySeconds")):
                errors.append(f"hostRateLimitWindows[{index}].minDelaySeconds must be positive")
            if not _positive_int(window.get("maxRequestsPerWindow")):
                errors.append(f"hostRateLimitWindows[{index}].maxRequestsPerWindow must be positive")
            if window.get("networkInvoked") is not False:
                errors.append(f"hostRateLimitWindows[{index}].networkInvoked must be false")

    if processor_source_ids and rate_window_source_ids != processor_source_ids:
        errors.append("hostRateLimitWindows must cover every processor handoff source")

    output_paths = plan.get("metadataOnlyOutputPaths")
    output_source_ids: set[str] = set()
    if not isinstance(output_paths, list) or not output_paths:
        errors.append("metadataOnlyOutputPaths must be a non-empty list")
    else:
        for index, output in enumerate(output_paths):
            if not isinstance(output, Mapping):
                errors.append(f"metadataOnlyOutputPaths[{index}] must be an object")
                continue
            source_id = output.get("sourceId")
            if isinstance(source_id, str):
                output_source_ids.add(source_id)
            for key in ("processorInputPath", "archiveManifestPath", "normalizedDocumentPath"):
                if not _is_metadata_json_path(output.get(key)):
                    errors.append(f"metadataOnlyOutputPaths[{index}].{key} must be a relative metadata JSON path")
            if output.get("metadataOnly") is not True:
                errors.append(f"metadataOnlyOutputPaths[{index}].metadataOnly must be true")
            if output.get("rawBodyPersisted") is not False:
                errors.append(f"metadataOnlyOutputPaths[{index}].rawBodyPersisted must be false")
            if output.get("downloadedDocumentsPersisted") is not False:
                errors.append(f"metadataOnlyOutputPaths[{index}].downloadedDocumentsPersisted must be false")

    rollback_notes = plan.get("rollbackNotes")
    rollback_source_ids: set[str] = set()
    if not isinstance(rollback_notes, list) or not rollback_notes:
        errors.append("rollbackNotes must be a non-empty list")
    else:
        for index, note in enumerate(rollback_notes):
            if not isinstance(note, Mapping):
                errors.append(f"rollbackNotes[{index}] must be an object")
                continue
            source_id = note.get("sourceId")
            if isinstance(source_id, str):
                rollback_source_ids.add(source_id)
            if note.get("action") != "discard_staged_metadata_json_only":
                errors.append(f"rollbackNotes[{index}].action must be discard_staged_metadata_json_only")
            if note.get("networkRollbackRequired") is not False:
                errors.append(f"rollbackNotes[{index}].networkRollbackRequired must be false")
            if note.get("privateArtifactCleanupRequired") is not False:
                errors.append(f"rollbackNotes[{index}].privateArtifactCleanupRequired must be false")
            artifacts = note.get("metadataArtifactsToRemove")
            if not isinstance(artifacts, list) or not artifacts:
                errors.append(f"rollbackNotes[{index}].metadataArtifactsToRemove must be a non-empty list")
            elif not all(_is_metadata_json_path(path) for path in artifacts):
                errors.append(f"rollbackNotes[{index}].metadataArtifactsToRemove must contain only relative metadata JSON paths")

    if output_source_ids and rollback_source_ids != output_source_ids:
        errors.append("rollbackNotes must cover every metadata-only output source")

    errors.extend(_reject_live_network_flags(plan, "plan"))
    errors.extend(_reject_raw_or_private_keys(plan, "plan"))
    errors.extend(_reject_unsafe_urls(plan, "plan"))
    return _dedupe(errors)


def _ordered_steps(
    *,
    host_rate_limit_windows: list[dict[str, Any]],
    robots_policy_checkpoints: list[dict[str, Any]],
    metadata_only_output_paths: list[dict[str, Any]],
    rollback_notes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "stepId": "validate_reviewed_recrawl_batch",
            "description": "Confirm the reviewed batch is public, approved for metadata-only handling, and fixture-backed.",
            "networkAllowed": False,
            "processorAllowed": False,
        },
        {
            "order": 2,
            "stepId": "validate_implementation_readiness_packet",
            "description": "Check readiness anchors, public URL safety, approved policy status, and bounded rate limits.",
            "networkAllowed": False,
            "processorAllowed": False,
        },
        {
            "order": 3,
            "stepId": "robots_policy_checkpoint",
            "description": "Require one allowed robots and crawl-policy checkpoint for every processor input.",
            "networkAllowed": False,
            "processorAllowed": False,
            "checkpointCount": len(robots_policy_checkpoints),
        },
        {
            "order": 4,
            "stepId": "apply_host_rate_limit_windows",
            "description": "Assign each source to a host bucket before any future live run is separately approved.",
            "networkAllowed": False,
            "processorAllowed": False,
            "windowCount": len(host_rate_limit_windows),
        },
        {
            "order": 5,
            "stepId": "prepare_processor_handoff_inputs",
            "description": "Prepare ipfs_datasets_py metadata-only handoff inputs without invoking processors.",
            "networkAllowed": False,
            "processorAllowed": True,
            "processorInvocationAllowed": False,
        },
        {
            "order": 6,
            "stepId": "stage_metadata_only_outputs",
            "description": "Plan relative JSON metadata output paths only; no raw bodies or downloaded documents are staged.",
            "networkAllowed": False,
            "processorAllowed": False,
            "outputCount": len(metadata_only_output_paths),
        },
        {
            "order": 7,
            "stepId": "record_rollback_notes",
            "description": "Record how to discard staged metadata if review fails before any live crawl occurs.",
            "networkAllowed": False,
            "processorAllowed": False,
            "rollbackNoteCount": len(rollback_notes),
        },
    ]


def _host_rate_limit_windows(
    documents: list[Mapping[str, Any]],
    readiness_packet: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rate_limit = _mapping(readiness_packet.get("rate_limit"))
    min_delay = rate_limit.get("min_delay_seconds", 10)
    max_requests = rate_limit.get("max_requests_per_host", rate_limit.get("requests_per_minute", 6))

    sources_by_host: dict[str, list[str]] = defaultdict(list)
    for document in documents:
        processor_input = _mapping(document.get("processorInput"))
        canonical_url = str(processor_input.get("canonicalUrl", ""))
        host = urlparse(canonical_url).hostname or "unknown"
        source_id = str(processor_input.get("sourceId", ""))
        if source_id:
            sources_by_host[host].append(source_id)

    windows: list[dict[str, Any]] = []
    for index, host in enumerate(sorted(sources_by_host), start=1):
        windows.append(
            {
                "windowId": f"host-window-{index:03d}",
                "host": host,
                "windowSeconds": 60,
                "minDelaySeconds": min_delay,
                "maxRequestsPerWindow": max_requests,
                "appliesToSourceIds": sorted(sources_by_host[host]),
                "networkInvoked": False,
            }
        )
    return windows


def _robots_policy_checkpoints(
    documents: list[Mapping[str, Any]],
    readiness_packet: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    robots_status = _status(readiness_packet, "robots_status", "robots")
    policy_status = _status(readiness_packet, "policy_status", "crawl_policy_status")
    checkpoints: list[dict[str, Any]] = []
    for index, document in enumerate(documents, start=1):
        processor_input = _mapping(document.get("processorInput"))
        checkpoints.append(
            {
                "checkpointId": f"robots-policy-{index:03d}",
                "sourceId": processor_input.get("sourceId"),
                "canonicalUrl": processor_input.get("canonicalUrl"),
                "robotsStatus": robots_status,
                "policyStatus": policy_status,
                "checkedAt": generated_at,
                "evidenceSource": "implementation_readiness_packet",
                "networkInvoked": False,
                "requiredBeforeProcessorInvocation": True,
            }
        )
    return checkpoints


def _metadata_only_output_paths(documents: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for document in documents:
        paths = _mapping(document.get("metadataOnlyOutputPaths"))
        outputs.append(
            {
                "sourceId": document.get("sourceId"),
                "processorInputPath": paths.get("processorInputPath"),
                "archiveManifestPath": paths.get("archiveManifestPath"),
                "normalizedDocumentPath": paths.get("normalizedDocumentPath"),
                "metadataOnly": True,
                "rawBodyPersisted": False,
                "downloadedDocumentsPersisted": False,
            }
        )
    return outputs


def _rollback_notes(outputs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for index, output in enumerate(outputs, start=1):
        artifacts = [
            str(output["processorInputPath"]),
            str(output["archiveManifestPath"]),
            str(output["normalizedDocumentPath"]),
        ]
        notes.append(
            {
                "rollbackId": f"metadata-rollback-{index:03d}",
                "sourceId": output.get("sourceId"),
                "trigger": "human_review_rejects_dry_run_or_live_execution_not_approved",
                "action": "discard_staged_metadata_json_only",
                "metadataArtifactsToRemove": artifacts,
                "networkRollbackRequired": False,
                "privateArtifactCleanupRequired": False,
            }
        )
    return notes


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _status(packet: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = packet.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower().replace("-", "_").replace(" ", "_")
        if isinstance(value, Mapping):
            nested = value.get("status") or value.get("decision")
            if isinstance(nested, str) and nested.strip():
                return nested.strip().lower().replace("-", "_").replace(" ", "_")
    return "missing"


def _parse_utc_timestamp(value: str) -> datetime:
    if not _is_utc_timestamp(value):
        raise ValueError("generated_at must be an ISO UTC timestamp ending in Z")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _is_utc_timestamp(value: Any) -> bool:
    return isinstance(value, str) and value.endswith("Z") and "T" in value


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_metadata_json_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith(".json"):
        return False
    if value.startswith(("/", "./", "../", "~")):
        return False
    path = PurePosixPath(value)
    return str(path).startswith("metadata_outputs/")


def _public_url_error(value: Any, path: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return f"{path} must be a non-empty URL string"
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return f"{path} must use https"
    host = parsed.hostname or ""
    if host not in _ALLOWED_PUBLIC_HOSTS:
        return f"{path} host is not PP&D allowlisted: {host}"
    if parsed.username or parsed.password:
        return f"{path} must not include authenticated URL userinfo"
    query_keys = {key.strip().lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys.intersection(_PRIVATE_QUERY_KEYS):
        return f"{path} must not include authenticated or private query parameters"
    if host == "devhub.portlandoregon.gov":
        url_path = "/" + parsed.path.strip("/").lower()
        if any(url_path == prefix or url_path.startswith(prefix + "/") for prefix in _PRIVATE_DEVHUB_PREFIXES):
            return f"{path} must not reference private DevHub account paths"
    return None


def _reject_live_network_flags(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.replace("-", "_").lower() in _LIVE_NETWORK_KEYS and child is True:
                errors.append(f"{child_path} must not enable live-network execution")
            errors.extend(_reject_live_network_flags(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_reject_live_network_flags(child, f"{path}[{index}]"))
    return errors


def _reject_raw_or_private_keys(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.replace("-", "_").lower()
            child_path = f"{path}.{key_text}"
            if normalized in _RAW_OR_PRIVATE_KEYS:
                errors.append(f"{child_path} is not allowed in metadata-only execution plans")
            errors.extend(_reject_raw_or_private_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_reject_raw_or_private_keys(child, f"{path}[{index}]"))
    return errors


def _reject_unsafe_urls(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.replace("-", "_").lower()
            child_path = f"{path}.{key_text}"
            if normalized in _URL_FIELD_NAMES:
                error = _public_url_error(child, child_path)
                if error:
                    errors.append(error)
            else:
                errors.extend(_reject_unsafe_urls(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_reject_unsafe_urls(child, f"{path}[{index}]"))
    return errors


def _dedupe(errors: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            unique.append(error)
    return unique
