# Portland PP&D Scraping, DevHub Automation, and Formal Guardrails Plan

Status: implementation plan and daemon handoff
Last verified against official public sources: 2026-05-08
Primary workspace: `ppd/`

## Purpose

Build a compliant, source-grounded implementation for Portland Permitting & Development (PP&D) that can:

- Archive and normalize the public PP&D website, forms, PDFs, permit guides, and DevHub help material.
- Support attended DevHub login and browser automation for user-owned sessions.
- Extract legal, procedural, document, fee, deadline, and UI-action requirements from public sources and observed DevHub workflows.
- Compile those requirements into formal guardrails that LLM agents can use before asking a user for missing facts or proposing a next action.
- Let agents autonomously assist with safe read-only and reversible draft work while stopping before consequential actions until the user is present, informed, and has confirmed the exact action.

The intended user experience is not "the agent guesses how permitting works." The intended experience is:

1. The agent loads a cited PP&D process model.
2. The agent compares that model to the user's document store and known case facts.
3. The agent asks only for missing, stale, ambiguous, or conflicting facts.
4. The agent drafts reversible form/PDF values when the facts are sufficient.
5. The agent blocks or escalates any official action that requires attendance, certification, upload, submission, scheduling, cancellation, or payment.

## Official Source Anchors

The first crawl and source registry should start from these official public entry points:

- PP&D bureau landing page: `https://www.portland.gov/ppd`
- Online permitting tools overview: `https://www.portland.gov/ppd/how-use-online-permitting-tools`
- DevHub public portal: `https://devhub.portlandoregon.gov`
- DevHub FAQ: `https://www.portland.gov/ppd/devhub-faqs`
- DevHub account and sign-in guide: `https://www.portland.gov/ppd/devhub-sign-guide`
- Apply for permits: `https://www.portland.gov/ppd/get-permit/apply-permits`
- DevHub permit application guide: `https://www.portland.gov/ppd/devhub-guide-submit-permit-application`
- Submit Plans Online / Single PDF Process: `https://www.portland.gov/ppd/get-permit/submit-plans-online`
- Permit applications and forms index: `https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications`
- File naming standards and PDF preparation: `https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs`
- Fee payment guide: `https://www.portland.gov/ppd/documents/how-pay-fees/download`
- Portland Maps public references where linked from PP&D guidance: `https://www.portlandmaps.com`

Source facts verified on 2026-05-08:

- PP&D manages building permits, land use, inspections, code enforcement, and public works permits.
- DevHub is the City of Portland's online permitting system.
- DevHub supports account-based workflows including applying for permits, paying fees, scheduling inspections, uploading corrections, and checking requests.
- DevHub uses PortlandOregon.gov credentials for authenticated online permitting services.
- Official guidance distinguishes permit requests requiring plan review from standard trade permits that may be purchased through DevHub.
- The DevHub permit application guide lists building, new single-family residence and detached ADU, solar, FCC wireless, demolition, trade, trade-with-plan-review, sign, and Urban Forestry request types.
- Permit applications can include dynamic questions, save-for-later behavior, required uploads, acknowledgement/certification, and post-submission status tracking.
- Some permit types must be submitted by email or other paths, so DevHub cannot be assumed to cover every permit.
- Single PDF guidance requires drawing plans together in one PDF, with applications, calculations, and other supporting documents uploaded as separate PDFs.
- Fee payment is a financial workflow and includes payment detail entry and a final submit-payment action. These actions require separate guardrails.

Verification notes from official pages:

- The PP&D landing page identifies PP&D's scope and links first-party entry points for permit need checks, building permit guidance, permit applications, status checks, fee payment, inspections, codes, and related PP&D programs.
- The online permitting tools page identifies DevHub as the City of Portland's online permitting system and links step-by-step guides for permit requests, standard trade permits, tree permits, solar permits, fee payment, inspection scheduling, and account/sign-in workflows.
- The DevHub account/sign-in guide states that a DevHub user account with PortlandOregon.gov credentials is required for online permitting services, and its steps include going to DevHub, selecting Sign In/Register, and using the PortlandOregon.gov sign-in flow.
- The DevHub FAQ lists account-scoped services including purchasing standard permits not requiring plan review, submitting permit requests requiring plan review, scheduling trade-permit inspections, uploading corrections, and paying fees.
- The standard trade permit guide notes that contractor license data on the DevHub profile can affect available fixture options, so agent gap analysis must check license-related facts before assuming a draft is ready.
- The upload-corrections guide treats correction upload as an authenticated DevHub workflow with permit/Application number or IVR lookup and review-group status checks, so uploads remain consequential and exact-confirmation gated.

