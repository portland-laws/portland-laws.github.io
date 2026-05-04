# Portland Permitting & Development Scraping, Automation, and Logic Guardrails Plan

## Summary

Build a compliant data and automation pipeline for Portland Permitting & Development (PP&D) and Development Hub PDX (DevHub) that can:

- Crawl public PP&D guidance, forms, permit-type pages, process pages, checklists, FAQs, and linked PDF artifacts.
- Automate authenticated DevHub workflows with explicit user authorization, controlled credentials, and auditable browser sessions.
- Convert scraped public guidance and observed authenticated workflow states into structured process models.
- Extract legal, procedural, and logical requirements into formal guardrails that LLM agents can use when helping users complete permitting processes.
- Identify only the missing user-specific facts, files, licenses, signatures, payments, acknowledgments, or decisions needed to complete a process.

The implementation should extend the existing Portland legal corpus direction in this repository: source-grounded retrieval, citations, knowledge graph artifacts, and browser-native/formal logic proof exploration.

## Current Source Landscape

Primary public sources to treat as authoritative starting points:

- PP&D landing and public guidance under `https://www.portland.gov/ppd`.
- Public applications and forms, including the "Permits and Inspections Applications" index.
- DevHub public portal at `https://devhub.portlandoregon.gov`.
- DevHub sign-in and account guidance on Portland.gov.
- DevHub FAQ and process guides on Portland.gov.
- Permit submission, plan upload, correction upload, payment, inspection, extension, and cancellation guidance pages.
- Linked PDFs, image-guided how-tos, handouts, and checklist documents.

Important current facts verified on May 1, 2026:

- DevHub is Portland's online permitting system.
- DevHub uses PortlandOregon.gov credentials for authenticated online permitting services.
- Public DevHub FAQ lists service categories including permit purchase, permit requests requiring plan review, inspection scheduling for online trade permits, correction uploads, and fee payments.
- DevHub application guidance lists permit request types including building permits, new single-family residence and detached ADU permits, solar permits, FCC wireless applications, demolition permits, trade permits, trade permits with plan review, sign permits, and Urban Forestry permits.
- Public guidance says some projects use a Single PDF Process, where drawing plans are one searchable PDF and applications/calculations/supporting documents are separate PDFs.

## Guiding Principles

- Compliance first: respect robots directives, published terms, rate limits, access controls, copyright constraints, and public-record/privacy boundaries.
- Public crawl before logged-in automation: extract as much as possible from public Portland.gov pages, PDFs, forms, and DevHub help content before touching authenticated workflows.
- Human authorization for user accounts: never log in, submit, pay, sign, certify, cancel, or upload on behalf of a user unless that action is explicitly authorized and the action is recorded.
- No bypassing controls: do not evade CAPTCHA, MFA, bot protections, paywalls, rate limits, access restrictions, or account boundaries.
- Preserve provenance: every extracted rule, checklist item, process state, and formal guardrail must point back to source URLs, document versions, captured timestamps, and page/PDF anchors when available.
- Separate legal requirements from operational UI behavior: code/legal obligations, submittal requirements, file-format rules, and DevHub click paths are related but not the same artifact.
- Fail closed: an agent should ask for clarification or route to a human when requirements conflict, evidence is stale, a workflow changes, or an irreversible action is about to occur.

## Target Architecture

```text
Public source discovery
  -> ipfs_datasets_py processor archival suite
  -> crawler frontier
  -> page/PDF/form/archive extractor
  -> normalized document store
  -> citation and version index
  -> process/requirement extraction
  -> formal logic guardrails
  -> agent planning and validation

Authenticated DevHub automation
  -> Playwright user-approved browser session
  -> state and form schema recorder
  -> guarded form-drafting scaffold
  -> account-scoped artifact store
  -> process-state model
  -> missing-information detector
  -> guarded action executor
```

## Repository Boundary

All PP&D implementation work should live under a top-level `ppd/` directory. The existing Portland legal corpus, browser logic port, and `ipfs_datasets_py` daemon artifacts should remain reusable references, not active write targets for this project.

The PP&D crawler and archive layer should reuse the existing website archival and processor suite in the `ipfs_datasets_py` submodule as a read-only dependency. The relevant submodule capabilities live under `ipfs_datasets_py/ipfs_datasets_py/processors/`, including:

- `web_archiving/` for web archive capture, archive utilities, and simple crawl primitives.
- `legal_scrapers/parallel_web_archiver.py`, `legal_scrapers/url_archive_cache.py`, and related legal/web archive helpers.
- `adapters/web_archive_adapter.py` and `adapters/specialized_scraper_adapter.py` for processor integration boundaries.
- `advanced_graphrag_website_processor.py`, `website_graphrag_processor.py`, and GraphRAG processors for archive-to-retrieval and archive-to-knowledge-graph workflows.
- PDF, multimedia, file-conversion, batch, and serialization processors that can normalize linked public documents after the archive layer captures them.

PP&D code should wrap these processors through a PP&D-local adapter contract rather than forking or rewriting the processor suite. The adapter should preserve PP&D allowlist, robots, no-persist, and redaction policy decisions before invoking any archival processor.

The only planned exceptions are:

- `docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md`: this plan.
- future root-level package or CI wiring only when needed to invoke `ppd/` commands from the repository root.
- read-only imports from existing TypeScript logic modules after an explicit compatibility layer is added.

No PP&D daemon run should write into:

- `src/lib/logic/`
- `public/corpus/portland-or/current/`
- `ipfs_datasets_py/.daemon/`
- existing TypeScript-port daemon ledgers.

## PP&D Directory Layout

```text
ppd/
  README.md
  daemon/
    ppd_daemon.ts
    task-board.md
    accepted-work/
    failed-patches/
    status.json
    progress.json
  crawler/
    seeds.ts
    allowlist.ts
    robots.ts
    fetcher.ts
    processorArchiveAdapter.ts
    extractHtml.ts
    extractPdf.ts
  devhub/
    session.ts
    playwrightSession.ts
    recorder.ts
    formDraftingScaffold.ts
    actionClassifier.ts
    selectors.ts
  extraction/
    processExtractor.ts
    requirementExtractor.ts
    sourceDiff.ts
  logic/
    predicates.ts
    deonticRules.ts
    guardrailCompiler.ts
    supportMap.ts
  data/
    raw/
    normalized/
    private/
    manifests/
  tests/
```

`ppd/.gitignore` should keep private DevHub artifacts, live crawl output, session state, traces, daemon status files, and failed patches out of version control. Curated public fixtures can still be committed under `ppd/tests/` when they are redacted and small.

## Daemon Reuse Plan

Reuse the prior TypeScript-port daemon pattern, but fork the operating model into a PP&D-specific daemon instead of sharing the existing daemon state.

Reusable patterns:

- Markdown task board as the controlling backlog.
- One narrow task per daemon cycle.
- Validation before accepting changes.
- Append-only accepted-work ledger.
- Failed patch capture with failure kind.
- Status and progress JSON files for long-running operation.
- Heartbeat while waiting on model, browser, crawler, or validation steps.
- Rollback-on-validation-failure behavior.
- Explicit blocked-task handling rather than spinning on the same failure.

PP&D-specific differences:

- The task board lives in `ppd/daemon/task-board.md`, not in the TypeScript logic port plan.
- Accepted artifacts live in `ppd/daemon/accepted-work/`.
- Failed patches live in `ppd/daemon/failed-patches/`.
- Status and progress files live in `ppd/daemon/`.
- The daemon allowlist initially permits edits only under `ppd/` and this PP&D plan document.
- The validation command set is PP&D-specific:
  - TypeScript typecheck for `ppd/` code when added.
  - crawler dry-run against a tiny public seed set.
  - extraction fixture tests.
  - DevHub recorder tests using mocked or manually captured fixtures only.
  - guardrail compiler tests.
- Authenticated DevHub automation is never run unattended by the daemon unless a user-owned session has been explicitly authorized for that cycle.

### Autonomous Supervisor Redesign

As of May 3, 2026, the active PP&D daemon/supervisor implementation is Python under `ppd/daemon/`. The supervisor is responsible for keeping work moving when the daemon is stuck, when every selectable item is blocked, or when the task board is fully complete.

The supervisor should now treat an all-complete PP&D board as a planning signal, not an idle state:

- Diagnose the completed board as `plan_next_tasks`.
- Review the completed work against the original PP&D goal.
- Append the next deterministic autonomous platform tranche when no model-generated repair is acceptable.
- Restart the daemon with `PPD_LLM_BACKEND=llm_router`.
- Let the daemon immediately select the next pending task rather than sleeping between available tasks.

The current autonomous platform tranche is intentionally broader than the parser-recovery tranches. It develops:

