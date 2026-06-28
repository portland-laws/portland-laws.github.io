"""Operator checklist packets for fixture-first public PP&D recrawls.

The checklist packet is a human-run review artifact. It converts an already
validated public metadata recrawl execution plan plus a SourceRegistry promotion
review packet into ordered operator checklist steps. It does not fetch URLs,
invoke processors, edit registries, or persist raw crawl output.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping
from urllib.parse import urlparse

from ppd.crawler.public_metadata_recrawl_execution_plan import validate_public_metadata_recrawl_execution_plan

CHECKLIST_PACKET_VERSION = 1
_REQUIRED_STEP_IDS = (
    "confirm_fixture_inputs",
    "robots_policy_manual_check",
    "rate_limit_window_manual_schedule",
    "processor_dry_run_verification",
    "metadata_only_output_review",
    "abort_condition_review",
    "post_run_source_registry_review",
)
_FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "allow_live_network",
        "allow_network",
        "download_documents",
        "downloaded_documents_persisted",
        "execute_live",
        "live_crawl",
        "live_network",
        "live_registry_edited",
        "network_allowed",
        "network_invoked",
        "network_requests_made",
        "persist_raw_body",
        "processor_invoked",
        "raw_body_persisted",
        "raw_page_bodies_stored",
        "registry_mutated",
        "run_live",
        "use_live_network",
    }
)
_FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "archive_path",
        "auth_state",
        "body",
        "content",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "download_path",
        "downloaded_document_path",
        "har_path",
        "html",
        "local_path",
        "password",
        "pdf_path",
        "raw_body",
        "raw_content",
        "raw_html",
        "response_body",
        "screenshot_path",
        "session_state",
        "storage_state",
        "text",
        "trace_path",
        "warc_path",
    }
)
_PRIVATE_PATH_MARKERS = ("/account", "/accounts", "/application", "/applications", "/cart", "/dashboard", "/payment", "/payments", "/permit", "/permits", "/session", "/sessions", "/upload", "/uploads")
_PRIVATE_QUERY_MARKERS = ("access_token=", "auth=", "code=", "password=", "session=", "token=")


def build_public_recrawl_operator_checklist_packet(
    metadata_recrawl_execution_plan: Mapping[str, Any],
    source_registry_promotion_review_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a no-network public recrawl operator checklist packet."""

    execution_plan = deepcopy(dict(metadata_recrawl_execution_plan))
    promotion_review = deepcopy(dict(source_registry_promotion_review_packet))
    plan_errors = validate_public_metadata_recrawl_execution_plan(execution_plan)
    if plan_errors:
        raise ValueError("metadata recrawl execution plan failed validation: " + "; ".join(plan_errors))
    promotion_errors = _promotion_review_errors(promotion_review)
    if promotion_errors:
        raise ValueError("source registry promotion review packet failed validation: " + "; ".join(promotion_errors))

    robots_checks = _robots_checks(execution_plan)
    rate_limit_windows = _rate_limit_windows(execution_plan)
    processor_checks = _processor_checks(execution_plan)
    metadata_outputs = _metadata_outputs(execution_plan)
    abort_conditions = _abort_conditions(promotion_review)
    post_run_review = _post_run_review(promotion_review)

    packet = {
        "schemaVersion": CHECKLIST_PACKET_VERSION,
        "packetType": "ppd_public_recrawl_operator_checklist_packet",
        "generatedAt": generated_at,
        "fixtureFirst": True,
        "operatorMode": "human_run_public_metadata_recrawl_checklist",
        "executionPolicy": {
            "networkAllowed": False,
            "networkInvoked": False,
            "processorInvocationAllowed": False,
            "processorInvoked": False,
            "metadataOnly": True,
            "persistRawBody": False,
            "downloadDocuments": False,
            "liveRegistryEdited": False,
        },
        "inputArtifactLinks": {
            "metadataRecrawlPlanType": execution_plan.get("planType"),
            "metadataRecrawlGeneratedAt": execution_plan.get("generatedAt"),
            "sourceBatch": deepcopy(execution_plan.get("sourceBatch", {})),
            "sourceRegistryPromotionReviewPacketId": promotion_review.get("packet_id"),
            "sourceRegistryPromotionReviewMode": promotion_review.get("review_mode"),
        },
        "checklistSteps": _checklist_steps(
            robots_checks=robots_checks,
            rate_limit_windows=rate_limit_windows,
            processor_checks=processor_checks,
            metadata_outputs=metadata_outputs,
            abort_conditions=abort_conditions,
            post_run_review=post_run_review,
        ),
        "robotsChecks": robots_checks,
        "rateLimitWindows": rate_limit_windows,
        "processorDryRunVerification": processor_checks,
        "metadataOnlyOutputs": metadata_outputs,
        "abortConditions": abort_conditions,
        "postRunReview": post_run_review,
        "operatorSignoff": {
            "required": True,
            "requiredFields": ["operator_name", "reviewed_at", "all_steps_initialed", "abort_conditions_checked", "post_run_review_completed"],
            "networkEvidenceAllowed": False,
            "privateArtifactEvidenceAllowed": False,
        },
    }
    errors = validate_public_recrawl_operator_checklist_packet(packet)
    if errors:
        raise ValueError("public recrawl operator checklist packet failed validation: " + "; ".join(errors))
    return packet