## Non-Negotiable Boundaries

- Respect robots directives, allowlists, terms, authentication boundaries, rate limits, copyright constraints, and privacy limits.
- Do not bypass MFA, CAPTCHA, bot defenses, access controls, paywalls, account boundaries, or rate limits.
- Do not store credentials, session state, screenshots, traces, HAR files, payment details, private uploads, local private file paths, or raw authenticated page values in committed artifacts.
- Do not automate account creation, password recovery, MFA enrollment, CAPTCHA, payment-detail entry, or final payment execution.
- Do not upload, submit, certify, cancel, schedule inspections, or make official changes without explicit user attendance and action-specific confirmation.
- Do not mark a workflow step complete merely because Playwright clicked or filled something. Completion requires post-action review, source-backed evidence, and user-visible outcome confirmation.
- Public crawls may store metadata manifests, normalized public text, checksums, and citations. Raw body persistence must be explicitly justified and kept out of git.
- Authenticated DevHub automation is account-scoped user assistance, not bulk scraping of private data.

## Repository Boundary

All implementation should live in `ppd/` unless a small root-level integration hook is explicitly required.

Use the existing `ipfs_datasets_py` submodule as a dependency, especially its processor and web archival capabilities. PP&D code should wrap those processors through local policy adapters rather than rewriting archival, WARC, PDF, GraphRAG, serialization, or dataset tooling.

Allowed write areas:

- `docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md`
- `ppd/`
- future root-level config only if needed to run PP&D validation

Disallowed default write areas:

- `src/lib/logic/`
- `public/corpus/portland-or/current/`
- `ipfs_datasets_py/.daemon/`
- private DevHub/session/browser artifacts
- raw downloaded public or private data unless ignored and explicitly part of a local run

## Target Architecture

```text
Official public source seeds
  -> PP&D allowlist / robots / policy preflight
  -> ipfs_datasets_py processor archival suite
  -> archive manifests and normalized document records
  -> HTML / PDF / form extraction
  -> source index and source freshness monitor
  -> requirement extraction
  -> permit process models
  -> formal guardrail compiler
  -> agent-facing missing-information and action-validation APIs

Attended DevHub browser session
  -> manual login handoff
  -> Playwright state recorder
  -> redacted form and action manifests
  -> reversible draft-fill executor
  -> exact-confirmation checkpoints
  -> attended worker journal
  -> post-action hardening review
```

## PP&D Package Layout

The current implementation should align with the Python-first `ppd/` package already present in this repository:

```text
ppd/
  contracts/       source, process, archive, PDF, DevHub, and requirement contracts
  crawler/         public crawl frontier, live dry-run, processor handoff
  daemon/          task board, supervisor, deterministic fallback, operations
  devhub/          Playwright, attended worker, action classification, guardrails
  extraction/      public HTML/PDF requirement extraction and freshness reports
  logic/           guardrail compiler and process dependency graph
  pdf/             local PDF draft-fill utilities
  platform/        side-effect-free platform capability contracts
  processor_suite/ processor integration plans
  surfaces/        surface registry and action policy
  tests/           committed fixtures and validation tests
```

## Core Data Products

### SourceRegistry

Fields:

- `source_id`
- `canonical_url`
- `source_type`: public_html, public_pdf, public_form, devhub_public, devhub_authenticated, external_reference
- `owning_surface`
- `allowlist_policy`
- `robots_policy`
- `crawl_frequency`
- `processor_policy`
- `privacy_classification`
- `last_seen_at`
- `freshness_status`

### ArchiveManifest

Fields:

- `manifest_id`
- `source_id`
- `canonical_url`
- `requested_url`
- `redirect_chain`
- `http_status`
- `content_type`
- `content_hash`
- `capture_started_at`
- `capture_finished_at`
- `processor_name`
- `processor_version`
- `archive_artifact_ref`
- `normalized_document_id`
- `skipped_reason`
- `no_raw_body_persisted`