- `ppd/crawler/whole_site_archival.py`: a side-effect-free whole-site public archival plan for PP&D public sources, processor-suite handoff, PDF normalization, requirement extraction, link graph construction, and formal-logic output manifests.
- `ppd/devhub/playwright_pdf_automation.py`: a side-effect-free Playwright and PDF draft automation plan for user-authorized draft form fills, local PDF field fills, audit events, and exact-confirmation gates.
- Supervisor regression coverage proving completed boards synthesize new platform tasks instead of idling.
- Daemon operations coverage proving watch mode starts the next cycle immediately when another task is selectable, while subprocess, validation, and LLM calls remain bounded by timeouts.

The supervisor may patch daemon/supervisor programming when diagnostics show the daemon is stuck, but those patches must stay inside `ppd/`, pass validation, avoid private artifacts, and preserve the fail-closed DevHub action boundaries.

The supervisor also handles goal drift. If an older narrow autonomous-platform slice, such as the tranche 2 source-evidence continuation task, stalls after newer live public scrape, attended Playwright, and PDF draft-fill boundaries exist, the supervisor should park the stale slice and append an execution-capability tranche. That tranche must include:

- A supervised live whole-site public crawl runner that resumes an allowlisted PP&D frontier, delegates capture to the `ipfs_datasets_py` processor suite, and persists metadata manifests instead of raw bodies or downloaded documents.
- Processor-suite execution integration that carries public pages and PDFs into archive manifests, normalized document records, PDF metadata, requirement batches, and formal-logic source evidence IDs.
- An attended Playwright DevHub worker runner for manual login handoff, journal replay, reversible draft fills from redacted facts, and mandatory pauses before official or security-sensitive transitions.
- A local PDF draft-fill work queue that maps public PP&D form fields to redacted user facts and invokes the local pypdf draft filler for previews only.
- A formal-logic guardrail extraction pipeline that produces obligations, prerequisites, missing-fact questions, reversible-action predicates, exact-confirmation predicates, and refused official-action stop gates.
- Supervisor recovery coverage proving stale `calling_llm` or `applying_files` status on old platform slices parks the stale tranche, appends execution-capability work, validates the daemon, and restarts with `PPD_LLM_BACKEND=llm_router`.

The daemon should treat no-file LLM failures as durable runtime diagnostics rather than ordinary validation candidates. When `llm_router` times out or its child process is terminated before returning a JSON proposal, the daemon records the failure, skips full validation for the empty proposal, resets the selected task to pending, and allows the supervisor to decide whether to retry, park, or replenish. Timeout cleanup must terminate the entire child process group so npm/Copilot descendants do not continue running after the daemon cycle ends.

### Live Execution Boundary

The PP&D workspace now has a live-capable boundary for the parts that can be exercised safely:

- `ppd/crawler/live_public_scrape.py` runs a tiny live public scrape only when `--live` or `allow_live_network=True` is explicit. It performs allowlist and robots preflight, caps the seed count, records metadata summaries, and does not persist raw response bodies or downloaded documents.
- `ppd/pdf/draft_fill.py` performs real local PDF field filling with `pypdf`. It writes only user-controlled draft output PDFs, refuses private/raw output paths, and does not upload or submit the result.
- `ppd/devhub/live_action_executor.py` defines the guarded live DevHub action boundary. Draft field fills can execute against an injected Playwright page after user browser authorization. Upload, submit, certify, cancel, inspection scheduling, and payment-review checkpoints require explicit live execution flags plus exact action-specific confirmation. MFA, CAPTCHA, account creation, password recovery, payment-detail entry, and final fee payment remain manual handoffs.
- `ppd/devhub/attended_worker.py` wraps the live DevHub executor with an attended-worker protocol. The worker pauses unless the user is present, has reviewed the current screen, and understands the next action. It also requires source evidence IDs, selector confidence, a dry-run or preview, an audit event, a rollback plan, and proof that private artifacts were not persisted before any attempt. After an action is attempted, the worker returns `attempted_review_required` and cannot mark the step complete until post-action hardening, user outcome review, completion evidence, and side-effect checks all pass. The worker can emit commit-safe journal events that record only transition metadata and guardrail facts; selector strings, filled values, local file paths, browser state, traces, screenshots, and exact confirmation phrases are excluded or redacted. Journal replay produces resumable worker states such as `collect_attendance_or_hardening`, `attempt_while_attended`, `review_post_action_hardening`, `manual_handoff`, and `closed_complete`, and rejects any later event for an already completed step.

The May 3, 2026 smoke run successfully fetched the public PP&D home seed `https://www.portland.gov/ppd` through the bounded live public scraper and stored only the summary returned to the terminal, not raw site output.

The first PP&D daemon milestone should be documentation-only and fixture-only:

