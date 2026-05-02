# PP&D Daemon Task Board

This board is the controlling backlog for the isolated PP&D daemon. The daemon should run one unchecked task per cycle, keep changes narrow, and validate before accepting work.

## Operating Rules

- Work only under `ppd/` unless a task explicitly names an allowed operations document.
- Do not create private DevHub session files, auth state, traces, raw crawl output, downloaded documents, or live crawl artifacts.
- Do not automate CAPTCHA, MFA, account creation, payment, official submission, certification, cancellation, upload, or inspection scheduling.
- Prefer fixture-first and validation-first work before live public crawling or authenticated automation.
- Keep every task small enough for one daemon cycle.
- When adding Python tests or helpers, keep comparisons syntactically complete and run py_compile through the daemon self-test before broader tests.
- Preserve source provenance in every public guidance, requirement, process, and guardrail fixture.
- After any rollback containing `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, do not retry a broad contract rewrite. First repair daemon supervision so changed Python or TypeScript files are syntax-checked before full validation.
- Syntax-recovery proposals should normally replace one file only. Use two files only when the second file is a tiny focused test or fixture for the same syntactic guardrail.
- Python proposals must not contain TypeScript-style annotations in expressions, such as `if value list[str]:`. TypeScript proposals must not contain Python control-flow or type syntax.
- When a domain task has failed twice for parser or compile reasons, block that task and append narrower daemon-repair tasks before resuming the domain task.
- If a syntax-preflight helper exists, the daemon apply path must call it before full validation and must classify parser failures as `syntax_preflight`.
- When a fixture-validator task fails because expected fields are absent, do not immediately rewrite the fixture or add a broader contract. First add a daemon diagnostic or prompt guardrail that reports the committed fixture shape and constrains the next retry to the fields actually present unless the task explicitly permits fixture replacement.
- After four consecutive daemon rounds without an accepted patch while the daemon is in `calling_llm`, pause the active domain task and append a narrow daemon prompt/preflight repair before retrying the domain task.

## Completed Work

- [x] Task checkbox-01: Bootstrap the PP&D daemon task board and operations boundary.
- [x] Task checkbox-02: Add PP&D-local ignore rules for private DevHub and generated crawl artifacts.
- [x] Task checkbox-03: Add the initial PP&D validation entrypoint.
- [x] Task checkbox-04: Add fixture-only public seed validation.
- [x] Task checkbox-05: Add public source allowlist validation.
- [x] Task checkbox-06: Add robots and no-persist policy fixture validation.
- [x] Task checkbox-07: Add skipped-URL reason fixture validation.
- [x] Task checkbox-08: Add processor archive adapter manifest fixture validation.
- [x] Task checkbox-09: Add normalized public HTML fixture validation.
- [x] Task checkbox-10: Add linked public document metadata fixture validation.
- [x] Task checkbox-11: Add public PDF metadata fixture validation.
- [x] Task checkbox-12: Add source index fixture validation.
- [x] Task checkbox-13: Add extraction provenance fixture validation.
- [x] Task checkbox-14: Add public guidance section hierarchy fixture validation.
- [x] Task checkbox-15: Add public guidance table/list extraction fixture validation.
- [x] Task checkbox-16: Add public form metadata fixture validation.
- [x] Task checkbox-17: Add DevHub public guidance fixture validation without authentication.
- [x] Task checkbox-18: Add mocked DevHub recorder fixture validation.
- [x] Task checkbox-19: Add DevHub action classification fixture validation.
- [x] Task checkbox-20: Add guarded form-drafting scaffold fixture validation.
- [x] Task checkbox-21: Add missing-information detector fixture validation.
- [x] Task checkbox-22: Add formal requirement predicate fixture validation.
- [x] Task checkbox-23: Add guardrail compiler fixture validation.
- [x] Task checkbox-24: Add permit lifecycle requirement category schema fixture validation.
- [x] Task checkbox-25: Add permit lifecycle source-evidence fixture validation.
- [x] Task checkbox-26: Add permit lifecycle normalized requirement fixture validation.
- [x] Task checkbox-27a: Add mutation coverage for missing lifecycle requirement category identifiers.
- [x] Task checkbox-27b: Add mutation coverage for empty lifecycle requirement actions.
- [x] Task checkbox-27c: Add mutation coverage for empty lifecycle requirement objects.
- [x] Task checkbox-27d: Add mutation coverage for missing lifecycle requirement source evidence.
- [x] Task checkbox-27e: Add mutation coverage for out-of-range lifecycle requirement confidence values.
- [x] Task checkbox-27f: Add mutation coverage for duplicate lifecycle requirement keys.
- [x] Task checkbox-28: Add deterministic daemon self-test coverage for PP&D task parsing.
- [x] Task checkbox-29: Add accepted-work ledger validation.
- [x] Task checkbox-30: Add failed-patch manifest validation.
- [x] Task checkbox-31: Add daemon status/progress validation for no private artifacts.
- [x] Task checkbox-32: Add fixture-only validation for public permit lifecycle category records.
- [x] Task checkbox-33: Add lifecycle requirement extraction diagnostics for narrow recovery tasks.
- [x] Task checkbox-34: Add recovery guardrails for syntactic validity after failed mutation patches.
- [x] Task checkbox-35: Recovery for checkbox-27e with syntax-valid confidence comparisons.
- [x] Task checkbox-36: Recovery for checkbox-27f duplicate requirement-key mutation validation.
- [x] Task checkbox-37: Add a fixture-only process-model schema test for one public PP&D permit process record.
- [x] Task checkbox-38: Add the smallest committed synthetic public-process fixture that passes checkbox-37.
- [x] Task checkbox-39: Add one mutation test proving process-model validation rejects a stage without source evidence.
- [x] Task checkbox-40: Add one mutation test proving process-model validation rejects a required document without a cited source evidence ID.
- [x] Task checkbox-41: Add a fixture-only missing-information schema test that derives missing user facts from the committed process fixture.
- [x] Task checkbox-42: Add the smallest committed missing-information fixture for checkbox-41 using placeholder user case facts and public-only citations.
- [x] Task checkbox-43: Add one mutation test proving missing-information validation rejects a requested user fact that has no linked process requirement.
- [x] Task checkbox-44: Add a fixture-only guardrail mapping test that maps one process stop gate to an agent action gate.
- [x] Task checkbox-45: Add the smallest committed guardrail mapping fixture for checkbox-44.
- [x] Task checkbox-46: Add one mutation test proving guardrail mapping validation rejects consequential or financial actions unless an explicit confirmation field is present and false by default in fixtures.
- [x] Task checkbox-47: Add a public-crawl dry-run plan fixture that lists seed URLs, allowlist decisions, robots/no-persist preflight fields, timeout policy, and skipped-URL reason codes without performing network access.
- [x] Task checkbox-48: Add validation for the public-crawl dry-run plan fixture from checkbox-47. Superseded and satisfied by checkbox-59 after fixture-shape diagnostics corrected the validator assumptions.
- [x] Task checkbox-49: Add a daemon syntax-preflight step that checks only changed Python and TypeScript files before full validation.
- [x] Task checkbox-50: Add daemon prompt guidance and failure-context diagnostics for syntax-preflight rollbacks.
- [x] Task checkbox-51: Resume checkbox-48 with the smallest fixture-first validator after checkbox-49 and checkbox-50 pass. Superseded and satisfied by checkbox-59.
- [x] Task checkbox-52: Wire the existing `ppd/daemon/syntax_preflight.py` helper into `ppd/daemon/ppd_daemon.py` apply flow.
- [x] Task checkbox-53: Add daemon self-test coverage that proves syntax-preflight runs no commands when no changed Python or TypeScript files are present.
- [x] Task checkbox-54: Add one daemon unit-style fixture for syntax-preflight failure classification using a synthetic changed Python filename and compact parser diagnostics only.
- [x] Task checkbox-55: Resume checkbox-48 only after checkbox-52 through checkbox-54 pass. Superseded and satisfied by checkbox-59.
- [x] Task checkbox-56: Add a narrow daemon fixture-shape diagnostic helper under `ppd/daemon/` for JSON fixtures.
- [x] Task checkbox-57: Wire the fixture-shape diagnostic into daemon failure-context guidance for validation failures that mention missing required fields in JSON fixtures.
- [x] Task checkbox-58: Add daemon self-test coverage proving the fixture-shape guidance appears after a failed validator reports absent fields.
- [x] Task checkbox-59: Resume checkbox-48 only after checkbox-56 through checkbox-58 pass.
- [x] Task checkbox-60: Add a fixture-only crawl-plan to processor-handoff validation test.
- [x] Task checkbox-61: Add a small PP&D source-provenance continuity test.
- [x] Task checkbox-62: Add a fixture-only Playwright form-state contract test for DevHub draft pages using accessible selectors, labels, roles, required flags, redacted values, and no live browser session.

## Next Goal-Aligned Tranche

- [x] Task checkbox-63: Add a Playwright draft-action preview fixture test proving reversible draft fills are represented as previews and do not include upload, submit, certify, payment, cancellation, MFA, CAPTCHA, or inspection scheduling actions. Blocked pending a narrow fixture-shape retry plan after validation showed the committed fixture does not expose `draftActionPreviews`.
- [x] Task checkbox-64: Add a guardrail-to-Playwright mapping fixture that links one missing-information fact to one reversible form field and one explicit stop gate, with source evidence IDs and redacted before/after values only.
- [x] Task checkbox-65: Add a daemon stale-blocked-task reconciliation test proving superseded blocked tasks are not reselected when a later accepted task explicitly satisfies the same recovery goal.
- [x] Task checkbox-66: Add a daemon prompt/preflight guardrail for repeated no-accepted-patch LLM rounds. Keep this to `ppd/daemon/` only and add a synthetic self-test proving that after four consecutive failed or empty proposal rounds, the next prompt asks for one narrow fixture-first file set, requires complete JSON file replacements, and forbids live DevHub sessions or broad contract rewrites. Do not implement the DevHub form-state domain test in this task.
- [x] Task checkbox-67: Resume checkbox-62 only after checkbox-66 passes. Use one syntax-valid Python unittest file, or one small redacted fixture plus one unittest file, that validates the committed or synthetic DevHub draft-page form-state fixture shape with accessible selectors, labels, roles, required flags, redacted values, and no browser launch. Do not add Playwright runtime automation, private auth state, screenshots, traces, uploads, submissions, payments, MFA, CAPTCHA, cancellation, certification, or inspection scheduling.
- [x] Task checkbox-68: Add a daemon fixture-shape retry self-test for DevHub draft-action preview validation failures. Use only `ppd/daemon/` or `ppd/tests/`, keep it synthetic, and prove KeyError or assertion failures for absent fixture keys such as `draftActionPreviews` produce guidance to inspect the committed fixture shape before retrying. Do not edit DevHub fixtures or implement the domain validator in this task.
- [x] Task checkbox-69: Resume checkbox-63 only after checkbox-68 passes. Use at most one redacted fixture plus one syntax-valid Python unittest file, inspect the committed `ppd/tests/fixtures/devhub/draft_action_preview.json` shape first, and either align the test to existing keys or replace the fixture with the smallest preview-only shape. Do not add Playwright runtime automation, private auth state, screenshots, traces, uploads, submissions, payments, MFA, CAPTCHA, cancellation, certification, or inspection scheduling.

## Next Goal-Aligned Tranche

- [x] Task checkbox-70: Add a fixture-only Playwright accessible-selector contract for one mocked DevHub permit form page. Validate role, accessible name, label text, nearby heading, required flag, redacted value, and stable selector basis only; do not launch a browser or touch live DevHub.
- [x] Task checkbox-71: Add a Playwright action-classification fixture that maps mocked form interactions to read-only, reversible draft-edit, consequential, and financial classes, with exact-confirmation defaults set to false.
- [x] Task checkbox-72: Add a guardrail test proving upload, submit, certify, pay, cancel, schedule inspection, MFA, CAPTCHA, account creation, and password recovery actions are refused in Playwright planning fixtures unless exact explicit user confirmation is present.
- [x] Task checkbox-73: Add a missing-information to form-field mapping fixture that links one required PP&D user fact to one mocked DevHub field, one source evidence ID, and one reversible draft-preview action.
- [x] Task checkbox-74: Add a source-evidence continuity test that confirms every Playwright planning fixture references an existing process, requirement, or public source evidence fixture and uses redacted values only.
- [x] Task checkbox-75: Add daemon no-eligible-task replanning guidance that treats `complete == task_count` with expanded goals as a prompt to append the next fixture-first tranche instead of invoking repeated repair on stale progress.

## Next Goal-Aligned Tranche

- [x] Task checkbox-76: Add a Playwright audit-event continuity fixture that records selector basis, source requirement, action classification, user-confirmation state, and redacted before/after field state for a reversible draft edit only.
- [x] Task checkbox-77: Add validation proving Playwright audit-event fixtures reject private auth state, cookies, traces, screenshots, raw browser storage, uploads, submissions, payments, certifications, cancellations, MFA, CAPTCHA, and inspection scheduling actions.
- [x] Task checkbox-78: Add a fixture-only DevHub recorder-state transition map that links accessible selector contracts, draft-action previews, and audit events without launching Playwright or touching live DevHub.
- [x] Task checkbox-79: Add an agent planning fixture that combines missing information, guardrail stop gates, Playwright draft previews, and source evidence into one reversible draft-only plan.
- [x] Task checkbox-80: Add a PP&D processor-archive provenance fixture that links public crawl dry-run URLs to processor handoff manifests, source-index records, and normalized document provenance without invoking network or processor code.
- [x] Task checkbox-81: Add daemon replenishment validation proving a completed board can be extended with a new goal-aligned tranche while preserving accepted-work history and avoiding stale supervisor repair counts.

## Replenished Goal-Aligned Tranche

- [x] Task checkbox-82: Add a formal-logic planner integration fixture that maps one extracted PP&D requirement, one missing user fact, one stop gate, and one reversible draft-only Playwright action into a single agent guardrail bundle.
- [x] Task checkbox-83: Add processor archive manifest validation that proves the PP&D handoff can reference ipfs_datasets_py processor provenance, source index records, and normalized document IDs without network, raw crawl output, or private DevHub artifacts.
- [x] Task checkbox-84: Add a mocked Playwright form-fill planning fixture that ranks accessible selectors by evidence confidence and refuses low-confidence selectors before any live browser session is launched.
- [x] Task checkbox-85: Add a missing-information resolution fixture that converts unresolved PP&D user facts into a minimal questionnaire while preserving source evidence, redaction, and action-classification guardrails.
- [x] Task checkbox-86: Add supervisor no-available-task fallback validation proving the supervisor can append a deterministic fixture-first tranche if Codex planning fails or times out.
- [x] Task checkbox-87: Add an autonomous draft-session audit ledger fixture that links source evidence, guardrails, selector confidence, user-confirmation state, and reversible form mutations without storing screenshots, traces, cookies, auth state, or raw browser storage.

## Replenished Goal-Aligned Tranche

- [x] Task checkbox-88: Add a fixture-only public PP&D change-monitoring plan that lists one high-change guidance page, one low-change PDF or form artifact, recrawl cadence, hash/header fields, and change-report categories without network access, raw crawl output, or downloaded documents.
- [x] Task checkbox-89: Add validation for the change-monitoring plan fixture proving each watched source has canonical URL provenance, content-hash or HTTP-cache metadata placeholders, a recrawl cadence, and skipped-action reasons for live crawl and private DevHub data.
- [x] Task checkbox-90: Add a fixture-only public form-field extraction contract for one PP&D application or checklist sample that records required labels, enumerated options, signature or acknowledgment markers, source page anchors, and redacted placeholder values only.
- [x] Task checkbox-91: Add validation that form-field extraction fixtures reject uncited required fields, raw PDF bodies, downloaded document bytes, private user values, and any instruction to submit, certify, upload, pay, cancel, or schedule inspections.
- [x] Task checkbox-92: Add a fixture-only source-diff report that compares two synthetic versions of one public PP&D requirement and classifies added, removed, and changed obligations with citations and confidence values.
- [x] Task checkbox-93: Add validation for source-diff fixtures proving changed requirements preserve prior and current source evidence, stable requirement IDs, review-needed flags, and fail-closed agent impact summaries.
- [x] Task checkbox-94: Add a mocked DevHub workflow-resume fixture that models read-only draft discovery and missing-field detection from redacted state only, with no browser launch, auth state, cookies, traces, screenshots, uploads, submissions, payments, MFA, CAPTCHA, cancellation, certification, or inspection scheduling.
- [x] Task checkbox-95: Add validation for mocked workflow-resume fixtures proving the allowed actions are limited to safe read-only inspection and reversible draft previews, while consequential and financial actions require exact confirmation and remain refused by default.

## Replenished Goal-Aligned Tranche

- [x] Task checkbox-96: Add a fixture-only exact-confirmation checkpoint contract for mocked DevHub consequential and financial actions, with redacted action previews, source-backed consequence summaries, durable audit-event references, and default refusal before confirmation. Do not launch a browser, store auth state, upload, submit, certify, pay, cancel, schedule inspections, automate MFA or CAPTCHA, or use live DevHub.
- [x] Task checkbox-97: Add validation for exact-confirmation checkpoint fixtures proving vague confirmations, stale source evidence, private values, missing audit-event IDs, and mismatched action strings are rejected before any consequential or financial DevHub action can be planned.
- [x] Task checkbox-98: Add a fixture-only public PP&D requirement-boundary sample that separates legal or procedural obligations from operational DevHub UI behavior for one permit process, preserving source evidence IDs, requirement type, confidence, and review-needed flags.
- [x] Task checkbox-99: Add validation for requirement-boundary fixtures proving legal obligations, operational UI hints, user facts, document requirements, fee notices, and deadlines are classified separately and fail closed when citations or review-needed flags are missing.
- [x] Task checkbox-100: Add a fixture-only public PDF extraction contract for one PP&D checklist or form sample that records document metadata, page-number anchors, required document labels, signature or acknowledgment markers, and extracted text snippets only; do not download documents or store raw PDF bytes.
- [~] Task checkbox-101: Add validation for public PDF extraction fixtures proving page anchors, source URLs, checksums or placeholder hash fields, redacted values, and skipped raw-byte/OCR-output reasons are present, while raw bodies and private DevHub artifacts are rejected.
- [ ] Task checkbox-102: Add a fixture-only redacted user-case-state contract that links a mocked project fact inventory, missing-information questions, uploaded-file placeholders, draft status, and source evidence without storing private documents, account identifiers, cookies, traces, screenshots, payments, or live DevHub state.
- [ ] Task checkbox-103: Add validation for user-case-state fixtures proving missing facts, file placeholders, draft/submitted status, payment status, messages, and outstanding tasks remain redacted, source-linked, and blocked from consequential or financial action planning by default.

## Generated Status

Last updated: 2026-05-02T06:45:00Z

- Latest target: `Supervisor repair after repeated validation failure while targeting checkbox-63.`
- Latest result: `supervisor_repair_replanned`
- Latest summary: Blocked the draft-action preview domain retry behind a narrow daemon fixture-shape guidance self-test, then queued a constrained fixture-first retry.



## Generated Status

Last updated: 2026-05-02T18:21:22.136761Z

- Latest target: `Task checkbox-92: Task checkbox-87: Add an autonomous draft-session audit ledger fixture that links source evidence, guardrails, selector confidence, user-confirmation state, and reversible form mutations without storing screenshots, traces, cookies, auth state, or raw browser storage.`
- Latest result: `accepted`
- Latest summary: Add a narrow redacted DevHub draft audit ledger fixture and focused validation test.
- Counts: `{"blocked": 0, "complete": 92, "in_progress": 0, "needed": 0}`



## Generated Status

Last updated: 2026-05-02T18:35:29.491670Z

- Latest target: `Task checkbox-100: Task checkbox-95: Add validation for mocked workflow-resume fixtures proving the allowed actions are limited to safe read-only inspection and reversible draft previews, while consequential and financial actions require exact confirmation and remain refused by default.`
- Latest result: `accepted`
- Latest summary: Add fixture-only workflow-resume action-gate validation for mocked DevHub resume states.
- Counts: `{"blocked": 0, "complete": 100, "in_progress": 0, "needed": 8}`


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-02T19:30:44.327882Z

- Latest target: `Task checkbox-106: Task checkbox-101: Add validation for public PDF extraction fixtures proving page anchors, source URLs, checksums or placeholder hash fields, redacted values, and skipped raw-byte/OCR-output reasons are present, while raw bodies and private DevHub artifacts are rejected.`
- Latest result: `syntax_preflight`
- Latest summary: Add a narrow public PDF extraction fixture and validator for checkbox-106.
- Counts: `{"blocked": 0, "complete": 105, "in_progress": 0, "needed": 3}`

<!-- ppd-daemon-task-board:end -->
