# PP&D Supervisor Operations

This document defines the operator-facing recovery rules for the isolated Portland Permitting & Development daemon workspace. It is intentionally scoped to supervisor and daemon recovery. It does not authorize live DevHub actions, authenticated scraping, official submissions, payments, uploads, cancellations, certifications, or account-management automation.

## Operating Boundary

The PP&D daemon and supervisor may only recover work inside the PP&D implementation boundary. Recovery actions must preserve these invariants:

- Source-controlled changes stay under `ppd/` unless the active task explicitly permits updating `docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md`.
- Private DevHub session files, browser storage state, traces, screenshots, raw crawl responses, downloaded documents, and user-specific artifacts are never created as committed fixtures.
- Public crawler work prefers deterministic fixtures and metadata manifests before any live network request.
- DevHub automation remains attended, user-authorized, and reversible until an explicit gate says otherwise.
- Official or security-sensitive transitions fail closed and require a human handoff unless the exact guarded action has been separately authorized.

## Persistent User-Unit Recovery

When the PP&D daemon is run as a persistent user service, the supervisor should treat service recovery as runtime orchestration, not as permission to broaden task scope.

A persistent user-unit restart is appropriate only when all of the following are true:

- The daemon is stopped, wedged, or stale according to PP&D-local status files.
- No validation, patch application, browser session, crawl, or model subprocess is still actively making progress.
- The selected task can be safely returned to `pending`, parked as stale, or recorded as a durable runtime diagnostic.
- Restarting will not resume a live DevHub browser action, upload, submit, certify, cancel, payment, MFA, CAPTCHA, account-creation, or password-recovery flow.

Before restart, the supervisor should record the recovery reason in PP&D-local daemon state or accepted-work notes when that mechanism is available. The record should identify the prior phase, the task id, the stale timestamp or timeout reason, and whether the next daemon cycle is a retry, a park-and-replenish action, or normal selection of another pending task.

Persistent user-unit recovery must not rely on private browser state. If the previous failure involved authenticated DevHub automation, the next cycle starts from an attended manual handoff or a redacted journal replay state, not from a hidden browser profile or saved credential file.

## Explicit Daemon Resume Gates

The supervisor may resume or restart the daemon only after passing the relevant gate for the last known phase.

### Gate: `idle_or_all_complete`

Resume is allowed when the board has selectable pending work or when an all-complete board has been diagnosed as a planning signal. If the board is complete, the supervisor may append the next deterministic PP&D platform tranche and then restart the daemon with the configured LLM backend. It must not sleep indefinitely while the original PP&D goal still has unfinished crawler, extraction, DevHub-boundary, PDF-draft, or formal-logic work.

### Gate: `calling_llm`

Resume is allowed after a bounded timeout or process-group termination if no JSON proposal was returned. The daemon should record this as a runtime diagnostic, reset the selected task to `pending`, and skip full validation for the empty proposal. The supervisor then decides whether to retry, park the task, or append a narrower deterministic recovery task.

### Gate: `applying_files`

Resume is allowed only after confirming there is no partial patch application still in progress. If a proposal cannot be applied cleanly, the daemon records the failed patch, restores the selected task to a safe state, and validates only the repository state that remains. The supervisor may then request a smaller proposal for the same task.

### Gate: `validating`

Resume is allowed after validation has completed, timed out, or been terminated as a process group. Failed validation keeps the selected task incomplete. The daemon must not mark task-board checkboxes complete unless the implementation, fixtures, and validation for that task are present and passing.

### Gate: `live_public_crawl`

Resume is allowed only for explicitly live-enabled public crawl commands that have bounded seed counts, allowlist checks, robots preflight, and metadata-only persistence. A recovery restart must not persist raw response bodies or downloaded public documents as a side effect.

### Gate: `attended_devhub`

Resume is allowed only into an attended worker state that requires the user to be present, review the current screen, and approve the next reversible draft action. The daemon must not silently continue from a saved authenticated browser context. Journal replay may restore redacted transition metadata, but it must not restore selectors, filled values, local file paths, screenshots, traces, storage state, or exact confirmation phrases.

## No Live DevHub Or Official-Action Side Effects

The supervisor and daemon may prepare fixtures, redacted journals, guardrail predicates, local draft-fill previews, and metadata-only manifests. They may not perform live official actions as part of autonomous recovery.

The following actions are always blocked for unattended daemon or supervisor recovery:

- CAPTCHA or MFA automation.
- Account creation, password recovery, or credential changes.
- Uploading application materials or correction files.
- Submitting, certifying, signing, withdrawing, cancelling, or otherwise finalizing an application.
- Scheduling inspections as an official portal action.
- Entering payment details, reviewing fees for payment, or making a payment.
- Persisting private DevHub browser state, traces, screenshots, raw form values, or downloaded user documents.

A DevHub step may proceed only as a manual handoff or an attended worker action when the current implementation requires all applicable evidence: user presence, source evidence ids, selector confidence, a preview or dry run, an audit event, rollback guidance, private-artifact checks, and exact confirmation for any guarded transition. After any attempted guarded action, the worker returns to a review-required state and cannot mark the step complete until post-action hardening and user outcome review pass.

## Recovery Outcomes

Each supervisor recovery should end in one of these states:

- `retry_pending`: the same task is safe to retry because no files or side effects were accepted.
- `parked_stale`: the task is stale relative to newer PP&D capabilities and has been parked with a diagnostic.
- `replenished`: the board was complete or stale, so the supervisor appended deterministic next-tranche work.
- `accepted_after_validation`: the daemon accepted a proposal only after validation passed.
- `manual_handoff`: further progress requires a user-attended browser, credential, payment, upload, certification, cancellation, or other official-action decision.

Any ambiguous recovery state should fail closed as `manual_handoff` or `retry_pending`. The supervisor should prefer a smaller deterministic task over broad autonomous changes when the previous failure involved syntax errors, patch application problems, no-file LLM output, or live-boundary uncertainty.
