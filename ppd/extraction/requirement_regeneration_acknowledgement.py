"""Validation for requirement regeneration reviewer acknowledgement packets.

The validator is intentionally side-effect free. It accepts already-loaded packet
mappings so callers can use deterministic fixtures before any live crawl or
authenticated automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


RAW_REFERENCE_KEYS = frozenset(
    {
        "raw_document_ref",
        "raw_crawl_ref",
        "raw_html_path",
        "raw_pdf_path",
        "raw_body_path",
        "download_path",
        "crawl_output_path",
        "warc_path",
        "screenshot_path",
        "trace_path",
        "har_path",
        "auth_state_path",
    }
)

RAW_REFERENCE_MARKERS = (
    "raw://",
    "crawl://",
    "/raw/",
    "/crawl/",
    ".warc",
    ".har",
    "trace.zip",
)

PRIVATE_FACT_KEYS = frozenset(
    {
        "case_facts",
        "private_case_facts",
        "known_facts",
        "user_facts",
        "private_values",
        "applicant_facts",
        "property_owner_facts",
        "permit_application_values",
    }
)

DOWNSTREAM_ACTIVATION_KEYS = frozenset(
    {
        "activate_downstream",
        "downstream_activation",
        "publish_guardrails",
        "mark_guardrails_active",
        "activate_guardrail_bundle",
        "enable_agent_use",
        "promote_to_current",
    }
)

ACCEPTED_DECISIONS = frozenset({"accept", "accepted", "approve", "approved"})
STALE_STATUSES = frozenset({"stale", "changed", "expired", "superseded", "unknown"})


@dataclass(frozen=True)
class PacketValidationIssue:
    """A deterministic validation issue for a reviewer acknowledgement packet."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class PacketValidationResult:
    """Validation result returned by ``validate_reviewer_acknowledgement_packet``."""

    accepted: bool
    issues: tuple[PacketValidationIssue, ...]


def validate_reviewer_acknowledgement_packet(packet: Mapping[str, Any]) -> PacketValidationResult:
    """Validate a requirement regeneration reviewer acknowledgement packet.

    The packet is accepted only when it contains queue links, cited source
    decisions, reviewer acknowledgement for stale accepted sources, synthetic
    fixture requirements, no private case facts, no raw crawl/document artifact
    references, and no downstream activation flags.
    """

    issues: list[PacketValidationIssue] = []

    _validate_queue_links(packet, issues)
    _validate_affected_source_decisions(packet, issues)
    _validate_synthetic_fixture_requirements(packet, issues)
    _scan_for_forbidden_content(packet, "$", issues)

    return PacketValidationResult(accepted=not issues, issues=tuple(issues))