### DocumentRecord

Fields:

- `document_id`
- `source_id`
- `title`
- `document_type`
- `language`
- `sections`
- `tables`
- `links`
- `pdf_pages`
- `form_fields`
- `citation_spans`
- `content_hash`
- `extraction_confidence`

### RequirementNode

Fields:

- `requirement_id`
- `source_evidence_ids`
- `requirement_type`: obligation, prohibition, permission, precondition, exception, deadline, fee_trigger, license_requirement, document_requirement, action_gate
- `subject`
- `action`
- `object`
- `conditions`
- `deadline_or_temporal_scope`
- `permit_types`
- `process_stage`
- `confidence`
- `human_review_status`
- `formalization_status`

### ProcessModel

Fields:

- `process_id`
- `permit_type`
- `scope`
- `eligibility_rules`
- `required_user_facts`
- `required_documents`
- `file_rules`
- `fees`
- `stages`
- `deadlines`
- `exceptions`
- `unsupported_paths`
- `devhub_surface_refs`
- `guardrail_bundle_id`

Standard process stages:

- pre-application research
- account setup or manual login
- property lookup
- permit type selection
- eligibility screening
- document preparation
- application data entry
- upload staging
- acknowledgement/certification review
- submission
- prescreen/intake
- fee payment
- plan review
- corrections/checksheets
- approval/issuance
- inspections
- closeout, cancellation, expiration, extension, or reactivation

### DevHubSurfaceMap

Fields:

- `surface_id`
- `auth_scope`
- `url_pattern`
- `page_heading`
- `accessible_landmarks`
- `actions`
- `fields`
- `validation_messages`
- `upload_controls`
- `state_transitions`
- `redaction_policy`
- `selector_confidence`
- `requires_attendance`
- `requires_exact_confirmation`

### UserGapAnalysis

Fields:

- `case_id`
- `process_id`
- `known_facts`
- `matched_documents`
- `missing_facts`
- `missing_documents`
- `stale_evidence`
- `conflicting_evidence`
- `required_confirmations`
- `blocked_actions`
- `next_safe_actions`

### GuardrailBundle

Fields:

- `guardrail_bundle_id`
- `process_id`
- `source_evidence_ids`
- `deterministic_predicates`
- `deontic_rules`
- `temporal_rules`
- `reversible_action_predicates`
- `exact_confirmation_predicates`
- `refused_action_predicates`
- `explanation_templates`
- `validation_status`

### ActionJournal

Commit-safe journal event types:

- public crawl preflight
- public crawl metadata capture
- requirement extraction
- user gap analysis
- reversible draft plan
- local PDF preview
- DevHub attended preflight
- DevHub attempted action
- post-action hardening review
- exact-confirmation checkpoint
- manual handoff
- refused action
- completion evidence

Journal events must not include credentials, cookies, auth state, screenshots, traces, HAR data, private values, payment details, or local private file paths.

## Public Website Archival Plan

### Phase 1: Source Discovery

- Seed from the official source anchors above.
- Parse links from Portland.gov PP&D pages using structured HTML parsing.
- Record every discovered URL with canonicalization, source page, link text, content type if known, and allow/skip decision.
- Keep the initial host allowlist narrow:
  - `www.portland.gov`
  - `devhub.portlandoregon.gov`
  - `www.portlandoregon.gov`
  - `www.portlandmaps.com` only for public property/permit references linked from official guidance
- Store skipped URLs with reason codes:
  - outside allowlist
  - unsupported scheme
  - private/authenticated
  - disallowed by robots or policy
  - raw download not permitted
  - too large
  - unsupported content type

### Phase 2: Processor Handoff

- Run PP&D-local policy preflight before invoking `ipfs_datasets_py`.
- Delegate robust web archival and extraction primitives to the processor suite.
- Preserve processor outputs through PP&D-local manifests, not by committing raw archives.
- Capture:
  - URL
  - redirect chain
  - response metadata
  - content hash
  - MIME type
  - processor name/version
  - source freshness metadata
  - normalized document reference

### Phase 3: HTML Extraction

Extract:

- title
- breadcrumbs
- headings and hierarchy
- body text
- ordered/unordered steps
- callouts and warnings
- tables
- contact blocks
- service hours
- "on this page" structure
- related links
- downloadable documents
- image alt text and captions
- visible updated/published dates when present

Preserve order. Many PP&D pages encode requirements through sequence.

### Phase 4: PDF and Form Extraction

Extract:

- text with page anchors
- tables and fee schedules
- checklist items
- required document labels
- signature and certification blocks
- fillable PDF field names and types
- checkbox/radio options
- date/deadline language
- file preparation instructions

Use OCR only when text extraction fails or when official screenshots contain necessary instructions. Mark OCR-derived content with confidence and human-review status.

### Phase 5: Change Monitoring

Recrawl schedule:

- DevHub FAQ, online tool guides, submit-permit guide, fee/payment guide: daily or every few days.
- Permit-type pages, forms index, file standards, Single PDF guidance: weekly.
- Low-change handouts and archived PDFs: monthly unless linked pages changed.

Change reports should include:

- changed source hash
- added or removed permit type
- changed required document
- changed upload or file naming rule
- changed fee/payment instruction
- changed deadline or expiration rule
- changed DevHub action guidance
- affected requirement IDs
- affected guardrail bundle IDs

## Authenticated DevHub Automation Plan

### Session Model

The default login flow is attended:

1. Open DevHub in a user-visible Playwright browser.
2. User selects Sign In/Register and completes PortlandOregon.gov login manually.
3. User completes MFA/CAPTCHA/security prompts manually if presented.
4. Worker confirms authenticated DevHub Home or equivalent account-scoped state.
5. Worker records only redacted state metadata and accessible UI structure.

Credential rules:

- The worker must not ask for or store passwords.
- The worker must not automate password recovery.
- The worker must not create accounts unless a separate human-run playbook is written.
- Browser state must be short-lived and ignored by git.

### DevHub Surface Categories

Safe read-only:

- DevHub Home
- My Permits & Requests
- permit details
- status messages
- fee notice review
- correction request review
- attachment list review
- inspection results review

Reversible draft:

- address/property search
- permit type selection before submission
- form field fill before submission
- save draft
- local preview of field mapping
- upload staging before official attach/submit

Consequential official:

- submit permit request
- certify acknowledgement
- upload correction to official record
- purchase trade permit
- schedule inspection
- cancel or withdraw
- request extension/reactivation
- change account/security settings

Financial:

- enter payment details
- submit payment
- save payment receipt

Unsupported/manual handoff:

- MFA
- CAPTCHA
- account creation
- password recovery
- final payment execution
- any workflow with unclear consequence

### Playwright Recorder

For each DevHub page or state, record:

- page title and visible heading
- URL pattern and route evidence
- accessible roles and names
- stable labels
- nearby headings
- validation messages
- required markers
- dropdown options
- conditional question triggers
- upload controls and file hints
- save/back/continue/submit button states
- timeout/save-for-later messages
- official action text and acknowledgement language

Fixtures should use mocked or synthetic pages unless a user explicitly authorizes a live attended capture. Live captures must be redacted before any fixture is committed.

### Guarded Action Executor

Before any Playwright action:

1. Classify the action.
2. Validate the action against the surface registry.
3. Require source evidence IDs.
4. Require user case facts for every filled value.
5. Require selector confidence.
6. Produce a preview.
7. Require attendance for DevHub actions.
8. Require exact confirmation for consequential actions.
9. Produce a commit-safe journal event.
10. Pause for post-action hardening after any live attempt.

Completion rule:

- `ready_to_attempt` means preflight passed.
- `attempted_review_required` means a live attempt happened and must be reviewed.
- `complete` requires user-visible outcome review, no private artifact leak, and completion evidence.

## Local PDF Draft-Fill Plan

Local PDF support is allowed earlier than live DevHub official uploads because it is reversible and user-controlled.

Required behavior:

- Build public form-field manifests from official public PDFs.
- Map fields to redacted user facts and requirement IDs.
- Generate local draft previews only in user-controlled output paths.
- Do not upload or submit generated PDFs.
- Do not persist private source documents in git.
- Preserve an audit event with field IDs, requirement IDs, redacted fact IDs, and output classification.

Acceptance fixtures:

- fillable public form field manifest
- redacted user facts
- generated local draft preview metadata
- privacy validator proving no private values are committed

## Requirement Extraction Plan

Extract four layers of requirements:

- Legal and policy requirements: obligations, prohibitions, permissions, exceptions, deadlines, authority.
- Submittal requirements: applications, plans, calculations, reports, signatures, licenses, property data, project descriptions, file standards.
- Workflow requirements: account, fields, save behavior, upload order, correction path, status tracking, fee review, payment sequence.
- Agent-operation requirements: when to ask the user, when to refuse, when to escalate, when to require attendance, when to require exact confirmation.

Extraction pipeline:

1. Normalize source text with citation spans.
2. Identify candidate requirements from headings, imperative language, checklists, tables, warnings, forms, and PDFs.
3. Link each candidate to permit type and stage.
4. Classify the candidate requirement type.
5. Extract conditions and exceptions.
6. Attach source evidence IDs.
7. Mark confidence and human-review status.
8. Compile validated candidates into process models and guardrail bundles.

## Formal Logic Guardrail Plan

### Layer 1: Deterministic Predicates

Examples:

```text
has_devhub_account(user)
has_property_identifier(project)
selected_permit_type(project, permit_type)
has_required_document(project, document_type)
document_is_pdf(file)
plans_are_single_pdf(project)
requires_plan_review(permit_type)
license_active(contractor_license)
acknowledgment_reviewed(user, acknowledgment_id)
user_present(session)
exact_confirmation(action_id)
```

### Layer 2: Deontic Rules

Examples:

```text
OBLIGATED(applicant, upload(application_pdf), before(submit_request))
OBLIGATED(applicant, upload(single_drawing_plan_pdf), if(single_pdf_process_applies))
PROHIBITED(agent, submit_application, unless(exact_confirmation(submit_application)))
PROHIBITED(agent, enter_payment_details, always)
PERMITTED(agent, fill_reversible_draft_field, if(user_present(session) and source_fact_available(field)))
PERMITTED(applicant, save_for_later, if(devhub_save_available))
```

### Layer 3: Temporal and Process Rules

Examples:

```text
before(prepare_documents, submit_request)
before(review_acknowledgement, certify_submission)
after(prescreen_acceptance, pay_intake_fees)
until(all_required_fields_complete, prohibit(submit_application))
after(live_attempt, require(post_action_hardening_review))
```

### Layer 4: Agent Action Gates

Examples:

```text
block(action) if source_evidence_stale(requirement)
block(action) if user_fact_conflict(requirement)
block(action) if action_class(action, consequential) and not exact_confirmation(action)
block(action) if action_class(action, financial)
ask_user(question) if missing_required_fact(requirement)
manual_handoff(action) if unsupported_surface(action)
```

The first production target should be deterministic predicates plus deontic and temporal guardrails. Full theorem-prover integration can follow after extracted rules have stable source evidence and test coverage.

## Agent Assistance Loop

1. User states a project goal.
2. Agent selects candidate process models.
3. Agent shows source-backed scope assumptions.
4. Agent reads known user facts and document-store metadata.
5. Agent runs gap analysis.
6. Agent asks only for missing or conflicting facts.
7. Agent prepares reversible draft values or local PDF previews.
8. Agent validates next action through the guardrail bundle.
9. Agent pauses for attendance and exact confirmation when required.
10. Agent produces a review packet:
    - known facts
    - missing facts
    - required documents
    - source citations
    - proposed next safe action
    - blocked actions and reasons

## Todo-Daemon Handoff Epics

The PP&D todo daemon should work in tranches that are broad enough to produce meaningful artifacts but small enough to validate.

### Epic 1: Source Registry and Surface Taxonomy

Deliver:

- official source seed manifest
- surface categories
- allowlist and skip reasons
- source freshness policy
- test fixtures for official source anchors

### Epic 2: Public Crawl Frontier and Processor Integration

Deliver:

- bounded public crawl frontier
- robots and allowlist preflight
- processor archival adapter
- archive manifest contract
- no-raw-body persistence validation

### Epic 3: Public Document and PDF Extraction

Deliver:

- HTML extraction contract
- PDF text and page-anchor extraction
- fillable field manifest extraction
- Single PDF and file-standard requirement extraction
- fixture coverage for representative pages and PDFs

