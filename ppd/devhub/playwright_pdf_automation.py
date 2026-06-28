"""Guarded Playwright and PDF draft automation plans for PP&D.

This module models future automation that can help a user prepare draft form
state and fill local PDF field plans. It deliberately does not launch a live
browser, log in, write private browser state, upload official files, submit
applications, pay fees, certify statements, schedule inspections, or bypass
security challenges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AutomationActionKind(str, Enum):
    OPEN_PUBLIC_GUIDANCE = "open_public_guidance"
    OPEN_USER_AUTHORIZED_DRAFT = "open_user_authorized_draft"
    READ_FORM_STATE = "read_form_state"
    FILL_FIELD = "fill_field"
    FILL_PDF_FIELD = "fill_pdf_field"
    SAVE_DRAFT_PREVIEW = "save_draft_preview"
    OFFICIAL_UPLOAD = "official_upload"
    SUBMIT_APPLICATION = "submit_application"
    PAY_FEE = "pay_fee"
    CERTIFY_STATEMENT = "certify_statement"
    CANCEL_REQUEST = "cancel_request"
    SCHEDULE_INSPECTION = "schedule_inspection"
    MFA = "mfa"
    CAPTCHA = "captcha"
    ACCOUNT_CREATION = "account_creation"


class AutomationDisposition(str, Enum):
    ALLOW_DRAFT = "allow_draft"
    REQUIRE_USER_HANDOFF = "require_user_handoff"
    REFUSE = "refuse"


DRAFT_ALLOWED_ACTIONS = frozenset(
    {
        AutomationActionKind.OPEN_PUBLIC_GUIDANCE,
        AutomationActionKind.OPEN_USER_AUTHORIZED_DRAFT,
        AutomationActionKind.READ_FORM_STATE,
        AutomationActionKind.FILL_FIELD,
        AutomationActionKind.FILL_PDF_FIELD,
        AutomationActionKind.SAVE_DRAFT_PREVIEW,
    }
)

REFUSED_ACTIONS = frozenset(
    {
        AutomationActionKind.OFFICIAL_UPLOAD,
        AutomationActionKind.SUBMIT_APPLICATION,
        AutomationActionKind.PAY_FEE,
        AutomationActionKind.CERTIFY_STATEMENT,
        AutomationActionKind.CANCEL_REQUEST,
        AutomationActionKind.SCHEDULE_INSPECTION,
        AutomationActionKind.MFA,
        AutomationActionKind.CAPTCHA,
        AutomationActionKind.ACCOUNT_CREATION,
    }
)


@dataclass(frozen=True)
class AutomationGate:
    action_kind: AutomationActionKind
    disposition: AutomationDisposition
    reason: str
    exact_confirmation_required: bool
    exact_confirmation_template: Optional[str] = None
    reversible: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.reason.strip():
            errors.append(f"gate {self.action_kind.value} reason is required")
        if self.action_kind in REFUSED_ACTIONS:
            if self.disposition != AutomationDisposition.REFUSE:
                errors.append(f"gate {self.action_kind.value} must refuse official or security-sensitive actions")
            if not self.exact_confirmation_required:
                errors.append(f"gate {self.action_kind.value} must require exact confirmation before human handoff")
            if self.reversible:
                errors.append(f"gate {self.action_kind.value} must not be marked reversible")
        if self.action_kind in DRAFT_ALLOWED_ACTIONS:
            if self.disposition == AutomationDisposition.REFUSE:
                errors.append(f"gate {self.action_kind.value} should not refuse reversible draft work")
            if self.action_kind in {AutomationActionKind.FILL_FIELD, AutomationActionKind.FILL_PDF_FIELD} and not self.reversible:
                errors.append(f"gate {self.action_kind.value} must be reversible")
        return errors


@dataclass(frozen=True)
class PlaywrightSelectorPlan:
    role: str
    accessible_name: str
    label_text: str
    nearby_heading: str
    confidence: float
    source_evidence_ids: tuple[str, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.role.strip():
            errors.append("selector role is required")
        if not self.accessible_name.strip():
            errors.append("selector accessible_name is required")
        if not self.label_text.strip():
            errors.append("selector label_text is required")
        if not self.nearby_heading.strip():
            errors.append("selector nearby_heading is required")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append("selector confidence must be between 0 and 1")
        if self.confidence < 0.85:
            errors.append("selector confidence below 0.85 requires human review before automation")
        if not self.source_evidence_ids:
            errors.append("selector requires source evidence ids")
        return errors


@dataclass(frozen=True)
class PlaywrightActionPlan:
    id: str
    action_kind: AutomationActionKind
    target_url_pattern: str
    selector: Optional[PlaywrightSelectorPlan]
    redacted_fact_id: Optional[str]
    preview_only: bool
    audit_event_kind: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("playwright action id is required")
        if not self.target_url_pattern.startswith("https://"):
            errors.append(f"playwright action {self.id or '<missing>'} target_url_pattern must be https")
        if self.action_kind not in DRAFT_ALLOWED_ACTIONS:
            errors.append(f"playwright action {self.id or '<missing>'} must be draft-allowed")
        if self.action_kind in {AutomationActionKind.FILL_FIELD, AutomationActionKind.FILL_PDF_FIELD} and self.selector is None:
            errors.append(f"playwright action {self.id or '<missing>'} requires a selector")
        if self.selector is not None:
            errors.extend(f"playwright action {self.id}: {error}" for error in self.selector.validate())
        if not self.preview_only:
            errors.append(f"playwright action {self.id or '<missing>'} must be preview_only")
        if not self.audit_event_kind.strip():
            errors.append(f"playwright action {self.id or '<missing>'} requires audit_event_kind")
        return errors


@dataclass(frozen=True)
class PdfFieldPlan:
    field_id: str
    pdf_field_name: str
    redacted_fact_id: str
    value_kind: str
    source_evidence_ids: tuple[str, ...]
    required_for_preview: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.field_id.strip():
            errors.append("pdf field id is required")
        if not self.pdf_field_name.strip():
            errors.append(f"pdf field {self.field_id or '<missing>'} pdf_field_name is required")
        if not self.redacted_fact_id.startswith("fact-"):
            errors.append(f"pdf field {self.field_id or '<missing>'} must reference a redacted fact")
        if self.value_kind not in {"text", "number", "date", "checkbox", "choice"}:
            errors.append(f"pdf field {self.field_id or '<missing>'} value_kind is invalid")
        if not self.source_evidence_ids:
            errors.append(f"pdf field {self.field_id or '<missing>'} requires source evidence ids")
        return errors


@dataclass(frozen=True)
class PdfFillPlan:
    id: str
    source_pdf_url: str
    local_template_ref: str
    output_mode: str
    fill_engine: str
    fields: tuple[PdfFieldPlan, ...]
    preview_only: bool = True
    official_upload_allowed: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("pdf fill plan id is required")
        if not self.source_pdf_url.startswith("https://www.portland.gov/ppd/"):
            errors.append("pdf fill source must be a public PP&D document URL")
        if not self.local_template_ref.startswith("ppd/tests/fixtures/"):
            errors.append("pdf fill local_template_ref must point at a committed fixture template")
        if self.output_mode != "draft_preview_pdf_fields":
            errors.append("pdf fill output_mode must be draft_preview_pdf_fields")
        if self.fill_engine not in {"pypdf", "pdf_field_manifest"}:
            errors.append("pdf fill engine must be pypdf or pdf_field_manifest")
        if not self.preview_only:
            errors.append("pdf fill plan must be preview_only")
        if self.official_upload_allowed:
            errors.append("pdf fill plan must not allow official upload")
        if not self.fields:
            errors.append("pdf fill plan requires fields")
        seen_ids: set[str] = set()
        for field_plan in self.fields:
            if field_plan.field_id in seen_ids:
                errors.append(f"duplicate pdf field id {field_plan.field_id}")
            seen_ids.add(field_plan.field_id)
            errors.extend(field_plan.validate())
        return errors


@dataclass(frozen=True)
class AutonomousInteractionPlan:
    plan_id: str
    user_authorization_required: bool
    live_browser_enabled_by_default: bool
    private_runtime_artifacts_allowed: bool
    playwright_actions: tuple[PlaywrightActionPlan, ...]
    pdf_fill_plans: tuple[PdfFillPlan, ...]
    gates: tuple[AutomationGate, ...]
    redacted_fact_ids: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.plan_id.strip():
            errors.append("interaction plan id is required")
        if not self.user_authorization_required:
            errors.append("interaction plan must require user authorization")
        if self.live_browser_enabled_by_default:
            errors.append("live browser must be disabled by default")
        if self.private_runtime_artifacts_allowed:
            errors.append("private runtime artifacts must not be allowed")
        if not self.redacted_fact_ids:
            errors.append("interaction plan requires redacted fact ids")
        if not self.source_evidence_ids:
            errors.append("interaction plan requires source evidence ids")
        for action in self.playwright_actions:
            errors.extend(action.validate())
            if action.redacted_fact_id is not None and action.redacted_fact_id not in self.redacted_fact_ids:
                errors.append(f"playwright action {action.id} references unknown redacted fact")
        for pdf_plan in self.pdf_fill_plans:
            errors.extend(pdf_plan.validate())
            for field_plan in pdf_plan.fields:
                if field_plan.redacted_fact_id not in self.redacted_fact_ids:
                    errors.append(f"pdf field {field_plan.field_id} references unknown redacted fact")
                missing_evidence = set(field_plan.source_evidence_ids).difference(self.source_evidence_ids)
                if missing_evidence:
                    errors.append(f"pdf field {field_plan.field_id} references unknown evidence ids: {sorted(missing_evidence)}")
        gate_by_kind = {gate.action_kind: gate for gate in self.gates}
        missing_refusals = REFUSED_ACTIONS.difference(gate_by_kind)
        if missing_refusals:
            errors.append(f"interaction plan missing refused action gates: {sorted(action.value for action in missing_refusals)}")
        for gate in self.gates:
            errors.extend(gate.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "planId": self.plan_id,
            "userAuthorizationRequired": self.user_authorization_required,
            "liveBrowserEnabledByDefault": self.live_browser_enabled_by_default,
            "privateRuntimeArtifactsAllowed": self.private_runtime_artifacts_allowed,
            "redactedFactIds": list(self.redacted_fact_ids),
            "sourceEvidenceIds": list(self.source_evidence_ids),
            "playwrightActions": [
                {
                    "id": action.id,
                    "actionKind": action.action_kind.value,
                    "targetUrlPattern": action.target_url_pattern,
                    "selector": None
                    if action.selector is None
                    else {
                        "role": action.selector.role,
                        "accessibleName": action.selector.accessible_name,
                        "labelText": action.selector.label_text,
                        "nearbyHeading": action.selector.nearby_heading,
                        "confidence": action.selector.confidence,
                        "sourceEvidenceIds": list(action.selector.source_evidence_ids),
                    },
                    "redactedFactId": action.redacted_fact_id,
                    "previewOnly": action.preview_only,
                    "auditEventKind": action.audit_event_kind,
                }
                for action in self.playwright_actions
            ],
            "pdfFillPlans": [
                {
                    "id": pdf_plan.id,
                    "sourcePdfUrl": pdf_plan.source_pdf_url,
                    "localTemplateRef": pdf_plan.local_template_ref,
                    "outputMode": pdf_plan.output_mode,
                    "fillEngine": pdf_plan.fill_engine,
                    "previewOnly": pdf_plan.preview_only,
                    "officialUploadAllowed": pdf_plan.official_upload_allowed,
                    "fields": [
                        {
                            "fieldId": field_plan.field_id,
                            "pdfFieldName": field_plan.pdf_field_name,
                            "redactedFactId": field_plan.redacted_fact_id,
                            "valueKind": field_plan.value_kind,
                            "sourceEvidenceIds": list(field_plan.source_evidence_ids),
                            "requiredForPreview": field_plan.required_for_preview,
                        }
                        for field_plan in pdf_plan.fields
                    ],
                }
                for pdf_plan in self.pdf_fill_plans
            ],
            "gates": [
                {
                    "actionKind": gate.action_kind.value,
                    "disposition": gate.disposition.value,
                    "reason": gate.reason,
                    "exactConfirmationRequired": gate.exact_confirmation_required,
                    "exactConfirmationTemplate": gate.exact_confirmation_template,
                    "reversible": gate.reversible,
                }
                for gate in self.gates
            ],
            "notes": list(self.notes),
        }


def build_default_interaction_plan() -> AutonomousInteractionPlan:
    """Return a fixture-first draft automation plan for future agents."""

    evidence = (
        "src-ppd-devhub-guide-submit-application",
        "src-ppd-building-permit-application-pdf",
        "src-ppd-devhub-faqs",
    )
    redacted_facts = (
        "fact-project-address",
        "fact-applicant-name",
        "fact-work-description",
        "fact-building-area",
    )
    selector = PlaywrightSelectorPlan(
        role="textbox",
        accessible_name="Project address",
        label_text="Project address",
        nearby_heading="Location",
        confidence=0.93,
        source_evidence_ids=(evidence[0],),
    )
    actions = (
        PlaywrightActionPlan(
            id="pw-open-user-authorized-draft",
            action_kind=AutomationActionKind.OPEN_USER_AUTHORIZED_DRAFT,
            target_url_pattern="https://devhub.portlandoregon.gov/",
            selector=None,
            redacted_fact_id=None,
            preview_only=True,
            audit_event_kind="draft_navigation_preview",
        ),
        PlaywrightActionPlan(
            id="pw-fill-project-address",
            action_kind=AutomationActionKind.FILL_FIELD,
            target_url_pattern="https://devhub.portlandoregon.gov/",
            selector=selector,
            redacted_fact_id="fact-project-address",
            preview_only=True,
            audit_event_kind="draft_field_preview",
        ),
        PlaywrightActionPlan(
            id="pw-save-draft-preview",
            action_kind=AutomationActionKind.SAVE_DRAFT_PREVIEW,
            target_url_pattern="https://devhub.portlandoregon.gov/",
            selector=None,
            redacted_fact_id=None,
            preview_only=True,
            audit_event_kind="draft_preview_checkpoint",
        ),
    )
    pdf_plan = PdfFillPlan(
        id="pdf-building-permit-application-draft",
        source_pdf_url="https://www.portland.gov/ppd/documents/building-permit-application-building-site-development-demolition-and-zoning-permits/download",
        local_template_ref="ppd/tests/fixtures/forms/building_permit_application_field_contract.json",
        output_mode="draft_preview_pdf_fields",
        fill_engine="pdf_field_manifest",
        fields=(
            PdfFieldPlan(
                field_id="pdf-project-address",
                pdf_field_name="Project address",
                redacted_fact_id="fact-project-address",
                value_kind="text",
                source_evidence_ids=(evidence[1],),
            ),
            PdfFieldPlan(
                field_id="pdf-work-description",
                pdf_field_name="Description of work",
                redacted_fact_id="fact-work-description",
                value_kind="text",
                source_evidence_ids=(evidence[1],),
            ),
            PdfFieldPlan(
                field_id="pdf-building-area",
                pdf_field_name="Existing building area",
                redacted_fact_id="fact-building-area",
                value_kind="number",
                source_evidence_ids=(evidence[1],),
            ),
        ),
    )
    gates = tuple(
        AutomationGate(
            action_kind=kind,
            disposition=AutomationDisposition.ALLOW_DRAFT,
            reason="Reversible draft preview action using redacted user facts.",
            exact_confirmation_required=False,
            reversible=True,
        )
        for kind in sorted(DRAFT_ALLOWED_ACTIONS, key=lambda item: item.value)
    ) + tuple(
        AutomationGate(
            action_kind=kind,
            disposition=AutomationDisposition.REFUSE,
            reason="Official, financial, certification, scheduling, account, or security-sensitive step requires a human handoff.",
            exact_confirmation_required=True,
            exact_confirmation_template=f"I authorize the human checkpoint for {kind.value}.",
            reversible=False,
        )
        for kind in sorted(REFUSED_ACTIONS, key=lambda item: item.value)
    )
    return AutonomousInteractionPlan(
        plan_id="ppd-playwright-pdf-draft-automation-v2",
        user_authorization_required=True,
        live_browser_enabled_by_default=False,
        private_runtime_artifacts_allowed=False,
        playwright_actions=actions,
        pdf_fill_plans=(pdf_plan,),
        gates=gates,
        redacted_fact_ids=redacted_facts,
        source_evidence_ids=evidence,
        notes=(
            "The plan is draft-first and preview-only.",
            "Future live execution must start from a user-authorized session handoff and still stop before official actions.",
        ),
    )


def validate_interaction_plan(plan: AutonomousInteractionPlan) -> list[str]:
    return plan.validate()
