"""Requirement extraction validation contracts for PP&D fixtures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class ExtractedRequirementType(str, Enum):
    OBLIGATION = "obligation"
    PROHIBITION = "prohibition"
    PERMISSION = "permission"
    PRECONDITION = "precondition"
    EXCEPTION = "exception"
    DEADLINE = "deadline"
    DEPENDENCY = "dependency"
    ACTION_GATE = "action_gate"


class RequirementSubject(str, Enum):
    APPLICANT = "applicant"
    PROPERTY_OWNER = "property_owner"
    CONTRACTOR = "contractor"
    PERMIT_TECHNICIAN = "permit_technician"
    REVIEWER = "reviewer"
    AGENT = "agent"
    SYSTEM = "system"


class RequirementFormalizationStatus(str, Enum):
    UNFORMALIZED = "unformalized"
    DRAFT = "draft"
    MACHINE_CHECKED = "machine_checked"
    HUMAN_REVIEW_NEEDED = "human_review_needed"
    HUMAN_REVIEWED = "human_reviewed"
    RETIRED = "retired"


@dataclass(frozen=True)
class RequirementEvidenceRef:
    source_id: str
    source_url: str
    quote: str
    page_number: Optional[int] = None
    anchor_id: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.source_id.strip():
            errors.append("evidence source_id is required")
        if not self.source_url.startswith("https://"):
            errors.append(f"evidence {self.source_id} source_url must be HTTPS")
        if not self.quote.strip():
            errors.append(f"evidence {self.source_id} quote is required")
        if self.page_number is not None and self.page_number < 1:
            errors.append(f"evidence {self.source_id} page_number must be positive")
        return errors


@dataclass(frozen=True)
class ExtractedRequirement:
    requirement_id: str
    type: ExtractedRequirementType
    subject: RequirementSubject
    action: str
    object: str
    conditions: tuple[str, ...] = field(default_factory=tuple)
    deadline_or_temporal_scope: Optional[str] = None
    evidence: tuple[RequirementEvidenceRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    formalization_status: RequirementFormalizationStatus = RequirementFormalizationStatus.UNFORMALIZED
    formalization_notes: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.requirement_id.strip():
            errors.append("requirement_id is required")
        if not self.action.strip():
            errors.append(f"requirement {self.requirement_id} action is required")
        if not self.object.strip():
            errors.append(f"requirement {self.requirement_id} object is required")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append(f"requirement {self.requirement_id} confidence must be between 0 and 1")
        if not self.evidence:
            errors.append(f"requirement {self.requirement_id} evidence is required")
        for item in self.evidence:
            errors.extend(item.validate())
        if self.type in {ExtractedRequirementType.DEADLINE, ExtractedRequirementType.EXCEPTION} and not self.conditions:
            errors.append(f"requirement {self.requirement_id} {self.type.value} must include conditions")
        if self.type == ExtractedRequirementType.DEADLINE and not (self.deadline_or_temporal_scope or "").strip():
            errors.append(f"requirement {self.requirement_id} deadline must include temporal scope")
        if self.formalization_status != RequirementFormalizationStatus.UNFORMALIZED and not (self.formalization_notes or "").strip():
            errors.append(f"requirement {self.requirement_id} formalization notes are required")
        return errors


@dataclass(frozen=True)
class RequirementExtractionFixture:
    fixture_id: str
    process_id: str
    process_name: str
    extracted_at: str
    requirements: tuple[ExtractedRequirement, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.fixture_id.strip():
            errors.append("fixture_id is required")
        if not self.process_id.strip():
            errors.append("process_id is required")
        if not self.process_name.strip():
            errors.append("process_name is required")
        if not self.extracted_at.endswith("Z"):
            errors.append("extracted_at must end in Z")
        if not self.requirements:
            errors.append("at least one requirement is required")

        seen_ids: set[str] = set()
        types_seen: set[ExtractedRequirementType] = set()
        for requirement in self.requirements:
            if requirement.requirement_id in seen_ids:
                errors.append(f"duplicate requirement_id {requirement.requirement_id}")
            seen_ids.add(requirement.requirement_id)
            types_seen.add(requirement.type)
            errors.extend(requirement.validate())

        required_types = {
            ExtractedRequirementType.OBLIGATION,
            ExtractedRequirementType.PRECONDITION,
            ExtractedRequirementType.DEADLINE,
            ExtractedRequirementType.EXCEPTION,
        }
        missing_types = sorted(requirement_type.value for requirement_type in required_types - types_seen)
        if missing_types:
            errors.append(f"missing required requirement types: {', '.join(missing_types)}")
        return errors


def _require_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _optional_str(data: Mapping[str, Any], key: str) -> Optional[str]:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string when present")
    return value


def _str_tuple(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(value)


def evidence_from_dict(data: Mapping[str, Any]) -> RequirementEvidenceRef:
    page_number = data.get("page_number")
    if page_number is None:
        page_number = data.get("pageNumber")
    if page_number is not None and not isinstance(page_number, int):
        raise ValueError("page_number must be an integer when present")
    return RequirementEvidenceRef(
        source_id=_require_str(data, "source_id"),
        source_url=_require_str(data, "source_url"),
        quote=_require_str(data, "quote"),
        page_number=page_number,
        anchor_id=_optional_str(data, "anchor_id"),
    )


def requirement_from_dict(data: Mapping[str, Any]) -> ExtractedRequirement:
    confidence = data.get("confidence")
    if not isinstance(confidence, int | float):
        raise ValueError("confidence must be numeric")
    evidence_value = data.get("evidence")
    if not isinstance(evidence_value, list):
        raise ValueError("evidence must be a list")
    evidence = tuple(evidence_from_dict(item) for item in evidence_value)
    return ExtractedRequirement(
        requirement_id=_require_str(data, "requirement_id"),
        type=ExtractedRequirementType(_require_str(data, "type")),
        subject=RequirementSubject(_require_str(data, "subject")),
        action=_require_str(data, "action"),
        object=_require_str(data, "object"),
        conditions=_str_tuple(data, "conditions"),
        deadline_or_temporal_scope=_optional_str(data, "deadline_or_temporal_scope"),
        evidence=evidence,
        confidence=float(confidence),
        formalization_status=RequirementFormalizationStatus(_require_str(data, "formalization_status")),
        formalization_notes=_optional_str(data, "formalization_notes"),
    )


def fixture_from_dict(data: Mapping[str, Any]) -> RequirementExtractionFixture:
    requirements_value = data.get("requirements")
    if not isinstance(requirements_value, list):
        raise ValueError("requirements must be a list")
    return RequirementExtractionFixture(
        fixture_id=_require_str(data, "fixture_id"),
        process_id=_require_str(data, "process_id"),
        process_name=_require_str(data, "process_name"),
        extracted_at=_require_str(data, "extracted_at"),
        requirements=tuple(requirement_from_dict(item) for item in requirements_value),
    )
