"""PP&D permit process model data contracts.

These contracts describe source-backed process models only. They do not crawl,
log in to DevHub, submit applications, upload files, pay fees, or execute any
other consequential permitting action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessStageKind(str, Enum):
    PRE_APPLICATION_RESEARCH = "pre_application_research"
    ACCOUNT_SETUP = "account_setup"
    PROPERTY_LOOKUP = "property_lookup"
    PERMIT_TYPE_SELECTION = "permit_type_selection"
    ELIGIBILITY_SCREENING = "eligibility_screening"
    DOCUMENT_PREPARATION = "document_preparation"
    APPLICATION_DATA_ENTRY = "application_data_entry"
    UPLOAD = "upload"
    ACKNOWLEDGMENT_CERTIFICATION = "acknowledgment_certification"
    SUBMISSION = "submission"
    PRESCREEN_INTAKE = "prescreen_intake"
    FEE_PAYMENT = "fee_payment"
    PLAN_REVIEW = "plan_review"
    CORRECTIONS = "corrections"
    APPROVAL_ISSUANCE = "approval_issuance"
    INSPECTIONS = "inspections"
    CLOSEOUT = "closeout"
    CANCELLATION = "cancellation"
    EXPIRATION_EXTENSION_REACTIVATION = "expiration_extension_reactivation"
    OTHER = "other"


class RequiredFactKind(str, Enum):
    PROPERTY = "property"
    APPLICANT = "applicant"
    OWNER = "owner"
    CONTRACTOR = "contractor"
    PROJECT_SCOPE = "project_scope"
    OCCUPANCY_USE = "occupancy_use"
    VALUATION = "valuation"
    LICENSE = "license"
    PRIOR_PERMIT_OR_CASE = "prior_permit_or_case"
    ACKNOWLEDGMENT = "acknowledgment"
    PAYMENT = "payment"
    OTHER = "other"


class RequiredDocumentKind(str, Enum):
    APPLICATION_FORM = "application_form"
    DRAWING_PLAN = "drawing_plan"
    CALCULATION = "calculation"
    REPORT = "report"
    SIGNATURE = "signature"
    LICENSE_PROOF = "license_proof"
    CORRECTION_RESPONSE = "correction_response"
    CHECKSHEET = "checksheet"
    PAYMENT_NOTICE = "payment_notice"
    OTHER = "other"


class ActionGateKind(str, Enum):
    READ_ONLY = "read_only"
    DRAFT_EDIT = "draft_edit"
    OFFICIAL_UPLOAD = "official_upload"
    CERTIFICATION = "certification"
    SUBMISSION = "submission"
    PAYMENT = "payment"
    CANCELLATION = "cancellation"
    INSPECTION_SCHEDULING = "inspection_scheduling"
    OTHER_CONSEQUENTIAL = "other_consequential"


class ActionGateClassification(str, Enum):
    SAFE_READ_ONLY = "safe_read_only"
    REVERSIBLE_DRAFT_EDIT = "reversible_draft_edit"
    POTENTIALLY_CONSEQUENTIAL = "potentially_consequential"
    FINANCIAL = "financial"


@dataclass(frozen=True)
class EvidenceRef:
    source_id: str
    source_url: Optional[str] = None
    anchor_id: Optional[str] = None
    page_number: Optional[int] = None
    captured_at: Optional[str] = None
    note: Optional[str] = None


@dataclass(frozen=True)
class ProcessStage:
    id: str
    name: str
    kind: ProcessStageKind
    sequence: int
    description: str = ""
    entry_conditions: tuple[str, ...] = field(default_factory=tuple)
    exit_conditions: tuple[str, ...] = field(default_factory=tuple)
    next_stage_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RequiredFact:
    id: str
    label: str
    kind: RequiredFactKind
    required: bool
    description: str = ""
    applies_when: tuple[str, ...] = field(default_factory=tuple)
    source_stage_ids: tuple[str, ...] = field(default_factory=tuple)
    validation_hint: Optional[str] = None
    contains_private_or_user_specific_data: bool = True
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RequiredDocument:
    id: str
    name: str
    kind: RequiredDocumentKind
    required: bool
    description: str = ""
    applies_when: tuple[str, ...] = field(default_factory=tuple)
    accepted_file_types: tuple[str, ...] = field(default_factory=tuple)
    source_stage_ids: tuple[str, ...] = field(default_factory=tuple)
    single_pdf_process_role: Optional[str] = None
    requires_signature: bool = False
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ActionGate:
    id: str
    name: str
    kind: ActionGateKind
    classification: ActionGateClassification
    description: str = ""
    required_confirmation: Optional[str] = None
    blocks_until: tuple[str, ...] = field(default_factory=tuple)
    prohibited_without_confirmation: bool = True
    source_stage_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PermitProcess:
    id: str
    name: str
    permit_types: tuple[str, ...]
    source_ids: tuple[str, ...]
    stages: tuple[ProcessStage, ...] = field(default_factory=tuple)
    required_facts: tuple[RequiredFact, ...] = field(default_factory=tuple)
    required_documents: tuple[RequiredDocument, ...] = field(default_factory=tuple)
    action_gates: tuple[ActionGate, ...] = field(default_factory=tuple)
    formal_requirement_ids: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("id is required")
        if not self.name.strip():
            errors.append("name is required")
        if not self.permit_types:
            errors.append("at least one permit_type is required")
        if not self.source_ids:
            errors.append("at least one source_id is required")

        stage_ids = {stage.id for stage in self.stages}
        for stage in self.stages:
            if not stage.id.strip():
                errors.append("stage id is required")
            if not stage.name.strip():
                errors.append(f"stage {stage.id} name is required")
            if stage.sequence < 0:
                errors.append(f"stage {stage.id} sequence must be non-negative")
            for next_stage_id in stage.next_stage_ids:
                if next_stage_id not in stage_ids:
                    errors.append(f"stage {stage.id} references unknown next stage {next_stage_id}")

        for fact in self.required_facts:
            if not fact.id.strip():
                errors.append("required fact id is required")
            if not fact.label.strip():
                errors.append(f"required fact {fact.id} label is required")
            for stage_id in fact.source_stage_ids:
                if stage_id not in stage_ids:
                    errors.append(f"required fact {fact.id} references unknown stage {stage_id}")

        for document in self.required_documents:
            if not document.id.strip():
                errors.append("required document id is required")
            if not document.name.strip():
                errors.append(f"required document {document.id} name is required")
            for stage_id in document.source_stage_ids:
                if stage_id not in stage_ids:
                    errors.append(f"required document {document.id} references unknown stage {stage_id}")

        consequential = {
            ActionGateClassification.POTENTIALLY_CONSEQUENTIAL,
            ActionGateClassification.FINANCIAL,
        }
        for gate in self.action_gates:
            if not gate.id.strip():
                errors.append("action gate id is required")
            if not gate.name.strip():
                errors.append(f"action gate {gate.id} name is required")
            if gate.classification in consequential and not (gate.required_confirmation or "").strip():
                errors.append(f"action gate {gate.id} requires explicit confirmation text")
            if gate.classification in consequential and not gate.prohibited_without_confirmation:
                errors.append(f"action gate {gate.id} must be prohibited without confirmation")
            for stage_id in gate.source_stage_ids:
                if stage_id not in stage_ids:
                    errors.append(f"action gate {gate.id} references unknown stage {stage_id}")

        return errors
