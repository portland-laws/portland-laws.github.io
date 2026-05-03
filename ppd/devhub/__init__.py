"""DevHub workflow modeling and guarded automation helpers.

The modules in this package define recorder, action-classification, and
attended-worker contracts. They do not store credentials, bypass MFA or CAPTCHA,
create accounts, recover passwords, enter payment details, or pay fees.
"""

from .attended_worker import (
    AttendedUserCheckpoint,
    AttendedWorkerDecision,
    AttendedWorkerEventKind,
    AttendedWorkerJournalEntry,
    AttendedWorkerResumeAction,
    AttendedWorkerResumeReport,
    AttendedWorkerResumeState,
    AttendedWorkerStatus,
    AttendedWorkerStep,
    WorkerHardeningReview,
    attempt_attended_step,
    complete_attended_step,
    journal_attended_decision,
    prepare_attended_step,
    record_action_result,
    resume_attended_worker_journal,
    validate_attended_worker_journal,
)
from .action_classifier import classify_workflow_action
from .workflow import (
    DevHubActionKind,
    DevHubField,
    DevHubFieldKind,
    DevHubSelector,
    DevHubSelectorKind,
    DevHubWorkflowAction,
    DevHubWorkflowState,
    DevHubWorkflowStateKind,
)
from .privacy_validation import validate_devhub_fixture_privacy, validate_devhub_fixture_privacy_file

__all__ = [
    "AttendedUserCheckpoint",
    "AttendedWorkerDecision",
    "AttendedWorkerEventKind",
    "AttendedWorkerJournalEntry",
    "AttendedWorkerResumeAction",
    "AttendedWorkerResumeReport",
    "AttendedWorkerResumeState",
    "AttendedWorkerStatus",
    "AttendedWorkerStep",
    "DevHubActionKind",
    "DevHubField",
    "DevHubFieldKind",
    "DevHubSelector",
    "DevHubSelectorKind",
    "DevHubWorkflowAction",
    "DevHubWorkflowState",
    "DevHubWorkflowStateKind",
    "WorkerHardeningReview",
    "attempt_attended_step",
    "classify_workflow_action",
    "complete_attended_step",
    "journal_attended_decision",
    "prepare_attended_step",
    "record_action_result",
    "resume_attended_worker_journal",
    "validate_attended_worker_journal",
    "validate_devhub_fixture_privacy",
    "validate_devhub_fixture_privacy_file",
]