def validate_public_recrawl_operator_checklist_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for an operator checklist packet."""

    errors: list[str] = []
    if packet.get("schemaVersion") != CHECKLIST_PACKET_VERSION:
        errors.append("schemaVersion must be 1")
    if packet.get("packetType") != "ppd_public_recrawl_operator_checklist_packet":
        errors.append("packetType must be ppd_public_recrawl_operator_checklist_packet")
    if packet.get("fixtureFirst") is not True:
        errors.append("fixtureFirst must be true")
    if not _is_utc_timestamp(packet.get("generatedAt")):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    policy = _mapping(packet.get("executionPolicy"))
    expected_policy = {
        "networkAllowed": False,
        "networkInvoked": False,
        "processorInvocationAllowed": False,
        "processorInvoked": False,
        "metadataOnly": True,
        "persistRawBody": False,
        "downloadDocuments": False,
        "liveRegistryEdited": False,
    }
    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            errors.append(f"executionPolicy.{key} must be {str(expected).lower()}")

    steps = packet.get("checklistSteps")
    if not isinstance(steps, list):
        errors.append("checklistSteps must be a list")
    else:
        step_ids = [step.get("stepId") for step in steps if isinstance(step, Mapping)]
        if tuple(step_ids) != _REQUIRED_STEP_IDS:
            errors.append("checklistSteps must use the required operator order")
        for index, step in enumerate(steps):
            if not isinstance(step, Mapping):
                errors.append(f"checklistSteps[{index}] must be an object")
                continue
            if step.get("networkAllowed") is not False:
                errors.append(f"checklistSteps[{index}].networkAllowed must be false")
            if step.get("processorInvocationAllowed") is not False:
                errors.append(f"checklistSteps[{index}].processorInvocationAllowed must be false")
            if step.get("requiresOperatorInitials") is not True:
                errors.append(f"checklistSteps[{index}].requiresOperatorInitials must be true")

    for key in ("robotsChecks", "rateLimitWindows", "processorDryRunVerification", "metadataOnlyOutputs", "abortConditions"):
        value = packet.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"{key} must be a non-empty list")

    post_run_review = _mapping(packet.get("postRunReview"))
    if post_run_review.get("promotionEnabled") is not False:
        errors.append("postRunReview.promotionEnabled must be false")
    if post_run_review.get("liveRegistryEdited") is not False:
        errors.append("postRunReview.liveRegistryEdited must be false")
    if post_run_review.get("requiresSeparatePromotionDecision") is not True:
        errors.append("postRunReview.requiresSeparatePromotionDecision must be true")

    signoff = _mapping(packet.get("operatorSignoff"))
    if signoff.get("required") is not True:
        errors.append("operatorSignoff.required must be true")
    if signoff.get("networkEvidenceAllowed") is not False:
        errors.append("operatorSignoff.networkEvidenceAllowed must be false")
    if signoff.get("privateArtifactEvidenceAllowed") is not False:
        errors.append("operatorSignoff.privateArtifactEvidenceAllowed must be false")

    errors.extend(_reject_forbidden_values(packet, "packet"))
    errors.extend(_reject_private_urls(packet, "packet"))
    return _dedupe(errors)


def _checklist_steps(
    *,
    robots_checks: list[dict[str, Any]],
    rate_limit_windows: list[dict[str, Any]],
    processor_checks: list[dict[str, Any]],
    metadata_outputs: list[dict[str, Any]],
    abort_conditions: list[dict[str, Any]],
    post_run_review: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _step(1, "confirm_fixture_inputs", "Confirm the execution plan and SourceRegistry promotion review packet are committed fixtures and remain review-only.", ["inputArtifactLinks", "executionPolicy"]),
        _step(2, "robots_policy_manual_check", "Review every robots and crawl-policy checkpoint before any separately approved live recrawl window.", [check["checkpointId"] for check in robots_checks]),
        _step(3, "rate_limit_window_manual_schedule", "Confirm host rate-limit windows and source coverage before scheduling any future live run.", [window["windowId"] for window in rate_limit_windows]),
        _step(4, "processor_dry_run_verification", "Verify processor handoff inputs are metadata-only dry-run inputs and do not allow processor invocation from this packet.", [check["verificationId"] for check in processor_checks]),
        _step(5, "metadata_only_output_review", "Confirm planned outputs are relative JSON metadata artifacts with no raw body or downloaded document persistence.", [output["outputId"] for output in metadata_outputs]),
        _step(6, "abort_condition_review", "Stop the run if any abort condition is observed before, during, or after operator review.", [condition["conditionId"] for condition in abort_conditions]),
        _step(7, "post_run_source_registry_review", "Review metadata-only field changes and unresolved blockers; keep production promotion disabled pending a separate decision.", post_run_review["reviewEvidenceIds"]),
    ]


def _step(order: int, step_id: str, instruction: str, evidence_required: list[str]) -> dict[str, Any]:
    return {
        "order": order,
        "stepId": step_id,
        "instruction": instruction,
        "networkAllowed": False,
        "processorInvocationAllowed": False,
        "requiresOperatorInitials": True,
        "evidenceRequired": evidence_required,
    }


def _robots_checks(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for checkpoint in plan.get("robotsPolicyCheckpoints", []):
        if not isinstance(checkpoint, Mapping):
            continue
        checks.append(
            {
                "checkpointId": str(checkpoint.get("checkpointId")),
                "sourceId": str(checkpoint.get("sourceId")),
                "canonicalUrl": str(checkpoint.get("canonicalUrl")),
                "robotsStatus": checkpoint.get("robotsStatus"),
                "policyStatus": checkpoint.get("policyStatus"),
                "requiredBeforeProcessorInvocation": True,
                "networkAllowed": False,
            }
        )
    return checks


def _rate_limit_windows(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for window in plan.get("hostRateLimitWindows", []):
        if not isinstance(window, Mapping):
            continue
        windows.append(
            {
                "windowId": str(window.get("windowId")),
                "host": str(window.get("host")),
                "windowSeconds": window.get("windowSeconds"),
                "minDelaySeconds": window.get("minDelaySeconds"),
                "maxRequestsPerWindow": window.get("maxRequestsPerWindow"),
                "appliesToSourceIds": list(window.get("appliesToSourceIds", [])),
                "networkAllowed": False,
            }
        )
    return windows


def _processor_checks(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for item in plan.get("processorHandoffInputs", []):
        if not isinstance(item, Mapping):
            continue
        source_id = str(item.get("sourceId"))
        arguments = _mapping(item.get("arguments"))
        processor = _mapping(item.get("processor"))
        checks.append(
            {
                "verificationId": "processor-dry-run-" + _stable_id(source_id),
                "sourceId": source_id,
                "canonicalUrl": item.get("canonicalUrl"),
                "processorName": processor.get("name"),
                "processorOperation": processor.get("operation"),
                "metadataOnly": arguments.get("metadataOnly") is True,
                "persistRawBody": False,
                "downloadDocuments": False,
                "processorInvocationAllowed": False,
            }
        )
    return checks


def _metadata_outputs(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for item in plan.get("metadataOnlyOutputPaths", []):
        if not isinstance(item, Mapping):
            continue
        source_id = str(item.get("sourceId"))
        outputs.append(
            {
                "outputId": "metadata-output-" + _stable_id(source_id),
                "sourceId": source_id,
                "processorInputPath": item.get("processorInputPath"),
                "archiveManifestPath": item.get("archiveManifestPath"),
                "normalizedDocumentPath": item.get("normalizedDocumentPath"),
                "metadataOnly": True,
                "rawBodyPersisted": False,
                "downloadedDocumentsPersisted": False,
            }
        )
    return outputs


def _abort_conditions(promotion_review: Mapping[str, Any]) -> list[dict[str, Any]]:
    blocker_count = len(promotion_review.get("unresolved_blockers", [])) if isinstance(promotion_review.get("unresolved_blockers"), list) else 0
    return [
        _abort("robots_or_policy_not_allowed", "Abort if a robots or crawl-policy checkpoint is missing, stale, disallowed, or uncertain."),
        _abort("rate_limit_window_unavailable", "Abort if the operator cannot preserve the documented host delay or request window."),
        _abort("processor_would_invoke_live_network", "Abort if any processor dry-run input would fetch URLs or invoke a live processor from this packet."),
        _abort("raw_or_downloaded_artifact_detected", "Abort if raw HTML, PDF bytes, WARC paths, screenshots, traces, HAR files, or downloaded documents appear."),
        _abort("private_or_authenticated_url_detected", "Abort if a DevHub account, payment, permit, upload, session, or private query URL appears."),
        _abort("metadata_output_not_review_only", "Abort if outputs are not relative metadata JSON artifacts or claim raw body persistence."),
        _abort("source_registry_promotion_enabled", "Abort if the SourceRegistry review packet enables live promotion or edits production records."),
        {
            "conditionId": "unresolved_blockers_require_post_run_review",
            "description": "Keep production promotion disabled while unresolved blockers remain in the SourceRegistry promotion review packet.",
            "presentInInput": blocker_count > 0,
            "abortRequired": True,
        },
    ]


def _abort(condition_id: str, description: str) -> dict[str, Any]:
    return {"conditionId": condition_id, "description": description, "presentInInput": False, "abortRequired": True}


def _post_run_review(promotion_review: Mapping[str, Any]) -> dict[str, Any]:
    production_status = _mapping(promotion_review.get("production_promotion_status"))
    reviewed_changes = promotion_review.get("reviewed_metadata_only_field_changes", [])
    prompts = promotion_review.get("reviewer_prompts", [])
    blockers = promotion_review.get("unresolved_blockers", [])
    evidence_ids: list[str] = []
    if isinstance(reviewed_changes, list):
        for row in reviewed_changes:
            if isinstance(row, Mapping):
                evidence_id = row.get("review_evidence_id")
                if isinstance(evidence_id, str) and evidence_id:
                    evidence_ids.append(evidence_id)
    if isinstance(prompts, list):
        for prompt in prompts:
            if isinstance(prompt, Mapping):
                prompt_id = prompt.get("prompt_id")
                if isinstance(prompt_id, str) and prompt_id:
                    evidence_ids.append(prompt_id)
    return {
        "promotionEnabled": production_status.get("enabled") is True,
        "liveRegistryEdited": promotion_review.get("live_registry_edited") is True,
        "requiresSeparatePromotionDecision": True,
        "reviewedMetadataOnlyFieldChangeCount": len(reviewed_changes) if isinstance(reviewed_changes, list) else 0,
        "unresolvedBlockerCount": len(blockers) if isinstance(blockers, list) else 0,
        "reviewPromptCount": len(prompts) if isinstance(prompts, list) else 0,
        "reviewEvidenceIds": sorted(set(evidence_ids)) or ["source-registry-promotion-review-packet"],
    }


def _promotion_review_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("fixture_first") is not True:
        errors.append("promotion review fixture_first must be true")
    if packet.get("metadata_only") is not True:
        errors.append("promotion review metadata_only must be true")
    if packet.get("network_requests_made") is not False:
        errors.append("promotion review network_requests_made must be false")
    if packet.get("raw_page_bodies_stored") is not False:
        errors.append("promotion review raw_page_bodies_stored must be false")
    if packet.get("live_registry_edited") is not False:
        errors.append("promotion review live_registry_edited must be false")
    if packet.get("review_mode") != "promotion_review_only":
        errors.append("promotion review mode must be promotion_review_only")
    production_status = _mapping(packet.get("production_promotion_status"))
    if production_status.get("enabled") is not False:
        errors.append("production promotion must remain disabled")
    if production_status.get("live_registry_records_edited") is not False:
        errors.append("production promotion must not edit live registry records")
    changes = packet.get("reviewed_metadata_only_field_changes")
    if not isinstance(changes, list) or not changes:
        errors.append("promotion review must include reviewed metadata-only field changes")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _stable_id(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_utc_timestamp(value: Any) -> bool:
    return isinstance(value, str) and value.endswith("Z") and "T" in value and len(value) >= 20


def _reject_forbidden_values(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized in _FORBIDDEN_FIELD_NAMES:
                errors.append(f"{child_path} is not allowed in operator checklist packets")
            if normalized in _FORBIDDEN_TRUE_KEYS and child is True:
                errors.append(f"{child_path} must be false")
            errors.extend(_reject_forbidden_values(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_reject_forbidden_values(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith(("/tmp/", "/home/", "file://")) or ".warc" in lowered:
            errors.append(f"{path} must not contain local, raw archive, or downloaded artifact paths")
    return errors


def _reject_private_urls(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            errors.extend(_reject_private_urls(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_reject_private_urls(child, f"{path}[{index}]") )
    elif isinstance(value, str) and value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        path_lower = parsed.path.lower()
        query_lower = parsed.query.lower()
        if parsed.netloc == "devhub.portlandoregon.gov" and any(path_lower.startswith(marker) for marker in _PRIVATE_PATH_MARKERS):
            errors.append(f"{path} must not contain private or authenticated DevHub URLs")
        if any(marker in query_lower for marker in _PRIVATE_QUERY_MARKERS):
            errors.append(f"{path} must not contain authenticated or private query parameters")
    return errors


def _normalize_key(value: str) -> str:
    return value.replace("-", "_").replace(" ", "_").lower()


def _dedupe(errors: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            result.append(error)
    return result
