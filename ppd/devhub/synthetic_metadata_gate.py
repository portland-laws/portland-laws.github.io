"""Validation gates for synthetic document metadata in DevHub workflows.

The gate is intentionally side-effect free. It only classifies whether a proposed
agent action may proceed given committed metadata about one or more documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


class DocumentAction(str, Enum):
    """Document-related actions PP&D agents may ask about."""

    LOCAL_PREVIEW = "local_preview"
    MISSING_INFORMATION_PROMPT = "missing_information_prompt"
    UPLOAD_STAGING = "upload_staging"
    CERTIFICATION = "certification"
    SUBMISSION = "submission"


SAFE_WITH_NONCOMPLIANT_SYNTHETIC = frozenset(
    {
        DocumentAction.LOCAL_PREVIEW,
        DocumentAction.MISSING_INFORMATION_PROMPT,
    }
)

CONSEQUENTIAL_SYNTHETIC_ACTIONS = frozenset(
    {
        DocumentAction.UPLOAD_STAGING,
        DocumentAction.CERTIFICATION,
        DocumentAction.SUBMISSION,
    }
)

COMPLIANT_STATUSES = frozenset({"compliant", "verified", "human_verified"})
NONCOMPLIANT_STATUSES = frozenset(
    {
        "noncompliant",
        "missing_provenance",
        "unverified",
        "unknown",
        "failed_validation",
        "stale",
        "conflicting",
    }
)


@dataclass(frozen=True)
class SyntheticDocumentMetadata:
    """Minimal metadata required to evaluate synthetic document safety."""

    document_id: str
    is_synthetic: bool
    compliance_status: str | None = None
    provenance: str | None = None
    source_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    human_review_status: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "SyntheticDocumentMetadata":
        evidence_value = data.get("source_evidence_ids") or data.get("source_evidence_id") or ()
        if isinstance(evidence_value, str):
            evidence_ids = (evidence_value,)
        elif isinstance(evidence_value, Sequence):
            evidence_ids = tuple(str(item) for item in evidence_value if str(item).strip())
        else:
            evidence_ids = ()

        return cls(
            document_id=str(data.get("document_id") or data.get("id") or "unknown-document"),
            is_synthetic=bool(data.get("is_synthetic") or data.get("synthetic")),
            compliance_status=_optional_text(data.get("compliance_status")),
            provenance=_optional_text(data.get("provenance")),
            source_evidence_ids=evidence_ids,
            human_review_status=_optional_text(data.get("human_review_status")),
        )

    @property
    def normalized_status(self) -> str:
        return (self.compliance_status or "unknown").strip().lower()

    @property
    def has_required_provenance(self) -> bool:
        return bool((self.provenance or "").strip()) and bool(self.source_evidence_ids)

    @property
    def is_compliant_for_consequential_action(self) -> bool:
        if not self.is_synthetic:
            return True
        return self.normalized_status in COMPLIANT_STATUSES and self.has_required_provenance

    @property
    def noncompliance_reasons(self) -> tuple[str, ...]:
        if not self.is_synthetic or self.is_compliant_for_consequential_action:
            return ()

        reasons: list[str] = []
        if self.normalized_status not in COMPLIANT_STATUSES:
            if self.normalized_status in NONCOMPLIANT_STATUSES:
                reasons.append(f"synthetic metadata status is {self.normalized_status}")
            else:
                reasons.append("synthetic metadata status is not recognized as compliant")
        if not (self.provenance or "").strip():
            reasons.append("synthetic metadata is missing provenance")
        if not self.source_evidence_ids:
            reasons.append("synthetic metadata is missing source evidence")
        return tuple(reasons)


@dataclass(frozen=True)
class SyntheticMetadataActionDecision:
    """Result of evaluating one proposed document action."""

    allowed: bool
    action: DocumentAction
    blocked_document_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    @property
    def requires_missing_information_prompt(self) -> bool:
        return not self.allowed and bool(self.blocked_document_ids)


def validate_synthetic_document_action(
    metadata: SyntheticDocumentMetadata | Mapping[str, object],
    action: DocumentAction | str,
) -> SyntheticMetadataActionDecision:
    """Validate one document's metadata for a proposed action."""

    document = metadata if isinstance(metadata, SyntheticDocumentMetadata) else SyntheticDocumentMetadata.from_mapping(metadata)
    normalized_action = _coerce_action(action)

    if normalized_action in SAFE_WITH_NONCOMPLIANT_SYNTHETIC:
        return SyntheticMetadataActionDecision(allowed=True, action=normalized_action)

    if normalized_action in CONSEQUENTIAL_SYNTHETIC_ACTIONS and not document.is_compliant_for_consequential_action:
        return SyntheticMetadataActionDecision(
            allowed=False,
            action=normalized_action,
            blocked_document_ids=(document.document_id,),
            reasons=document.noncompliance_reasons,
        )

    return SyntheticMetadataActionDecision(allowed=True, action=normalized_action)


def validate_synthetic_document_set_action(
    documents: Sequence[SyntheticDocumentMetadata | Mapping[str, object]],
    action: DocumentAction | str,
) -> SyntheticMetadataActionDecision:
    """Validate a batch of documents and block if any synthetic item is unsafe."""

    normalized_action = _coerce_action(action)
    blocked_ids: list[str] = []
    reasons: list[str] = []

    for item in documents:
        decision = validate_synthetic_document_action(item, normalized_action)
        blocked_ids.extend(decision.blocked_document_ids)
        reasons.extend(decision.reasons)

    if blocked_ids:
        return SyntheticMetadataActionDecision(
            allowed=False,
            action=normalized_action,
            blocked_document_ids=tuple(blocked_ids),
            reasons=tuple(dict.fromkeys(reasons)),
        )

    return SyntheticMetadataActionDecision(allowed=True, action=normalized_action)


def _coerce_action(action: DocumentAction | str) -> DocumentAction:
    if isinstance(action, DocumentAction):
        return action
    try:
        return DocumentAction(str(action))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in DocumentAction)
        raise ValueError(f"Unsupported document action {action!r}; expected one of: {allowed}") from exc


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