1. Create `ppd/daemon/task-board.md`.
2. Add a small seed manifest for public PP&D pages.
3. Add extraction fixtures from public HTML/PDF samples.
4. Add validation commands that operate only on fixtures.
5. Only then add live public crawl dry-runs.

## Data Stores

- `processor_archive_manifests`: PP&D-local manifests that reference `ipfs_datasets_py` processor/archive outputs by content hash, source URL, canonical URL, capture timestamp, processor name/version, and policy decision. These manifests should not contain raw response bodies.
- `raw_public_documents`: immutable HTML, PDF, image-alt text, downloaded form metadata, headers, crawl timestamp, checksum, and source URL, preferably captured through the `ipfs_datasets_py` processor archival suite and represented in PP&D through manifests and normalized fixtures.
- `normalized_documents`: markdown/text extraction, sections, tables, links, page numbers, form fields, and document type.
- `source_index`: canonical URL, redirects, title, bureau, page type, last-seen timestamp, etag/last-modified when present, content hash, and crawl status.
- `permit_processes`: permit type, scope, eligibility, required inputs, required documents, fees, review stages, correction stages, inspections, expiration/reactivation/cancellation/refund paths.
- `devhub_workflow_snapshots`: authenticated screen states, labels, fields, validation messages, options, dependencies, and navigation edges, with private user values redacted by default.
- `formal_requirements`: normalized obligations, prohibitions, permissions, preconditions, exceptions, deadlines, temporal constraints, and citation links.
- `agent_guardrails`: executable checks that gate LLM-agent actions, prompts, and missing-information requests.
- `user_case_state`: account-scoped project facts, uploaded-file inventory, draft/submitted status, payments, messages, checksheets, and outstanding tasks.

## Public Crawling Plan

### Phase 1: Discovery

- Seed the crawler with:
  - `https://www.portland.gov/ppd`
  - PP&D residential permitting pages.
  - PP&D commercial permitting pages.
  - PP&D applications/forms/handouts pages.
  - DevHub FAQ and quick guides.
  - DevHub public landing page.
  - Portland Maps permit/case search references where relevant.
- Discover links using structured HTML parsing.
- Track content type: HTML, PDF, image, downloadable document, external site, mailto, phone, and portal action.
- Keep a domain allowlist initially limited to:
  - `www.portland.gov`
  - `devhub.portlandoregon.gov`
  - `www.portlandoregon.gov`
  - `www.portlandmaps.com` only for public permit/case/property references.
- Store skipped URLs with reason codes.
- Route archival capture through a PP&D adapter over `ipfs_datasets_py/ipfs_datasets_py/processors` once a URL has passed allowlist, robots, timeout, content-type, and no-persist preflight.
- Treat PP&D-native crawler code as policy and orchestration glue. Do not duplicate robust archive, processor, GraphRAG, PDF, or serialization functionality that already exists in the submodule.

### Phase 2: Extraction

- HTML:
  - Extract title, breadcrumbs, headings, body text, tables, ordered steps, callouts, contact details, links, downloadable documents, modified dates if exposed, and image alt/caption text.
  - Preserve heading hierarchy and list ordering because process pages encode requirements through sequence.
- PDFs:
  - Extract text with page numbers.
  - Extract form fields when PDFs are fillable.
  - OCR only when text extraction fails.
  - Detect checkboxes, required-data labels, signature blocks, fee tables, and document expiration language.
- Images:
  - Prefer alt text and captions first.
  - Use OCR only for instructional screenshots when legally and technically appropriate.
- Forms:
  - Identify required fields, enumerated options, conditional sections, signatures, attestations, and instructions.

### Phase 3: Change Monitoring

- Use content hashes and HTTP caching headers when available.
- Recrawl high-change pages daily or weekly:
  - DevHub FAQ and how-to guides.
  - Permit application pages.
  - fee/payment pages.
  - temporary exemption/suspension pages.
- Recrawl low-change PDFs monthly unless linked page changed.
- Generate change reports:
  - new/removed permit types.
  - changed submittal requirements.
  - changed deadlines or expiration rules.
  - changed fees/payment instructions.
  - changed authenticated workflow guidance.

## Authenticated DevHub Automation Plan

### Scope

Authenticated automation should support account-scoped user assistance, not bulk scraping of private data.

Initial supported actions:

- Sign in with explicit user-provided credentials or delegated browser session.
- Capture available DevHub navigation and workflow states for the signed-in user.
- Resume saved drafts.
- Inspect "My Permits & Requests" state.
- Identify missing required fields and files before submission.
- Prepare uploads and form entries for user review.
- Stop before irreversible actions unless the user has explicitly approved that exact action.

Later supported actions:

- Submit an application after final user confirmation.
- Upload corrections after user confirmation.
- Schedule inspections where permitted.
- Pay fees only with explicit, high-friction confirmation and payment-specific safeguards.

### Session Strategy

- Use Playwright browser automation for DevHub because workflow state is dynamic and authenticated.
- Store authentication state separately from scraped public data.
- Prefer short-lived encrypted session storage over storing credentials.
- Support a "bring your own browser" mode where the user logs in manually and automation attaches only after authentication.
- Mask or redact PII and project-sensitive values in logs, screenshots, traces, and fixtures.
- Record selectors semantically:
  - accessible name.
  - label text.
  - role.
  - nearby heading.
  - stable URL/state.
  - fallback CSS/XPath only as a last resort.

### Playwright Form-Drafting Scaffold

Future AI agents should use Playwright only inside a guarded drafting workflow:

- Start from a user-approved browser session. The preferred mode is manual login, then attach/continue after the user is authenticated.
- Read workflow state, labels, accessible names, validation messages, upload controls, and visible options before proposing any field changes.
- Draft reversible field entries only when the missing-information detector has source-backed user facts or the user has supplied values in the current interaction.
- Keep field-value fixtures redacted. Test Playwright code against mocked DevHub pages or synthetic fixtures, not real user account pages.
- Support dry-run and "preview changes" modes that show planned field edits before interacting with a page.
- Stop before official upload, certification, submission, payment, cancellation, inspection scheduling, or any action classified as consequential/financial unless the user explicitly confirms the exact action in that session.
- Never automate CAPTCHA, MFA, account creation, password recovery, payment entry, or bypass controls.
- Record an audit event for every proposed and executed browser action, including the selector basis, process requirement, user confirmation state, and whether the action was read-only, draft-edit, consequential, or financial.
- Route live browser attempts through the attended worker. The attended worker separates `ready_to_attempt`, `attempted_review_required`, and `complete` so no single step is fully completed merely because Playwright clicked or filled something.
- Persist only commit-safe attended-worker journal entries for live-step state. A valid journal must show a ready preflight event before an attempted event, and an attempted review-required event before any completion-review event can mark the step complete.
- On daemon or worker restart, replay the attended-worker journal to recover the last known state. A ready preflight can resume to an attended attempt; an attempted step resumes to post-action hardening review; a completed step is closed and must not receive later worker events.

### Login Workflow

- Navigate to DevHub public portal.
- Follow the official Sign In/Register path to PortlandOregon.gov authentication.
- Allow manual MFA/CAPTCHA/user-verification steps if presented.
- Confirm successful session by detecting signed-in DevHub home, account menu, or user-specific navigation.
- Do not automate password recovery, MFA enrollment, or account creation beyond documenting the user-visible steps unless separately authorized.

### Workflow Recorder

For each authenticated DevHub workflow, record:

- Page/state identifier.
- URL and redirect chain.
- Available actions.
- Form fields, labels, descriptions, validation messages, and required markers.
- Select/dropdown options.
- Conditional questions and trigger dependencies.
- Save/continue/back/submit button states.
- Timeout behavior and save-for-later behavior.
- Upload controls, accepted file types, file-size hints, and file naming rules.
- Acknowledgment/certification text, stored as citation-backed legal/action gates.

### Guarded Action Executor

Before any action, the executor must classify it:

- Safe read-only: navigate, inspect, download own documents, summarize status.
- Reversible draft edit: fill field, save draft, attach file before final submission.
- Potentially consequential: submit application, upload official correction, schedule inspection, cancel request, certify statement.
- Financial: pay fees or enter payment details.

Potentially consequential and financial actions require:

- explicit user instruction for that exact action.
- a summarized action preview.
- source-backed explanation of the consequence.

### PP&D Surface Registry

The implementation should keep one side-effect-free registry that maps every PP&D process surface to its executor, automation mode, guardrails, and completion rule. The current registry lives under `ppd/surfaces/` and covers:

- public guidance, public status/search references, processor archive handoff, requirement/formal-logic export, and user document-store fact matching.
- local PDF draft filling and draft previews.
- DevHub login handoff, reversible draft field reads/fills/saves, messages/checksheets, uploads, submissions/certifications/cancellations, payment review, inspection scheduling, and security/account handoffs.
- completion evidence and audit closeout.

