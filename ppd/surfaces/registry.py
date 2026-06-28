"""Canonical PP&D website/process surface registry.

This registry is side-effect free. It does not crawl, launch Playwright, log in,
upload, submit, pay, or fill PDFs. It gives agents a single contract for which
PP&D surface they are touching and which local executor plus guardrails must be
used before that surface can advance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ppd.devhub.live_action_executor import LiveDevHubActionKind


class SurfaceKind(str, Enum):
    PUBLIC_GUIDANCE = "public_guidance"
    PUBLIC_SEARCH_STATUS = "public_search_status"
    PROCESSOR_ARCHIVE = "processor_archive"
    REQUIREMENT_LOGIC = "requirement_logic"
    USER_DOCUMENT_FACTS = "user_document_facts"
    PDF_DRAFT_FILL = "pdf_draft_fill"
    DEVHUB_LOGIN = "devhub_login"
    DEVHUB_DRAFT = "devhub_draft"
    DEVHUB_UPLOAD = "devhub_upload"
    DEVHUB_SUBMISSION = "devhub_submission"
    DEVHUB_PAYMENT = "devhub_payment"
    DEVHUB_INSPECTION = "devhub_inspection"
    DEVHUB_MESSAGES_CHECKSHEETS = "devhub_messages_checksheets"
    DEVHUB_SECURITY_HANDOFF = "devhub_security_handoff"
    COMPLETION_EVIDENCE = "completion_evidence"


class AutomationMode(str, Enum):
    PUBLIC_READ_ONLY = "public_read_only"
    LOCAL_DRAFT_ONLY = "local_draft_only"
    ATTENDED_REVERSIBLE = "attended_reversible"
    ATTENDED_EXACT_CONFIRMATION = "attended_exact_confirmation"
    MANUAL_HANDOFF = "manual_handoff"
    REFUSED_BY_DEFAULT = "refused_by_default"


@dataclass(frozen=True)
class PpdSurfaceBinding:
    surface: SurfaceKind
    display_name: str
    automation_mode: AutomationMode
    modules: tuple[str, ...]
    devhub_actions: tuple[LiveDevHubActionKind, ...] = ()
    required_guardrails: tuple[str, ...] = ()
    completion_rule: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "surface": self.surface.value,
            "displayName": self.display_name,
            "automationMode": self.automation_mode.value,
            "modules": list(self.modules),
            "devhubActions": [action.value for action in self.devhub_actions],
            "requiredGuardrails": list(self.required_guardrails),
            "completionRule": self.completion_rule,
        }


PUBLIC_GUARDRAILS = (
    "public allowlist",
    "robots preflight",
    "bounded timeout",
    "processor-suite handoff",
    "no raw response persistence",
)

ATTENDED_GUARDRAILS = (
    "user present",
    "screen reviewed",
    "source evidence ids",
    "selector confidence",
    "preview or dry-run",
    "audit event",
    "rollback plan",
    "no private artifacts persisted",
)

OFFICIAL_GUARDRAILS = ATTENDED_GUARDRAILS + (
    "exact action confirmation",
    "post-action hardening",
    "user outcome review",
    "completion evidence ids",
)


def ppd_surface_registry() -> tuple[PpdSurfaceBinding, ...]:
    return (
        PpdSurfaceBinding(
            surface=SurfaceKind.PUBLIC_GUIDANCE,
            display_name="Public PP&D guidance, forms pages, handouts, and PDFs",
            automation_mode=AutomationMode.PUBLIC_READ_ONLY,
            modules=("ppd.crawler.live_public_preflight", "ppd.crawler.live_public_scrape"),
            required_guardrails=PUBLIC_GUARDRAILS,
            completion_rule="source discovery is complete only after processor handoff metadata exists",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.PUBLIC_SEARCH_STATUS,
            display_name="Public permit search and status references",
            automation_mode=AutomationMode.PUBLIC_READ_ONLY,
            modules=("ppd.crawler.public_dry_run", "ppd.contracts.frontier_checkpoint"),
            required_guardrails=PUBLIC_GUARDRAILS + ("redacted status identifiers",),
            completion_rule="status evidence must be linked to source ids and contain no private account values",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.PROCESSOR_ARCHIVE,
            display_name="ipfs_datasets_py processor archive and normalization handoff",
            automation_mode=AutomationMode.PUBLIC_READ_ONLY,
            modules=("ppd.crawler.archive_adapter_preflight", "ppd.contracts.crawl_processor_handoff"),
            required_guardrails=("processor metadata available", "content-hash placeholder", "no raw body manifest"),
            completion_rule="archive manifests must precede requirement extraction and formal logic export",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.REQUIREMENT_LOGIC,
            display_name="Requirement extraction and formal-logic guardrails",
            automation_mode=AutomationMode.LOCAL_DRAFT_ONLY,
            modules=("ppd.logic.guardrail_compiler", "ppd.logic.requirement_process_dependency_graph"),
            required_guardrails=("source evidence ids", "missing-fact questions", "exact-confirmation predicates"),
            completion_rule="guardrails are complete only when obligations and stop gates cite processor-backed evidence",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.USER_DOCUMENT_FACTS,
            display_name="User document-store facts and missing information",
            automation_mode=AutomationMode.LOCAL_DRAFT_ONLY,
            modules=("ppd.logic.missing_information_response_plan",),
            required_guardrails=("redacted facts", "missing fact prompts", "conflict review"),
            completion_rule="facts may fill drafts only after provenance, freshness, and conflict checks pass",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.PDF_DRAFT_FILL,
            display_name="Local PP&D PDF draft field filling",
            automation_mode=AutomationMode.LOCAL_DRAFT_ONLY,
            modules=("ppd.pdf.draft_fill", "ppd.devhub.playwright_pdf_automation"),
            required_guardrails=("local draft output only", "field manifest", "redacted user facts", "no upload"),
            completion_rule="PDF steps produce previews; upload remains a separate attended official surface",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_LOGIN,
            display_name="DevHub login and browser handoff",
            automation_mode=AutomationMode.MANUAL_HANDOFF,
            modules=("ppd.devhub.attended_worker", "ppd.devhub.live_action_executor"),
            devhub_actions=(LiveDevHubActionKind.USER_LOGIN_HANDOFF,),
            required_guardrails=("manual login", "no credential storage", "no MFA or CAPTCHA automation"),
            completion_rule="login is never completed by the agent; the user controls authenticated handoff",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_DRAFT,
            display_name="DevHub reversible draft form reads, fills, and saves",
            automation_mode=AutomationMode.ATTENDED_REVERSIBLE,
            modules=("ppd.devhub.attended_worker", "ppd.devhub.live_action_executor"),
            devhub_actions=(
                LiveDevHubActionKind.READ_FORM_STATE,
                LiveDevHubActionKind.FILL_FIELD,
                LiveDevHubActionKind.SAVE_DRAFT,
            ),
            required_guardrails=ATTENDED_GUARDRAILS,
            completion_rule="draft work cannot mark a process complete; it creates reviewable draft state only",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_UPLOAD,
            display_name="DevHub official document upload",
            automation_mode=AutomationMode.ATTENDED_EXACT_CONFIRMATION,
            modules=("ppd.devhub.attended_worker", "ppd.devhub.live_action_executor"),
            devhub_actions=(LiveDevHubActionKind.OFFICIAL_UPLOAD,),
            required_guardrails=OFFICIAL_GUARDRAILS + ("user-selected local file",),
            completion_rule="upload attempts remain review-required until post-action evidence and user outcome review pass",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_SUBMISSION,
            display_name="DevHub submission, certification, cancellation, and lifecycle transitions",
            automation_mode=AutomationMode.ATTENDED_EXACT_CONFIRMATION,
            modules=("ppd.devhub.attended_worker", "ppd.devhub.live_action_executor"),
            devhub_actions=(
                LiveDevHubActionKind.SUBMIT_APPLICATION,
                LiveDevHubActionKind.CERTIFY_STATEMENT,
                LiveDevHubActionKind.CANCEL_REQUEST,
            ),
            required_guardrails=OFFICIAL_GUARDRAILS,
            completion_rule="official transitions are attempted only with exact confirmation and finish only after hardening review",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_PAYMENT,
            display_name="DevHub fee and payment review",
            automation_mode=AutomationMode.MANUAL_HANDOFF,
            modules=("ppd.devhub.fee_review_guardrails", "ppd.devhub.live_action_executor"),
            devhub_actions=(
                LiveDevHubActionKind.OPEN_PAYMENT_REVIEW,
                LiveDevHubActionKind.PAY_FEE,
                LiveDevHubActionKind.ENTER_PAYMENT_DETAILS,
            ),
            required_guardrails=("fee notice evidence", "payment-specific confirmation", "manual payment entry"),
            completion_rule="agents may open/review fee context when confirmed, but final payment and payment details remain manual",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_INSPECTION,
            display_name="DevHub inspection scheduling and related official actions",
            automation_mode=AutomationMode.ATTENDED_EXACT_CONFIRMATION,
            modules=("ppd.devhub.attended_worker", "ppd.devhub.live_action_executor"),
            devhub_actions=(LiveDevHubActionKind.SCHEDULE_INSPECTION,),
            required_guardrails=OFFICIAL_GUARDRAILS,
            completion_rule="inspection scheduling requires exact confirmation and post-action outcome review",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_MESSAGES_CHECKSHEETS,
            display_name="DevHub messages, checksheets, corrections, and outstanding tasks",
            automation_mode=AutomationMode.ATTENDED_REVERSIBLE,
            modules=("ppd.devhub.attended_worker", "ppd.devhub.workflow"),
            required_guardrails=ATTENDED_GUARDRAILS + ("redacted message/task summary",),
            completion_rule="message/checksheet handling produces review packets before official response actions",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.DEVHUB_SECURITY_HANDOFF,
            display_name="DevHub security, account creation, and recovery challenges",
            automation_mode=AutomationMode.REFUSED_BY_DEFAULT,
            modules=("ppd.devhub.live_action_executor",),
            devhub_actions=(
                LiveDevHubActionKind.MFA,
                LiveDevHubActionKind.CAPTCHA,
                LiveDevHubActionKind.ACCOUNT_CREATION,
                LiveDevHubActionKind.PASSWORD_RECOVERY,
            ),
            required_guardrails=("manual user control", "no automation", "no credential capture"),
            completion_rule="security and account recovery surfaces are always manual handoff",
        ),
        PpdSurfaceBinding(
            surface=SurfaceKind.COMPLETION_EVIDENCE,
            display_name="Completion evidence and audit closeout",
            automation_mode=AutomationMode.LOCAL_DRAFT_ONLY,
            modules=("ppd.devhub.attended_worker", "ppd.logic.guardrail_compiler"),
            required_guardrails=("completion evidence ids", "side-effect review", "user outcome review"),
            completion_rule="a process can close only after every attempted official surface has post-action hardening",
        ),
    )


def binding_for_devhub_action(action_kind: LiveDevHubActionKind) -> PpdSurfaceBinding:
    for binding in ppd_surface_registry():
        if action_kind in binding.devhub_actions:
            return binding
    raise KeyError(f"unmapped DevHub action: {action_kind.value}")


def build_agentic_completion_contract() -> dict[str, object]:
    """Return the high-level process contract agents must follow."""

    ordered_surfaces = [
        SurfaceKind.PUBLIC_GUIDANCE,
        SurfaceKind.PROCESSOR_ARCHIVE,
        SurfaceKind.REQUIREMENT_LOGIC,
        SurfaceKind.USER_DOCUMENT_FACTS,
        SurfaceKind.PDF_DRAFT_FILL,
        SurfaceKind.DEVHUB_LOGIN,
        SurfaceKind.DEVHUB_DRAFT,
        SurfaceKind.DEVHUB_MESSAGES_CHECKSHEETS,
        SurfaceKind.DEVHUB_UPLOAD,
        SurfaceKind.DEVHUB_PAYMENT,
        SurfaceKind.DEVHUB_SUBMISSION,
        SurfaceKind.DEVHUB_INSPECTION,
        SurfaceKind.COMPLETION_EVIDENCE,
    ]
    registry = {binding.surface: binding for binding in ppd_surface_registry()}
    return {
        "schemaVersion": 1,
        "processGoal": "assist a user through PP&D permitting without skipping evidence, attendance, or exact-confirmation gates",
        "orderedSurfaces": [surface.value for surface in ordered_surfaces],
        "surfaceBindings": [registry[surface].to_dict() for surface in ordered_surfaces],
        "completionRule": (
            "No PP&D process is complete merely because an agent drafted, clicked, uploaded, "
            "submitted, scheduled, or opened payment review. Completion requires source-backed "
            "guardrails, attended attempts for live surfaces, post-action hardening, user outcome "
            "review, and completion evidence ids."
        ),
    }