### Epic 4: Process and Requirement Schemas

Deliver:

- requirement node schema
- permit process schema
- stage dependency graph
- source evidence model
- residential, commercial, trade, solar, demolition, sign, Urban Forestry, correction, inspection, and fee examples

### Epic 5: Formal Guardrail Compiler

Deliver:

- deterministic predicate compiler
- deontic rule compiler
- temporal rule compiler
- action gate compiler
- explanation support map
- validation tests for blocked and allowed actions

### Epic 6: DevHub Attended Login and Recorder

Deliver:

- Playwright manual-login handoff
- authenticated state detector
- redacted surface recorder
- selector confidence model
- mocked DevHub fixtures
- privacy validator

### Epic 7: Reversible Draft Automation

Deliver:

- field mapping from user facts to DevHub draft fields
- dry-run preview
- reversible fill executor
- save-for-later boundary
- attended worker journal
- post-action review states

### Epic 8: Local PDF Draft Fill

Deliver:

- public PDF field manifests
- user fact mapping
- local preview generation
- output path policy
- no-upload/no-submit guardrails

### Epic 9: User Document Gap Analysis

Deliver:

- user fact inventory model
- user document metadata model
- missing fact detector
- stale/conflicting evidence detector
- review packet generator

### Epic 10: Official Action and Payment Guardrails

Deliver:

- action classifier
- exact confirmation checkpoints
- official upload/submission/certification blockers
- payment review and payment execution blockers
- manual handoff workflows

### Epic 11: Operations and Supervision

Deliver:

- daemon task-board tranches
- supervisor idle recovery
- orphan child cleanup
- validation commands
- live-run playbooks
- source recrawl cadence
- production readiness checklist

## Validation Strategy

Every tranche should include at least one validation command. Recommended validation layers:

- `python3 -m py_compile` for touched Python files.
- PP&D fixture validation: `PYTHONPATH=ipfs_datasets_py python3 ppd/tests/validate_ppd.py`.
- Focused unit tests for changed modules.
- Privacy scan for forbidden paths and markers.
- Fixture-only Playwright tests for DevHub state recording.
- No-live-network default tests.
- Explicit live public dry-run only when the command includes a live flag.
- No authenticated live test unless a user explicitly attends the browser session.

## Production Readiness Gates

Do not call the system production-ready until all gates pass:

- Public source registry includes all official seed anchors and a documented recrawl policy.
- Public crawl produces archive manifests without committing raw bodies.
- Requirement nodes cite source evidence and have confidence/human-review status.
- Process models exist for representative residential, commercial, trade, correction, inspection, and fee workflows.
- Formal guardrails block missing required fields, missing documents, stale evidence, submission without confirmation, official upload without confirmation, and payment execution.
- DevHub recorder can run in attended/manual-login mode without credential capture.
- Playwright actions are classified and journaled.
- Local PDF draft fill creates previews only and never uploads/submits.
- Agent review packets explain known facts, missing gaps, blocked actions, and source citations.
- Private/session artifacts are ignored and absent from git.
- Supervisor and daemon recover from no-eligible-task, validation-failure, and orphan-child states.

## Ordered Delivery Waves

Use these waves to keep implementation narrow, source-backed, and daemon-friendly:

1. **Public source inventory and archival handoff**: finalize the official seed set, robots/allowlist policy, crawl batches, and `ipfs_datasets_py` processor manifests before deeper extraction work.
2. **Requirement and process normalization**: extract HTML/PDF requirements into permit-family process models, stage graphs, citation spans, deadlines, fees, document rules, and exceptions.
3. **Attended DevHub automation**: ship only manual-login, redacted recording, reversible draft-fill, and save-for-later support before any consequential workflow checkpoints.
4. **User document-store gap analysis**: compare known user facts/documents against requirement bundles so agents ask only for missing, stale, ambiguous, or conflicting inputs.
5. **Formal guardrail compilation and agent APIs**: compile reviewed requirements into predicates, deontic rules, temporal gates, exact-confirmation blockers, and agent-facing explain/validate/review-packet APIs.
6. **Operations and continuous supervision**: keep the PP&D daemon/supervisor fed with human-authored tranches, deterministic validation, live-run playbooks, and recrawl/freshness monitoring.