Agents should consult the registry before touching any PP&D surface. Public and local draft surfaces may advance autonomously only within their read-only or draft-only guardrails. DevHub draft surfaces require an attended user, screen review, source evidence IDs, selector confidence, preview/dry-run evidence, an audit event, rollback plan, and proof that private artifacts were not persisted. Official uploads, submissions, certifications, cancellations, and inspections require exact action confirmation plus post-action hardening and user outcome review. Payment-detail entry, final payment execution, MFA, CAPTCHA, account creation, and password recovery remain manual handoffs.

No process should be marked complete merely because an agent clicked, filled, uploaded, submitted, scheduled, or opened payment review. Completion requires source-backed guardrails, attended attempts for live surfaces, post-action hardening, user outcome review, and completion evidence IDs.
- confirmation checkpoint.
- durable audit event.

## Process Model

Each PP&D process should compile into a normalized process graph:

```text
Process
  id
  permit_type
  authority_sources[]
  eligibility_rules[]
  required_user_facts[]
  required_documents[]
  file_rules[]
  fees[]
  stages[]
  deadlines[]
  exceptions[]
  external_dependencies[]
  irreversible_actions[]
```

Stages should include:

- pre-application research.
- account setup.
- property lookup.
- permit/request type selection.
- eligibility screening.
- document preparation.
- application data entry.
- upload.
- acknowledgment/certification.
- submission.
- prescreen/intake.
- fee payment.
- plan review.
- corrections/checksheets.
- approval/issuance.
- inspections.
- closeout, cancellation, expiration, extension, or reactivation.

## Requirement Extraction

Extract requirements at four levels:

- Legal requirements: code-based obligations, prohibitions, permissions, exceptions, deadlines, and authority.
- Submittal requirements: forms, plans, calculations, reports, signatures, licenses, property data, project descriptions, and file standards.
- Workflow requirements: DevHub account, field completion, save behavior, upload order, correction upload path, and status tracking.
- Agent-operation requirements: when to ask the user, when to refuse, when to escalate to PP&D, and when to stop for confirmation.

Each requirement should include:

- `requirement_id`
- `type`: obligation, prohibition, permission, precondition, exception, deadline, dependency, action_gate
- `subject`: applicant, property owner, contractor, permit technician, reviewer, agent, system
- `action`
- `object`
- `conditions`
- `deadline_or_temporal_scope`
- `evidence`
- `confidence`
- `formalization_status`

## Formal Logic Guardrails

