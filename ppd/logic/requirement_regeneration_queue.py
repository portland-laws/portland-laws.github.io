"""Fixture-first requirement regeneration queue planning.

This module is intentionally side-effect free. It consumes committed rehearsal,
freshness drift, and dependency-index fixtures and returns deterministic queue
items that can be reviewed before any downstream process model or guardrail
activation is allowed.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CONSEQUENTIAL_CHANGE_KINDS = {
    "changed_required_document",
    "changed_file_rule",
    "changed_fee_instruction",
    "changed_deadline",
    "changed_devhub_action_guidance",
    "removed_permit_type",
    "added_permit_type",
}

STALE_FRESHNESS_STATUSES = {
    "stale",
    "expired",
    "outdated",
    "superseded",
    "needs_refresh",
    "missing",
    "unknown",
}

CURRENT_STATUSES = {
    "current",
    "fresh",
    "valid",
    "up_to_date",
    "unchanged",
}

REVIEWED_STATUSES = {
    "reviewed",
    "approved",
    "accepted",
    "human_reviewed",
    "reviewer_reviewed",
}

RAW_DOCUMENT_FIELD_NAMES = {
    "raw_document_ref",
    "raw_document_refs",
    "raw_document_reference",
    "raw_document_references",
    "raw_document_url",
    "raw_document_urls",
    "raw_body",
    "response_body",
    "raw_html",
    "raw_text",
    "page_source",
    "html_source",
    "body_html",
    "dom_snapshot",
    "archive_artifact_ref",
    "downloaded_document_path",
    "download_path",
    "local_document_path",
    "filesystem_path",
    "absolute_path",
}

PRIVATE_CASE_FACT_FIELD_NAMES = {
    "case_facts",
    "known_facts",
    "private_case_facts",
    "private_facts",
    "user_facts",
    "applicant_facts",
    "property_owner_facts",
    "payment_facts",
    "permit_application_values",
}

PRIVATE_CLASSIFICATIONS = {
    "private",
    "confidential",
    "restricted",
    "account_scoped",
    "authenticated",
    "devhub_authenticated",
    "case_specific",
}

LIVE_CRAWL_VALUES = {
    "live",
    "live_crawl",
    "live-public-crawl",
    "browser_live_crawl",
    "playwright_live_crawl",
}


@dataclass(frozen=True)
class RegenerationQueueItem:
    queue_item_id: str
    source_id: str
    source_url: str
    change_kinds: tuple[str, ...]
    affected_requirement_ids: tuple[str, ...]
    affected_process_model_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    human_review_owners: tuple[str, ...]
    required_synthetic_fixtures: tuple[str, ...]
    blocked_downstream_activation: bool
    reviewer_acknowledgement_required: bool
    activation_block_reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "queue_item_id": self.queue_item_id,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "change_kinds": list(self.change_kinds),
            "affected_requirement_ids": list(self.affected_requirement_ids),
            "affected_process_model_ids": list(self.affected_process_model_ids),
            "affected_guardrail_bundle_ids": list(self.affected_guardrail_bundle_ids),
            "human_review_owners": list(self.human_review_owners),
            "required_synthetic_fixtures": list(self.required_synthetic_fixtures),
            "blocked_downstream_activation": self.blocked_downstream_activation,
            "reviewer_acknowledgement_required": self.reviewer_acknowledgement_required,
            "activation_block_reason": self.activation_block_reason,
        }


@dataclass(frozen=True)
class RegenerationQueueValidationIssue:
    code: str
    message: str
    location: str


@dataclass(frozen=True)
class RegenerationQueueValidationResult:
    ready: bool
    issues: tuple[RegenerationQueueValidationIssue, ...]

    def messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues)


class RegenerationQueueValidationError(ValueError):
    """Raised when a requirement regeneration queue plan is not acceptable."""

    def __init__(self, issues: Sequence[RegenerationQueueValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(issue.message for issue in self.issues))


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def build_regeneration_queue(
    recrawl_rehearsal_plan: dict[str, Any],
    freshness_drift_digest: dict[str, Any],
    source_dependency_index: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic regeneration queue items from fixture dictionaries."""

    rehearsal_sources = _index_sources(recrawl_rehearsal_plan.get("sources", []))
    dependency_sources = source_dependency_index.get("sources", {})
    changed_sources = _changed_sources(freshness_drift_digest)

    items: list[RegenerationQueueItem] = []
    for source_id in sorted(changed_sources):
        drift = changed_sources[source_id]
        dependencies = dependency_sources.get(source_id, {})
        source_url = str(
            drift.get("canonical_url")
            or rehearsal_sources.get(source_id, {}).get("canonical_url")
            or dependencies.get("canonical_url")
            or ""
        )
        change_kinds = _sorted_strings(drift.get("change_kinds", []))
        owners = _sorted_strings(dependencies.get("human_review_owners", []))
        if not owners:
            owners = ("ppd-requirements-review",)

        required_fixtures = _required_fixtures(source_id, change_kinds, dependencies)
        blocked = bool(change_kinds) or bool(dependencies.get("guardrail_bundle_ids"))
        reason = (
            "reviewer_acknowledgement_required_before_guardrail_or_process_activation"
            if blocked
            else "no_downstream_activation_block_required"
        )
        items.append(
            RegenerationQueueItem(
                queue_item_id=f"regen-{source_id}",
                source_id=source_id,
                source_url=source_url,
                change_kinds=change_kinds,
                affected_requirement_ids=_sorted_strings(dependencies.get("requirement_ids", [])),
                affected_process_model_ids=_sorted_strings(dependencies.get("process_model_ids", [])),
                affected_guardrail_bundle_ids=_sorted_strings(dependencies.get("guardrail_bundle_ids", [])),
                human_review_owners=owners,
                required_synthetic_fixtures=required_fixtures,
                blocked_downstream_activation=blocked,
                reviewer_acknowledgement_required=blocked,
                activation_block_reason=reason,
            )
        )

    return {
        "plan_id": str(recrawl_rehearsal_plan.get("plan_id", "fixture-first-requirement-regeneration")),
        "drift_digest_id": str(freshness_drift_digest.get("digest_id", "unknown-drift-digest")),
        "queue_policy": {
            "fixture_first": True,
            "live_crawl_required": False,
            "blocks_downstream_activation_until_review_acknowledgement": True,
        },
        "queue_items": [item.as_dict() for item in items],
    }


def build_regeneration_queue_from_files(
    recrawl_rehearsal_plan_path: str | Path,
    freshness_drift_digest_path: str | Path,
    source_dependency_index_path: str | Path,
) -> dict[str, Any]:
    return build_regeneration_queue(
        load_json(recrawl_rehearsal_plan_path),
        load_json(freshness_drift_digest_path),
        load_json(source_dependency_index_path),
    )


def validate_requirement_regeneration_queue_plan(plan: Mapping[str, Any]) -> RegenerationQueueValidationResult:
    """Validate a requirement regeneration queue plan before review or activation.

    The validator is intentionally conservative. Regeneration plans may be derived
    from stale or changed public source metadata, but they must not carry private
    case facts, live crawl provenance, raw document references, uncited changed
    source mappings, or downstream activation requests before reviewer review.
    """

    issues: list[RegenerationQueueValidationIssue] = []
    cited_evidence_ids = _collect_cited_evidence_ids(plan)

    mappings = _changed_source_mappings(plan)
    for index, mapping in enumerate(mappings):
        location = mapping.get("__location__", f"changed_source_mappings[{index}]")
        change_kinds = _sorted_strings(mapping.get("change_kinds", []))
        source_id = _clean_string(mapping.get("source_id")) or f"mapping-{index}"
        if not change_kinds and not _truthy(mapping.get("changed")):
            continue

        mapping_evidence_ids = _string_set(
            mapping.get("source_evidence_ids")
            or mapping.get("citation_evidence_ids")
            or mapping.get("citations")
            or mapping.get("source_citations")
        )
        if not mapping_evidence_ids:
            issues.append(
                RegenerationQueueValidationIssue(
                    code="uncited_changed_source_mapping",
                    message=f"changed source mapping {source_id} must cite public source evidence",
                    location=f"{location}.source_evidence_ids",
                )
            )
        elif cited_evidence_ids and not mapping_evidence_ids.issubset(cited_evidence_ids):
            missing = sorted(mapping_evidence_ids - cited_evidence_ids)
            issues.append(
                RegenerationQueueValidationIssue(
                    code="uncited_changed_source_mapping",
                    message=f"changed source mapping {source_id} cites evidence not present in the plan: {', '.join(missing)}",
                    location=f"{location}.source_evidence_ids",
                )
            )

        _require_affected_links(mapping, location, source_id, issues)
        _validate_stale_current_source(mapping, location, issues)
        _validate_downstream_activation(mapping, location, issues)

    _validate_stale_current_source(plan, "$", issues)
    _validate_downstream_activation(plan, "$", issues)
    _validate_recursive_plan_fields(plan, "$", issues)

    return RegenerationQueueValidationResult(ready=not issues, issues=tuple(issues))


def assert_requirement_regeneration_queue_plan(plan: Mapping[str, Any]) -> None:
    result = validate_requirement_regeneration_queue_plan(plan)
    if not result.ready:
        raise RegenerationQueueValidationError(result.issues)


def _require_affected_links(
    mapping: Mapping[str, Any],
    location: str,
    source_id: str,
    issues: list[RegenerationQueueValidationIssue],
) -> None:
    required_fields = (
        ("affected_requirement_ids", "missing_affected_requirement_links", "affected requirement IDs"),
        ("affected_process_model_ids", "missing_affected_process_links", "affected process model IDs"),
        ("affected_guardrail_bundle_ids", "missing_affected_guardrail_links", "affected guardrail bundle IDs"),
    )
    for field, code, label in required_fields:
        if not _string_set(mapping.get(field)):
            issues.append(
                RegenerationQueueValidationIssue(
                    code=code,
                    message=f"changed source mapping {source_id} must include {label}",
                    location=f"{location}.{field}",
                )
            )


def _validate_stale_current_source(
    value: Any,
    location: str,
    issues: list[RegenerationQueueValidationIssue],
) -> None:
    if isinstance(value, Mapping):
        freshness = _clean_string(value.get("freshness_status") or value.get("source_freshness_status")).lower()
        current_status = _clean_string(
            value.get("cache_status")
            or value.get("current_cache_status")
            or value.get("source_cache_status")
            or value.get("current_status")
        ).lower()
        marked_current = current_status in CURRENT_STATUSES or _truthy(value.get("marked_current")) or _truthy(value.get("current"))
        acknowledged = (
            _truthy(value.get("stale_source_current_acknowledgement"))
            or _truthy(value.get("stale_source_acknowledged"))
            or _truthy(value.get("reviewer_acknowledged_stale_current"))
        )
        if freshness in STALE_FRESHNESS_STATUSES and marked_current and not acknowledged:
            issues.append(
                RegenerationQueueValidationIssue(
                    code="stale_source_marked_current_without_acknowledgement",
                    message="stale source evidence cannot be marked current without reviewer acknowledgement",
                    location=location,
                )
            )
        for key, child in value.items():
            child_location = f"{location}.{key}" if location != "$" else str(key)
            _validate_stale_current_source(child, child_location, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_stale_current_source(child, f"{location}[{index}]", issues)


def _validate_downstream_activation(
    value: Any,
    location: str,
    issues: list[RegenerationQueueValidationIssue],
) -> None:
    if not isinstance(value, Mapping):
        return
    requests_activation = (
        _truthy(value.get("activate_downstream"))
        or _truthy(value.get("downstream_activation"))
        or _truthy(value.get("promote_downstream"))
        or _truthy(value.get("promote_to_active"))
        or _clean_string(value.get("activation_status")).lower() in {"active", "activate", "promoted"}
        or value.get("blocked_downstream_activation") is False
    )
    if requests_activation and not _reviewer_reviewed(value):
        issues.append(
            RegenerationQueueValidationIssue(
                code="downstream_activation_without_reviewer_review",
                message="downstream process or guardrail activation requires reviewer review first",
                location=location,
            )
        )


def _validate_recursive_plan_fields(
    value: Any,
    location: str,
    issues: list[RegenerationQueueValidationIssue],
) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_location = f"{location}.{key_text}" if location != "$" else key_text
            if normalized_key in PRIVATE_CASE_FACT_FIELD_NAMES:
                issues.append(
                    RegenerationQueueValidationIssue(
                        code="private_case_facts",
                        message=f"requirement regeneration plans must not include private case fact field {key_text!r}",
                        location=child_location,
                    )
                )
            if normalized_key in RAW_DOCUMENT_FIELD_NAMES or _looks_like_raw_document_reference(normalized_key, child):
                issues.append(
                    RegenerationQueueValidationIssue(
                        code="raw_document_reference",
                        message=f"requirement regeneration plans must not include raw document reference field {key_text!r}",
                        location=child_location,
                    )
                )
            if normalized_key in {"privacy_classification", "privacy", "data_classification"}:
                classification = _clean_string(child).lower()
                if classification in PRIVATE_CLASSIFICATIONS:
                    issues.append(
                        RegenerationQueueValidationIssue(
                            code="private_case_facts",
                            message=f"private classification {classification!r} is not allowed in regeneration queue plans",
                            location=child_location,
                        )
                    )
            if normalized_key in {"provenance", "provenance_type", "capture_mode", "crawl_mode", "run_mode", "source"}:
                if _contains_live_crawl_value(child):
                    issues.append(
                        RegenerationQueueValidationIssue(
                            code="live_crawl_provenance",
                            message="requirement regeneration plans must use deterministic fixture provenance, not live crawl provenance",
                            location=child_location,
                        )
                    )
            if normalized_key in {"live_crawl_provenance", "from_live_crawl", "live_crawl_required"} and _truthy(child):
                issues.append(
                    RegenerationQueueValidationIssue(
                        code="live_crawl_provenance",
                        message=f"live crawl provenance flag {key_text!r} is not allowed in regeneration queue plans",
                        location=child_location,
                    )
                )
            _validate_recursive_plan_fields(child, child_location, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_recursive_plan_fields(child, f"{location}[{index}]", issues)


def _collect_cited_evidence_ids(plan: Mapping[str, Any]) -> set[str]:
    evidence_ids: set[str] = set()
    for field in ("source_evidence", "source_evidence_records", "citations", "citation_records"):
        value = plan.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    evidence_id = _clean_string(item.get("source_evidence_id") or item.get("evidence_id") or item.get("id"))
                    if evidence_id:
                        evidence_ids.add(evidence_id)
                else:
                    evidence_ids.update(_string_set(item))
        else:
            evidence_ids.update(_string_set(value))
    return evidence_ids


def _changed_source_mappings(plan: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    mappings: list[Mapping[str, Any]] = []
    for field in ("changed_source_mappings", "source_change_mappings", "changed_sources"):
        value = plan.get(field)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    mappings.append({**item, "__location__": f"{field}[{index}]"})
    queue_items = plan.get("queue_items")
    if isinstance(queue_items, list):
        for index, item in enumerate(queue_items):
            if isinstance(item, Mapping):
                mappings.append({**item, "__location__": f"queue_items[{index}]"})
    return tuple(mappings)


def _reviewer_reviewed(value: Mapping[str, Any]) -> bool:
    status = _clean_string(
        value.get("reviewer_review_status")
        or value.get("human_review_status")
        or value.get("review_status")
    ).lower()
    if status in REVIEWED_STATUSES:
        return True
    review = value.get("review")
    if isinstance(review, Mapping):
        review_status = _clean_string(review.get("status") or review.get("review_status") or review.get("human_review_status")).lower()
        return review_status in REVIEWED_STATUSES
    return False


def _contains_live_crawl_value(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in LIVE_CRAWL_VALUES
    if isinstance(value, Mapping):
        return any(_contains_live_crawl_value(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_live_crawl_value(child) for child in value)
    return False


def _index_sources(sources: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    if not isinstance(sources, list):
        return indexed
    for source in sources:
        if isinstance(source, dict) and source.get("source_id"):
            indexed[str(source["source_id"])] = source
    return indexed


def _changed_sources(digest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    changed: dict[str, dict[str, Any]] = {}
    for entry in digest.get("changed_sources", []):
        if not isinstance(entry, dict) or not entry.get("source_id"):
            continue
        change_kinds = set(_sorted_strings(entry.get("change_kinds", [])))
        if entry.get("freshness_status") == "changed" or change_kinds & CONSEQUENTIAL_CHANGE_KINDS:
            changed[str(entry["source_id"])] = entry
    return changed


def _required_fixtures(source_id: str, change_kinds: tuple[str, ...], dependencies: dict[str, Any]) -> tuple[str, ...]:
    explicit = list(_as_strings(dependencies.get("required_synthetic_fixtures", [])))
    inferred: list[str] = []
    for kind in change_kinds:
        inferred.append(f"ppd/tests/fixtures/requirement_regeneration_queue/{source_id}.{kind}.json")
    return _sorted_strings([*explicit, *inferred])


def _sorted_strings(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(sorted(set(_as_strings(values))))


def _as_strings(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if value is not None and str(value)]


def _string_set(value: Any) -> set[str]:
    return {item for item in _string_values(value) if item}


def _string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value.strip()
    elif isinstance(value, Mapping):
        evidence_id = value.get("source_evidence_id") or value.get("evidence_id") or value.get("id")
        if isinstance(evidence_id, str):
            yield evidence_id.strip()
    elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
        for item in value:
            yield from _string_values(item)


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "auto", "automatic", "active", "promote"}
    return bool(value)


def _looks_like_raw_document_reference(key: str, value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    if not text:
        return False
    if key.endswith("path") and (text.startswith("/") or text.startswith("~/") or ":\\" in text):
        return True
    if "raw" in key and (text.endswith(".pdf") or text.endswith(".html") or text.endswith(".warc")):
        return True
    return text.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".warc")) and (
        text.startswith("/") or "/downloads/" in text or "\\downloads\\" in text
    )