## Operator Todo List

Use this ordered todo list for human planning, backlog seeding, or manual execution:

1. Build the official PP&D/DevHub source map, including permit-family grouping, allowlist scope, recrawl cadence, and skip-reason policy.
2. Define crawl batches and processor-suite handoff contracts so every fetched page or PDF yields manifest metadata, hashes, normalized document IDs, and source evidence IDs without committing raw bodies.
3. Extract public HTML, PDFs, and fillable-form metadata into normalized requirement candidates with page anchors, citation spans, confidence markers, and human-review status.
4. Assemble permit-family process models for residential, commercial, trade, solar, demolition, sign, Urban Forestry, inspections, corrections, fees, cancellations, and extension/reactivation flows.
5. Build the attended DevHub login/session handoff so users authenticate manually while the worker records only redacted route, heading, field, and validation-state evidence.
6. Build reversible draft automation for DevHub and local PDF previews, including field manifests, fact-to-field mapping, save-for-later boundaries, and post-action review states.
7. Build the user document-store reconciliation layer that maps known documents/facts to process requirements, identifies missing or stale facts, and emits review packets instead of guessing.
8. Compile reviewed requirement nodes into deterministic predicates, deontic rules, temporal ordering rules, and exact-confirmation/payment/manual-handoff stop gates.
9. Expose agent-facing APIs that load process models, compare user facts, explain missing requirements, preview safe next actions, and block unsupported or consequential actions.
10. Add source-freshness monitoring, contradiction detection, privacy validation, and no-private-artifact enforcement before any production or semi-automated use.
11. Add bounded live public crawl playbooks and attended DevHub playbooks so operators know when the system may move from fixtures to explicitly authorized real sessions.
12. Keep the daemon/supervisor backlog replenished with narrow, source-backed tranches until every permit-family workflow and guardrail bundle has acceptance coverage.

## Daemon/Supervisor Wiring

The PP&D execution path is already wired around this plan document and the isolated PP&D task board:

- Plan source of truth for daemon prompts: `docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md`
- Backlog source of truth for daemon work selection: `ppd/daemon/task-board.md`
- Shared execution engine: `ipfs_datasets_py.optimizers.todo_daemon`
- PP&D wrappers: `ppd/daemon/ppd_daemon.py` and `ppd/daemon/ppd_supervisor.py`

Recommended operator flow:

1. Update this plan with the current wave ordering and guardrail policy.
2. Append a human-authored tranche of unchecked tasks to `ppd/daemon/task-board.md`.
3. Run `bash ppd/daemon/control.sh doctor` after backlog changes if the supervisor needs one repair/replanning pass.
4. Run `bash ppd/daemon/control.sh supervisor-start` for continuous replenishment or `bash ppd/daemon/control.sh start` for a single daemon worker loop.
5. Keep live crawl and authenticated DevHub actions behind explicit flags, user attendance, exact confirmation, and privacy validation.

## Open Questions

- Which permit categories are V1 priority: residential building, standard trade, solar, demolition, signs, Urban Forestry, correction uploads, inspections, or fees?
- Should private user case state be local-only, or will an encrypted backend exist?
- Which user document stores need first-class connectors?
- Will there be a dedicated DevHub test account, or only user-owned attended sessions?
- Which formal logic output should be the first stable interchange format for downstream agents?

## References

- PP&D bureau landing page: https://www.portland.gov/ppd
- Online permitting tools overview: https://www.portland.gov/ppd/how-use-online-permitting-tools
- DevHub public portal: https://devhub.portlandoregon.gov
- DevHub FAQ: https://www.portland.gov/ppd/devhub-faqs
- DevHub account and sign-in guide: https://www.portland.gov/ppd/devhub-sign-guide
- Apply for permits: https://www.portland.gov/ppd/get-permit/apply-permits
- DevHub permit application guide: https://www.portland.gov/ppd/devhub-guide-submit-permit-application
- Submit Plans Online / Single PDF Process: https://www.portland.gov/ppd/get-permit/submit-plans-online
- Permit applications and inspections applications: https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications
- File naming standards and preparing PDFs: https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs
- Fee payment guide: https://www.portland.gov/ppd/documents/how-pay-fees/download