Use a layered representation so guardrails are practical before full theorem-prover parity is complete:

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
```

### Layer 2: Deontic Rules

Examples:

```text
OBLIGATED(applicant, upload(application_pdf), before(submit_request))
OBLIGATED(applicant, upload(single_drawing_plan_pdf), if(single_pdf_process_applies))
PROHIBITED(agent, submit_application, unless(explicit_user_confirmation(submit_application)))
PERMITTED(applicant, save_for_later, if(devhub_save_available))
```

### Layer 3: Temporal and Process Rules

Examples:

```text
before(prepare_documents, submit_request)
after(prescreen_acceptance, pay_intake_fees)
until(all_required_fields_complete, prohibit(submit_application))
if(inactivity_exceeds_policy_window, draft_may_be_deleted)
```

### Layer 4: Proof and Explanation Artifacts

- Compile extracted rules to the repository's existing logic artifact conventions where possible:
  - TDFOL/deontic formulas.
  - CEC/DCEC process events.
  - F-logic frames for permit/process ontology.
  - support maps tying each formal rule to source text.
- Store explanation text for agent-facing and user-facing forms.
- Mark generated proof artifacts as machine-derived until validated.

## Agent Assistance Loop

The agent should operate as a missing-information resolver:

1. User states the project goal.
2. Agent retrieves relevant PP&D process model and source-backed requirements.
3. Agent compares known user document-store facts against required facts and documents.
4. Agent asks only for missing or ambiguous facts.
5. Agent checks eligibility, exceptions, and workflow prerequisites.
6. Agent prepares a draft application plan and file checklist.
7. Agent optionally drives DevHub draft entry under user-approved browser automation.
8. Agent pauses before submission, certification, payment, cancellation, or official upload.
9. Agent records final state, sources used, unresolved issues, and recommended next action.

## Missing-Information Detection

The user's document store should be queried for:

- property address and property ID.
- owner/applicant/contractor identity.
- contractor CCB/BCD/license numbers where required.
- project description and scope.
- occupancy/use details.
- valuation.
- existing permit/case numbers.
- plan PDFs.
- calculations and reports.
- forms and signatures.
- prior PP&D correspondence.
- checksheets and correction responses.
- payment/fee notices.

The detector should output:

- available evidence.
- missing fields.
- conflicting facts.
- stale documents.
- uncertain matches.
- facts that require user certification.

## Data Contracts

### `ScrapedDocument`

```ts
interface ScrapedDocument {
  id: string;
  sourceUrl: string;
  canonicalUrl: string;
  contentType: "html" | "pdf" | "image" | "form" | "other";
  title: string;
  fetchedAt: string;
  contentHash: string;
  text: string;
  links: SourceLink[];
  extractedFields?: ExtractedField[];
  pageAnchors?: PageAnchor[];
}
```

### `PermitProcess`

```ts
interface PermitProcess {
  id: string;
  name: string;
  permitTypes: string[];
  sourceIds: string[];
  stages: ProcessStage[];
  requiredFacts: RequiredFact[];
  requiredDocuments: RequiredDocument[];
  actionGates: ActionGate[];
  formalRequirements: FormalRequirement[];
}
```

### `FormalRequirement`

```ts
interface FormalRequirement {
  id: string;
  kind: "obligation" | "prohibition" | "permission" | "precondition" | "exception" | "deadline";
  naturalLanguage: string;
  formula?: string;
  logicSystem?: "predicate" | "deontic" | "tdfol" | "cec" | "flogic";
  evidence: EvidenceRef[];
  confidence: number;
  validationStatus: "draft" | "machine_checked" | "human_reviewed" | "retired";
}
```

### `DevHubWorkflowState`

```ts
interface DevHubWorkflowState {
  id: string;
  workflow: string;
  urlPattern: string;
  heading: string;
  fields: WorkflowField[];
  actions: WorkflowAction[];
  validationMessages: string[];
  nextStates: string[];
  capturedAt: string;
}
```

## Implementation Phases

### Phase 1: Governance and Source Inventory

- Create source allowlist and crawl policy.
- Check robots and terms for every domain before crawling.
- Define private-data redaction policy.
- Define user-consent and audit requirements for DevHub automation.
- Build initial source inventory from PP&D public pages and DevHub guides.

### Phase 2: Public Crawler MVP

- Implement deterministic PP&D policy/preflight wrappers for Portland.gov PP&D pages.
- Add an adapter that invokes the `ipfs_datasets_py` processor archival suite for public page/PDF capture only after PP&D policy checks pass.
- Add PDF processing through existing processor capabilities where possible before adding PP&D-specific extractors.
- Normalize documents to markdown/text with provenance.
- Generate crawl manifest and content hashes.
- Add rate limits, retries, and skip reasons.
- Validate extraction on a small sample of permit pages and application PDFs.

### Phase 3: Process and Requirement Extraction

- Add extraction prompts/rules for:
  - permit type.
  - eligibility.
  - required forms.
  - required documents.
  - deadlines.
  - fees.
  - review stages.
  - inspections.
  - exceptions.
- Build human-reviewable JSON artifacts.
- Add source-backed diff reports when public pages change.

### Phase 4: Authenticated DevHub Recorder

- Implement Playwright session bootstrap.
- Support manual login and saved browser state.
- Record workflow states without submitting anything.
- Capture field schemas, options, validation messages, and navigation edges.
- Redact PII in traces and screenshots.
- Produce repeatable fixtures from a test account or synthetic account only when authorized.
- Add a Playwright form-drafting scaffold that can fill reversible draft fields in mocked fixtures, but only emits action plans for live DevHub until confirmation-gate tests are complete.
- Add tests proving the scaffold refuses upload, submit, certify, pay, cancel, schedule inspection, MFA, CAPTCHA, account creation, and password recovery routes without exact user authorization.

### Phase 5: Guardrail Compiler

- Convert extracted requirements into deterministic predicates and deontic rules.
- Attach evidence references to every formal requirement.
- Add consistency checks:
  - missing citation.
  - conflicting deadline.
  - conflicting required document.
  - unsupported action gate.
  - stale source.
- Export guardrails for LLM-agent runtime.

### Phase 6: Agent Integration

- Add a planning API:
  - `loadPermitProcess(goal)`
  - `compareUserFacts(process, documentStore)`
  - `listMissingRequirements(caseState)`
  - `validateNextAction(caseState, action)`
  - `explainBlockedAction(caseState, action)`
- Add an autonomous-assistance loop that stays citation-grounded.
- Require confirmation gates for consequential actions.
- Add UI or CLI review screens for application readiness.

### Phase 7: Continuous Maintenance

- Schedule public recrawls.
- Run source diff checks.
- Recompile process models and guardrails.
- Flag affected agent workflows when requirements change.
- Keep a human-review queue for changed legal/process requirements.

## Testing Plan

- Crawler tests:
  - URL canonicalization.
  - allowlist enforcement.
  - robots/terms gate handling.
  - HTML extraction.
  - PDF extraction with page references.
  - content hashing and recrawl diffs.
- Requirement extraction tests:
  - known permit pages produce expected required documents.
  - checklist PDFs produce expected checkbox requirements.
  - citations survive normalization.
  - contradictory extracted rules are flagged.
- DevHub automation tests:
  - login flow can pause for manual authentication.
  - Playwright fixtures can discover fields by accessible name, label text, role, nearby heading, and stable URL/state.
  - form-drafting scaffold can prepare reversible draft entries from redacted fixture facts.
  - scaffold refuses consequential and financial actions without exact confirmation.
  - attended worker pauses before every attempt unless the user is present and preflight hardening passes.
  - attended worker keeps attempted actions in review-required state until completion hardening and user outcome review pass.
  - attended worker journals reject attempts without ready preflight and reject completions without a prior attempted event.
  - attended worker journals redact exact confirmation phrases and never serialize selectors, values, local file paths, browser storage, screenshots, or traces.
  - attended worker journal replay reports deterministic resume actions and rejects later events after completion.
  - mocked pages cover upload controls, validation messages, disabled submit states, save-for-later, and draft-resume navigation.
  - selectors use accessible roles/names where possible.
  - recorder captures fields without submitting.
  - PII redaction works in traces and logs.
  - irreversible buttons are blocked without explicit confirmation.
- Guardrail tests:
  - missing required document blocks submission.
  - missing acknowledgment blocks submission.
  - payment action requires payment-specific confirmation.
  - stale source blocks autonomous confidence.
  - unsupported process asks for human assistance.
- End-to-end tests:
  - residential project goal -> process model -> missing facts -> draft checklist.
  - trade permit goal -> license prerequisite check -> DevHub draft readiness.
  - correction upload goal -> checksheet requirements -> upload confirmation gate.

## Security and Privacy

- Encrypt stored session state and never commit it.
- Keep account-scoped DevHub artifacts outside public static assets.
- Redact names, emails, phone numbers, addresses, permit numbers, payment details, and uploaded filenames unless needed for the active user case.
- Use separate storage namespaces for public corpus and private user case data.
- Log agent actions with timestamp, action type, user instruction, confirmation state, and result.
- Do not store payment card or bank details.
- Use least-privilege service accounts only where the City explicitly permits them.

## Risks and Mitigations

- Site structure changes: prefer semantic extraction, record source diffs, and run Playwright smoke tests.
- Auth flow changes: support manual login and fail closed.
- Legal requirement ambiguity: keep human-review status and cite source text.
- Private data leakage: default redaction, encryption, and storage separation.
- Over-automation: classify actions and require confirmation for consequential steps.
- Stale guidance: source timestamps, recrawl schedules, and stale-evidence guardrails.
- PDF extraction errors: page-level citations, OCR confidence, and human-review queues.
- Conflicting public sources: detect conflicts and route to PP&D or human review.

## Acceptance Criteria

- Public crawler produces a reproducible manifest of PP&D pages and documents with source URLs, hashes, and normalized text.
- At least one residential, one commercial, one trade, and one correction workflow are represented as process models.
- Every generated requirement has evidence and validation status.
- Authenticated DevHub recorder can capture workflow state without submitting or paying.
- Guardrail compiler blocks at least:
  - missing required fields.
  - missing required documents.
  - missing explicit acknowledgment.
  - submission without confirmation.
  - payment without payment-specific confirmation.
- Agent loop can summarize known facts, missing gaps, and next safe action with citations.
- Changed source pages trigger a diff report and mark affected guardrails for review.

## Open Questions

- What formal logic formats should be treated as the first production target for PP&D workflows: deterministic predicates plus deontic rules, or full TDFOL/CEC from the beginning?
- Will the project maintain a DevHub test account, or should all authenticated automation initially run only in user-owned manual-login sessions?
- Which user document stores need first-class connectors?
- Should private user case state stay local-only, or is an encrypted backend planned?
- Which PP&D permit categories are highest priority for V1?

## Source References

- DevHub public portal: https://devhub.portlandoregon.gov
- DevHub sign-in guide: https://www.portland.gov/ppd/devhub-sign-guide
- DevHub FAQ: https://www.portland.gov/ppd/devhub-faqs
- DevHub permit application guide: https://www.portland.gov/ppd/devhub-guide-submit-permit-application
- Submit plans online / Single PDF Process: https://www.portland.gov/ppd/get-permit/submit-plans-online
- PP&D permits and inspections applications: https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications
