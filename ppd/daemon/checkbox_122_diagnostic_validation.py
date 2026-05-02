"""Validation for the checkbox-122 daemon diagnostic fixture.

The diagnostic is intentionally about daemon supervision shape, not the public
crawl frontier checkpoint itself. It must keep retry guidance narrow enough to
recover from a blocked task without authorizing a broad rewrite or implementing
new crawler behavior in the diagnostic cycle.
"""

from __future__ import annotations

from typing import Any, Mapping


REQUIRED_BLOCKED_TASK_ID = "checkbox-121"
REQUIRED_SUCCESSOR_VALIDATION_TASK_ID = "checkbox-123"
REQUIRED_ALLOWED_RETRY_SHAPE = "one_file_retry"
REQUIRED_PROHIBITED_RETRY_SHAPE = "broad_rewrite"
REQUIRED_DEFERRED_IMPLEMENTATION = "public_crawl_frontier_checkpoint"


def validate_checkbox_122_diagnostic(data: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a checkbox-122 diagnostic record."""

    errors: list[str] = []

    if data.get("diagnosticTaskId") != "checkbox-122":
        errors.append("diagnosticTaskId must be checkbox-122")

    blocked_task_id = data.get("blockedTaskId")
    if blocked_task_id != REQUIRED_BLOCKED_TASK_ID:
        errors.append(
            "blockedTaskId must report "
            f"{REQUIRED_BLOCKED_TASK_ID}, got {blocked_task_id!r}"
        )

    successor_task_id = data.get("acceptedSuccessorValidationTaskId")
    if successor_task_id != REQUIRED_SUCCESSOR_VALIDATION_TASK_ID:
        errors.append(
            "acceptedSuccessorValidationTaskId must report "
            f"{REQUIRED_SUCCESSOR_VALIDATION_TASK_ID}, got {successor_task_id!r}"
        )

    allowed_retry = data.get("allowedRetryShape")
    if not isinstance(allowed_retry, Mapping):
        errors.append("allowedRetryShape must be an object")
    else:
        if allowed_retry.get("kind") != REQUIRED_ALLOWED_RETRY_SHAPE:
            errors.append("allowedRetryShape.kind must be one_file_retry")
        if allowed_retry.get("maximumFiles") != 1:
            errors.append("allowedRetryShape.maximumFiles must be 1")
        allowed_scope = allowed_retry.get("allowedScope")
        if allowed_scope != ["ppd/daemon/"]:
            errors.append("allowedRetryShape.allowedScope must be ['ppd/daemon/']")

    prohibited_retry = data.get("prohibitedRetryShape")
    if not isinstance(prohibited_retry, Mapping):
        errors.append("prohibitedRetryShape must be an object")
    else:
        if prohibited_retry.get("kind") != REQUIRED_PROHIBITED_RETRY_SHAPE:
            errors.append("prohibitedRetryShape.kind must be broad_rewrite")
        prohibited_paths = prohibited_retry.get("prohibitedPaths")
        if not isinstance(prohibited_paths, list) or not prohibited_paths:
            errors.append("prohibitedRetryShape.prohibitedPaths must be a non-empty list")
        elif "ppd/crawler/" not in prohibited_paths:
            errors.append("prohibitedRetryShape.prohibitedPaths must include ppd/crawler/")

    deferred = data.get("deferredImplementation")
    if deferred != REQUIRED_DEFERRED_IMPLEMENTATION:
        errors.append(
            "deferredImplementation must be public_crawl_frontier_checkpoint"
        )

    if data.get("implementsPublicCrawlFrontierCheckpoint") is not False:
        errors.append("implementsPublicCrawlFrontierCheckpoint must be false")

    validation_claims = data.get("validationClaims")
    if not isinstance(validation_claims, list):
        errors.append("validationClaims must be a list")
    else:
        required_claims = {
            "reports_blocked_task_id",
            "reports_accepted_successor_validation_task_id",
            "reports_allowed_one_file_retry_shape",
            "reports_prohibited_broad_rewrite_shape",
            "does_not_implement_public_crawl_frontier_checkpoint",
        }
        missing_claims = sorted(required_claims.difference(validation_claims))
        if missing_claims:
            errors.append(f"validationClaims missing required claims: {missing_claims}")

    return errors
