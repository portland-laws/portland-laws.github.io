# PP&D Daemon Task Board

This board is the controlling backlog for the isolated PP&D daemon. The daemon should run one unchecked task per cycle, keep changes narrow, and validate before accepting work.

## Operating Rules

- Work only under ppd/ unless a task explicitly names an allowed operations document.
- Do not create private DevHub session files, auth state, traces, raw crawl output, downloaded documents, or live crawl artifacts.
- Do not automate CAPTCHA, MFA, account creation, payment, official submission, certification, cancellation, upload, or inspection scheduling.
- Prefer fixture-first and validation-first work before live public crawling or authenticated automation.
- Keep every task small enough for one daemon cycle.
- Preserve source provenance in every public guidance, requirement, process, and guardrail fixture.
- After any rollback containing SyntaxError, py_compile, TS1005, TS1109, or TS1128, do not retry a broad contract rewrite. First repair daemon supervision so changed Python or TypeScript files are syntax-checked before full validation.
- Syntax-recovery proposals should normally replace one file only. Use two files only when the second file is a tiny focused test or fixture for the same syntactic guardrail.
- Python proposals must not contain TypeScript-style annotations in expressions, such as if value list[str]. TypeScript proposals must not contain Python control-flow or type syntax.
- When a domain task has failed twice for parser or compile reasons, block that task and append narrower daemon-repair tasks before resuming the domain task.
- If a syntax-preflight helper exists, the daemon apply path must call it before full validation and must classify parser failures as syntax_preflight.
- If no unchecked task remains because every selectable item is blocked, append daemon-repair tasks instead of revisiting blocked domain work by default.
- For checkbox-178, checkbox-182, checkbox-186, checkbox-187, and checkbox-191 recovery, prefer daemon diagnostics, retry scoping, task selection, or prompt/preflight repairs under ppd/daemon/ before adding any ppd/devhub/ implementation file.
- Any retry that mentions repeated non-JSON LLM responses must persist only compact response summaries, never raw full responses, private session data, auth state, traces, crawl output, or downloaded documents.

## Completed Work

- [x] Task checkbox-01 through checkbox-171: Completed PP&D bootstrap, validation, fixture, provenance, DevHub draft-planning, formal-logic guardrail, supervisor recovery, and replenishment tasks preserved from the existing board.
- [x] Task checkbox-172: Add supervisor validation-failure classification coverage proving forbidden-marker self-triggering fixture fields are detected and converted into neutral absence-field repair guidance.
- [x] Task checkbox-173: Add daemon prompt-repair coverage proving validation failures from forbidden marker substrings produce a JSON-only retry instruction with neutral artifact field names.
- [x] Task checkbox-174: Add supervisor stale-status reconciliation coverage proving a no-eligible or calling_llm status with a completed board triggers deterministic replanning instead of observe or restart churn.
- [x] Task checkbox-175: Add daemon LLM result-persistence coverage proving parse, timeout, validation-interrupted, and vanished-child failures are recorded before the worker exits or restarts.
- [x] Task checkbox-176: Add a fixture-only public source lineage rollup plus focused validation that summarizes PP&D seed URLs, processor handoff manifests, normalized document IDs, source freshness records, and skipped-action reasons without live crawling or raw response bodies.
- [x] Task checkbox-177: Add validation for source lineage rollups proving every lineage edge is citation-backed, uses stable public identifiers, excludes private DevHub artifacts, and marks stale or conflicting evidence review-needed before downstream guardrails reuse it.
- [x] Task checkbox-179: Add a fixture-only formal-logic contradiction packet plus focused validation that detects incompatible PP&D obligations or prerequisites, preserves both provenance chains, marks affected predicates blocked, and asks for human review before agent planning continues.
- [x] Task checkbox-180: Add daemon task-selection regression coverage proving that when every domain task is blocked, the supervisor appends or selects a narrow daemon-repair task instead of revisiting blocked checkbox-176 or checkbox-178 work.
- [x] Task checkbox-181: Add daemon prompt-scoping coverage proving syntax_preflight history for a PP&D domain task produces a JSON-only retry instruction limited to one parser-bearing file or one daemon repair file.
- [x] Task checkbox-183: Add syntax-preflight unit coverage for malformed Python fragments seen in draft-readiness retries, including `if confidence None`, while preserving fixture-only validation and avoiding DevHub implementation changes.
- [x] Task checkbox-184: Add a fixture-only daemon prompt fixture proving repeated non-JSON LLM responses for a blocked PP&D task are summarized into target_task, failure_kind, compact_raw_response_summary, and next_action_hint fields without storing the full raw response.
- [x] Task checkbox-185: Add parser-clean daemon diagnostics validation for blocked-task LLM parse loops using one small Python unittest or one daemon helper only; do not touch DevHub, crawler, extraction, logic, or domain fixture contracts in this cycle.
- [x] Task checkbox-188: Add supervisor blocked-cascade recovery coverage proving a board with only blocked domain/recovery tasks gets deterministic daemon-repair tasks without invoking the LLM repair path.
- [x] Task checkbox-189: Add daemon blocked-task prompt-budget fixture coverage proving repeated llm_router exits summarize the target, compact errors, and next daemon-repair hint without retrying blocked domain work.
- [x] Task checkbox-190: Add daemon task-selection coverage proving blocked tasks are skipped until a new non-blocked repair task is accepted or a human explicitly reopens the blocked task.
- [x] Task checkbox-192: Add one parser-clean daemon retry-scope helper or unittest proving that two syntax_preflight failures on checkbox-178 reject source-plus-fixture-plus-test bundles and allow only one parser-bearing file or one daemon repair file.

## Blocked Work

- [!] Task checkbox-178: Add a fixture-only DevHub draft-readiness decision matrix plus focused validation that combines missing facts, redacted file placeholders, selector confidence, upload-readiness gates, fee notices, and exact-confirmation defaults while refusing official actions.
- [!] Task checkbox-182: Add daemon diagnostics coverage proving repeated non-JSON LLM responses for a blocked task are persisted with target task, failure kind, compact raw-response summary, and a next-action hint before the worker exits.
- [!] Task checkbox-186: Add daemon retry-scope coverage proving that after two syntax_preflight failures on checkbox-178, the next prompt permits either one parser-bearing file or one daemon repair file, and rejects source-plus-fixture-plus-test bundles.
- [!] Task checkbox-187: Add blocked-task selection coverage proving that when checkbox-178 and checkbox-182 are both blocked, the daemon selects the newest unchecked daemon-repair task from this tranche before retrying either blocked task.
- [!] Task checkbox-191: Add supervisor recovery-note compaction coverage proving repeated repair notes are summarized before future prompt construction so task-board context stays bounded.
- [!] Task checkbox-193: Add one focused daemon diagnostic unittest proving a repeated non-JSON LLM response records target_task, failure_kind, compact raw-response summary, and next_action_hint without storing the full raw response.
- [!] Task checkbox-194: Add one parser-clean supervisor recovery-note compaction helper or fixture test that summarizes repeated repair notes before prompt construction without touching DevHub, crawler, extraction, logic, or domain fixtures.

## Supervisor Repair Notes

- Parked repeated syntax_preflight rollbacks for checkbox-178. The next retry must first improve daemon prompt, syntax guardrails, retry-scope validation, or replace only the parser-bearing file with no new fixture contract.
- Parked repeated malformed generated Python string literals for checkbox-182 and checkbox-191. Recovery must be parser-clean first and behavior-rich second.
- The daemon reached a blocked-only board on 2026-05-03, so this board appends narrow daemon-repair tasks that can run independently before any blocked domain task is retried.
- Tranche 15 keeps recovery in ppd/daemon and ppd/tests only. It does not implement DevHub draft readiness, live crawling, authenticated automation, upload, payment, submission, certification, cancellation, or inspection scheduling.

## Blocked Cascade Recovery Tranche 15

- [!] Task checkbox-195: Replace or add only `ppd/daemon/SUPERVISOR_REPAIR_GUIDE.md` with parser-failure recovery rules that name the recent malformed Python fragments, require syntax-valid one-file retries, and keep repair separate from PP&D domain implementation.
- [!] Task checkbox-196: Add one daemon-only parser-clean diagnostic helper or unittest that converts repeated non-JSON LLM output into target_task, failure_kind, compact_raw_response_summary, and next_action_hint without storing the full raw response.
- [!] Task checkbox-197: Add one daemon-only retry-scope helper or unittest proving a blocked-only board selects a new unchecked daemon-repair task before revisiting checkbox-178, checkbox-182, checkbox-186, checkbox-187, checkbox-191, checkbox-193, or checkbox-194.


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-06-30T17:32:03.017767Z

- Latest target: `Task checkbox-196: Add one daemon-only parser-clean diagnostic helper or unittest that converts repeated non-JSON LLM output into target_task, failure_kind, compact_raw_response_summary, and next_action_hint without storing the full raw response.`
- Latest result: `validation`
- Latest summary: Add daemon-only parser-clean diagnostics for repeated non-JSON LLM output with focused unittest coverage.
- Counts: `{"blocked": 10, "complete": 17, "in_progress": 0, "needed": 0}`

<!-- ppd-daemon-task-board:end -->