def require_reviewer_acknowledgement_packet(packet: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` when a reviewer acknowledgement packet is invalid."""

    result = validate_reviewer_acknowledgement_packet(packet)
    if result.accepted:
        return
    details = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in result.issues)
    raise ValueError(f"invalid requirement regeneration reviewer acknowledgement packet: {details}")


def _validate_queue_links(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    queue_links = packet.get("queue_links")
    if not isinstance(queue_links, Sequence) or isinstance(queue_links, (str, bytes)) or not queue_links:
        issues.append(
            PacketValidationIssue(
                code="missing_queue_links",
                message="reviewer packet must include at least one queue link",
                path="$.queue_links",
            )
        )
        return

    for index, link in enumerate(queue_links):
        path = f"$.queue_links[{index}]"
        if not isinstance(link, Mapping):
            issues.append(PacketValidationIssue("invalid_queue_link", "queue link must be an object", path))
            continue
        href = link.get("href") or link.get("url")
        if not isinstance(href, str) or not href.startswith("https://"):
            issues.append(
                PacketValidationIssue(
                    code="invalid_queue_link",
                    message="queue link must include an https href or url",
                    path=path,
                )
            )
        label = link.get("label") or link.get("queue_id")
        if not isinstance(label, str) or not label.strip():
            issues.append(
                PacketValidationIssue(
                    code="invalid_queue_link",
                    message="queue link must include a non-empty label or queue_id",
                    path=path,
                )
            )


def _validate_affected_source_decisions(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    decisions = packet.get("affected_source_decisions")
    if not isinstance(decisions, Sequence) or isinstance(decisions, (str, bytes)) or not decisions:
        issues.append(
            PacketValidationIssue(
                code="missing_affected_source_decisions",
                message="reviewer packet must include affected source decisions",
                path="$.affected_source_decisions",
            )
        )
        return

    for index, decision in enumerate(decisions):
        path = f"$.affected_source_decisions[{index}]"
        if not isinstance(decision, Mapping):
            issues.append(PacketValidationIssue("invalid_affected_source_decision", "decision must be an object", path))
            continue

        source_id = decision.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            issues.append(
                PacketValidationIssue(
                    code="missing_source_id",
                    message="affected source decision must name a source_id",
                    path=path,
                )
            )

        disposition = decision.get("decision")
        if not isinstance(disposition, str) or not disposition.strip():
            issues.append(
                PacketValidationIssue(
                    code="missing_source_decision",
                    message="affected source decision must include a decision",
                    path=path,
                )
            )

        if not _has_source_citation(decision):
            issues.append(
                PacketValidationIssue(
                    code="uncited_affected_source_decision",
                    message="affected source decision must include source-grounded citation evidence",
                    path=path,
                )
            )

        freshness_status = _normalized_string(decision.get("freshness_status"))
        accepted = _normalized_string(disposition) in ACCEPTED_DECISIONS
        reviewer_ack = decision.get("reviewer_acknowledged_stale_source") is True
        if accepted and freshness_status in STALE_STATUSES and not reviewer_ack:
            issues.append(
                PacketValidationIssue(
                    code="stale_source_accepted_without_reviewer_acknowledgement",
                    message="stale affected sources cannot be accepted without explicit reviewer acknowledgement",
                    path=path,
                )
            )


def _validate_synthetic_fixture_requirements(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    fixtures = packet.get("synthetic_fixture_requirements")
    if not isinstance(fixtures, Sequence) or isinstance(fixtures, (str, bytes)) or not fixtures:
        issues.append(
            PacketValidationIssue(
                code="missing_synthetic_fixture_requirements",
                message="reviewer packet must list synthetic fixture requirements that exercise the regeneration decision",
                path="$.synthetic_fixture_requirements",
            )
        )
        return

    for index, requirement in enumerate(fixtures):
        path = f"$.synthetic_fixture_requirements[{index}]"
        if not isinstance(requirement, Mapping):
            issues.append(PacketValidationIssue("invalid_synthetic_fixture_requirement", "fixture requirement must be an object", path))
            continue
        fixture_id = requirement.get("fixture_id") or requirement.get("requirement_id")
        assertion = requirement.get("assertion") or requirement.get("expected_validation")
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            issues.append(
                PacketValidationIssue(
                    code="invalid_synthetic_fixture_requirement",
                    message="fixture requirement must include fixture_id or requirement_id",
                    path=path,
                )
            )
        if not isinstance(assertion, str) or not assertion.strip():
            issues.append(
                PacketValidationIssue(
                    code="invalid_synthetic_fixture_requirement",
                    message="fixture requirement must include assertion or expected_validation",
                    path=path,
                )
            )


def _scan_for_forbidden_content(value: Any, path: str, issues: list[PacketValidationIssue]) -> None:
    if isinstance(value, Mapping):
        privacy = _normalized_string(value.get("privacy_classification"))
        if privacy in {"private", "restricted", "authenticated", "case_private"}:
            issues.append(
                PacketValidationIssue(
                    code="private_case_facts_present",
                    message="reviewer acknowledgement packets must not include private or authenticated case facts",
                    path=path,
                )
            )

        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_text = str(key)
            normalized_key = key_text.lower()
            if normalized_key in PRIVATE_FACT_KEYS:
                issues.append(
                    PacketValidationIssue(
                        code="private_case_facts_present",
                        message="reviewer acknowledgement packets must not include private case fact fields",
                        path=child_path,
                    )
                )
            if normalized_key in RAW_REFERENCE_KEYS:
                issues.append(
                    PacketValidationIssue(
                        code="raw_document_or_crawl_reference_present",
                        message="reviewer acknowledgement packets must not include raw document, crawl, browser, or auth artifact references",
                        path=child_path,
                    )
                )
            if normalized_key in DOWNSTREAM_ACTIVATION_KEYS:
                issues.append(
                    PacketValidationIssue(
                        code="downstream_activation_flag_present",
                        message="reviewer acknowledgement packets must not activate downstream guardrails or publish state",
                        path=child_path,
                    )
                )
            _scan_for_forbidden_content(child, child_path, issues)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(child, f"{path}[{index}]", issues)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in RAW_REFERENCE_MARKERS):
            issues.append(
                PacketValidationIssue(
                    code="raw_document_or_crawl_reference_present",
                    message="reviewer acknowledgement packets must cite normalized public evidence, not raw crawl or document artifacts",
                    path=path,
                )
            )


def _has_source_citation(decision: Mapping[str, Any]) -> bool:
    citations = decision.get("citations") or decision.get("source_citations") or decision.get("source_evidence_ids")
    if not isinstance(citations, Sequence) or isinstance(citations, (str, bytes)) or not citations:
        return False

    for citation in citations:
        if isinstance(citation, str) and citation.strip():
            return True
        if not isinstance(citation, Mapping):
            continue
        evidence_id = citation.get("evidence_id") or citation.get("source_evidence_id")
        source_id = citation.get("source_id")
        quote = citation.get("quote") or citation.get("normalized_excerpt") or citation.get("citation_span")
        if isinstance(evidence_id, str) and evidence_id.strip():
            return True
        if isinstance(source_id, str) and source_id.strip() and isinstance(quote, str) and quote.strip():
            return True
    return False


def _normalized_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")
