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
- [x] Task checkbox-196: Add one daemon-only parser-clean diagnostic helper or unittest that converts repeated non-JSON LLM output into target_task, failure_kind, compact_raw_response_summary, and next_action_hint without storing the full raw response.
- [x] Task checkbox-199: Add one daemon-only blocked-selection unittest using plain string parsing, not custom regex named-group syntax, proving blocked checkbox-178/182/186/187/191/193/194/195/197 are skipped when a fresh unchecked daemon-repair task exists.
- [x] Task checkbox-200: Add one parser-clean daemon retry-scope unittest proving a syntax_preflight history for checkbox-178 rejects a three-file source-plus-fixture-plus-test proposal and allows exactly one parser-bearing file or exactly one daemon repair file.
- [x] Task checkbox-201: Add one daemon-only stale-calling-llm recovery unittest proving a task stuck in `calling_llm` for a blocked target is summarized as a compact supervisor diagnostic and the newest unchecked daemon-repair task remains selectable without retrying checkbox-178.
- [x] Task checkbox-202: Add one parser-clean daemon preflight unittest proving a proposal after checkbox-178 syntax_preflight history is rejected when it edits any DevHub domain file without also being the single parser-bearing repair file under test.

## Blocked Work

- [x] Task checkbox-178: Add a fixture-only DevHub draft-readiness decision matrix plus focused validation that combines missing facts, redacted file placeholders, selector confidence, upload-readiness gates, fee notices, and exact-confirmation defaults while refusing official actions.
- [x] Task checkbox-182: Add daemon diagnostics coverage proving repeated non-JSON LLM responses for a blocked task are persisted with target task, failure kind, compact raw-response summary, and a next-action hint before the worker exits.
- [x] Task checkbox-186: Add daemon retry-scope coverage proving that after two syntax_preflight failures on checkbox-178, the next prompt permits either one parser-bearing file or one daemon repair file, and rejects source-plus-fixture-plus-test bundles.
- [x] Task checkbox-187: Add blocked-task selection coverage proving that when checkbox-178 and checkbox-182 are both blocked, the daemon selects the newest unchecked daemon-repair task from this tranche before retrying either blocked task.
- [x] Task checkbox-191: Add supervisor recovery-note compaction coverage proving repeated repair notes are summarized before future prompt construction so task-board context stays bounded.
- [x] Task checkbox-193: Add one focused daemon diagnostic unittest proving a repeated non-JSON LLM response records target_task, failure_kind, compact raw-response summary, and next_action_hint without storing the full raw response.
- [x] Task checkbox-194: Add one parser-clean supervisor recovery-note compaction helper or fixture test that summarizes repeated repair notes before prompt construction without touching DevHub, crawler, extraction, logic, or domain fixtures.
- [x] Task checkbox-195: Replace or add only `ppd/daemon/SUPERVISOR_REPAIR_GUIDE.md` with parser-failure recovery rules that name the recent malformed Python fragments, require syntax-valid one-file retries, and keep repair separate from PP&D domain implementation.
- [x] Task checkbox-197: Add one daemon-only retry-scope helper or unittest proving a blocked-only board selects a new unchecked daemon-repair task before revisiting checkbox-178, checkbox-182, checkbox-186, checkbox-187, checkbox-191, checkbox-193, or checkbox-194.
- [x] Task checkbox-198: Replace only `ppd/daemon/SUPERVISOR_REPAIR_GUIDE.md` with the exact parser-recovery phrases expected by existing supervisor guide tests, including `must not implement the stalled PP&D domain task directly`, while keeping the file documentation-only.
- [x] Task checkbox-203: Add one daemon diagnostics helper or focused unittest proving compact failure summaries include target_task, failure_kind, next_action_hint, and a raw-response length cap while excluding private DevHub artifacts, auth state, traces, crawl output, and downloaded documents.

## Supervisor Repair Notes

- Parked repeated syntax_preflight rollbacks for checkbox-178. The next retry must first improve daemon prompt, syntax guardrails, retry-scope validation, or replace only the parser-bearing file with no new fixture contract.
- Parked repeated malformed generated Python string literals for checkbox-182 and checkbox-191. Recovery must be parser-clean first and behavior-rich second.
- The daemon reached a blocked-only board on 2026-05-03, so this board appends narrow daemon-repair tasks that can run independently before any blocked domain task is retried.
- Tranche 15 and Tranche 16 keep recovery in ppd/daemon and ppd/tests only. They do not implement DevHub draft readiness, live crawling, authenticated automation, upload, payment, submission, certification, cancellation, or inspection scheduling.
- Tranche 16 is intentionally small after repeated parser and regex failures: each task should change either one daemon file or one focused daemon test file unless the selected task explicitly requires both.
- Tranche 17 replenished independent daemon-repair work after the supervisor reported no selectable tasks while checkbox-178 remained active in calling_llm.
- Tranche 18 keeps recovery moving after all previous repair tasks became blocked or completed. These tasks must stay daemon-scoped and must not implement checkbox-178 directly.
- Tranche 19 adds fresh selectable daemon-repair work after checkbox-204 through checkbox-207 completed and the board again had no needed task. These tasks are validation-first and parser-clean by design.
- Tranche 20 was added manually after Tranche 19 became fully blocked and the daemon, running with blocked revisits enabled, retried blocked checkbox-178. These tasks keep recovery in daemon tests and selection policy before any DevHub draft-readiness retry.

## Blocked Cascade Recovery Tranche 18

- [x] Task checkbox-204: Add one parser-clean daemon unittest proving that a blocked-only board with stale `calling_llm` status appends or selects exactly one unchecked daemon-repair task and does not select checkbox-178, checkbox-182, checkbox-186, checkbox-187, checkbox-191, checkbox-193, checkbox-194, checkbox-195, checkbox-197, checkbox-198, or checkbox-203.
- [x] Task checkbox-205: Add one narrow daemon helper or unittest proving syntax_preflight failures with `py_compile` details generate a next_action_hint that says to replace only one syntactically failing Python file or one daemon repair file before any domain retry.
- [x] Task checkbox-206: Add one daemon prompt-guard fixture or unittest proving that after two syntax_preflight failures for checkbox-178, the prompt explicitly forbids source-plus-fixture-plus-test bundles and recommends a one-file parser-clean repair.
- [x] Task checkbox-207: Clean up duplicated generated-status blocks in `ppd/daemon/task-board.md` with a documentation-only replacement that preserves all completed and blocked task checkboxes and leaves the active unchecked Tranche 18 tasks intact.

## Blocked Cascade Recovery Tranche 19

- [x] Task checkbox-208: Add one daemon-only parser-clean unittest proving a blocked-only board with stale `calling_llm` for checkbox-178 produces a new unchecked daemon-repair task and does not reopen checkbox-178, checkbox-182, checkbox-186, checkbox-187, checkbox-191, checkbox-193, checkbox-194, checkbox-195, checkbox-197, checkbox-198, or checkbox-203.
- [x] Task checkbox-209: Add one narrow daemon helper or unittest proving repeated non-JSON LLM responses are persisted as compact diagnostics with target_task, failure_kind, compact_raw_response_summary, and next_action_hint while capping response text and excluding private artifact markers.
- [x] Task checkbox-210: Add one parser-clean daemon prompt-scope unittest proving that after two syntax_preflight failures for checkbox-178, a retry prompt permits exactly one parser-bearing file or one daemon repair file and rejects source-plus-fixture-plus-test bundles before any DevHub domain retry.

## Manual Recovery Tranche 20

- [x] Task checkbox-211: Add one daemon-only unittest proving `select_task` does not choose blocked checkbox-178 when a fresh unchecked daemon-repair task exists, even if `revisit_blocked` is enabled.
- [x] Task checkbox-212: Add one supervisor regression proving a blocked-only PP&D board appends a fresh daemon-repair tranche before restarting a worker with blocked revisits enabled.
- [x] Task checkbox-213: Add one parser-clean prompt-scope unittest proving checkbox-178 retries stay blocked after three syntax_preflight failures until a daemon-repair task passes validation.
- [x] Task checkbox-214: Add one task-board accounting unittest proving duplicate generated-status sections outside the managed marker are detected before daemon task selection.


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-03T20:03:28.802435Z

- Latest target: `Task checkbox-225: Add autonomous platform continuation coverage for tranche 2 proving whole-site archival, Playwright draft automation, PDF field filling, and formal-logic outputs stay connected through source evidence IDs.`
- Latest result: `syntax_preflight`
- Latest summary: Add fixture-first tranche 2 coverage tying whole-site archival, Playwright draft automation, PDF field filling, and formal-logic outputs to shared source evidence IDs.
- Counts: `{"blocked": 0, "complete": 54, "in_progress": 0, "needed": 4}`

<!-- ppd-daemon-task-board:end -->
## Built-In Supervisor Repair Notes

- Parked repeated syntax-preflight loop for `Add one daemon-only parser-clean unittest proving a blocked-only board with stale `calling_llm` for checkbox-178 produces a new unchecked daemon-repair task and does not reopen checkbox-178, checkbox-182, checkbox-186, checkbox-187, checkbox-191, checkbox-193, checkbox-194, checkbox-195, checkbox-197, checkbox-198, or checkbox-203.` so the daemon can continue with independent selectable work. The task should be resumed only after a narrow syntax-valid fixture/test repair is available.

## Built-In Blocked Cascade Recovery Tranche

- [x] Task checkbox-215: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 1 proving blocked PP&D work stays parked until a fresh daemon repair task validates.
- [x] Task checkbox-216: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 2 proving blocked PP&D work stays parked until a fresh daemon repair task validates.
- [x] Task checkbox-217: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 3 proving blocked PP&D work stays parked until a fresh daemon repair task validates.
- [x] Task checkbox-218: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 4 proving blocked PP&D work stays parked until a fresh daemon repair task validates.

## Built-In Supervisor Repair Notes

- Appended deterministic blocked-cascade recovery tasks because all selectable work was blocked. The supervisor avoided the LLM repair path and created daemon-repair tasks that can run independently before blocked domain work is retried.

## Built-In Autonomous PP&D Platform Tranche

- [x] Task checkbox-219: Add a side-effect-free whole-site PP&D archival plan under ppd/crawler that models full public-site discovery, processor-suite handoff, PDF normalization, requirement extraction, and formal-logic outputs without live crawling or private artifacts.
- [x] Task checkbox-220: Add validation coverage for the whole-site PP&D archival plan proving it uses the ipfs_datasets_py processor suite, public allowlists, robots preflight, bounded retries, and no raw crawl, browser, or private DevHub artifacts.
- [x] Task checkbox-221: Add a side-effect-free Playwright and PDF draft automation plan under ppd/devhub that models user-authorized draft form fills, local PDF field fills, audit events, and exact-confirmation checkpoints without live login or official actions.
- [x] Task checkbox-222: Add validation coverage for Playwright and PDF draft automation proving reversible draft fills are allowed while upload, submit, payment, certification, cancellation, inspection scheduling, MFA, CAPTCHA, and account creation remain refused by default.
- [x] Task checkbox-223: Add supervisor completed-board regression coverage proving an all-complete PP&D board appends the autonomous platform tranche and restarts the daemon instead of idling with no available work.
- [x] Task checkbox-224: Add daemon/supervisor operations coverage proving watch mode starts the next cycle immediately after each task, relies on LLM and validation timeouts to avoid hangs, and leaves supervisor replanning responsible for empty boards.

## Built-In Supervisor Planning Notes

- The completed PP&D recovery board now advances into autonomous platform work. This tranche is aligned to whole-site public archival, ipfs_datasets_py processor-suite handoff, guarded Playwright draft automation, local PDF field filling, and formal-logic guardrail extraction.
- Slice policy: `autonomous_platform_after_completed_recovery`. The supervisor uses this deterministic tranche when an all-complete PP&D board would otherwise leave the daemon with no work.

## Built-In Autonomous PP&D Platform Tranche 2

- [~] Task checkbox-225: Add autonomous platform continuation coverage for tranche 2 proving whole-site archival, Playwright draft automation, PDF field filling, and formal-logic outputs stay connected through source evidence IDs.
- [ ] Task checkbox-226: Add processor-suite integration planning for tranche 2 proving PP&D public documents flow through archive manifests, normalized document records, PDF metadata, and requirement batches before agents use them.
- [ ] Task checkbox-227: Add Playwright/PDF handoff validation for tranche 2 proving redacted user facts can fill draft fields and PDF previews while official DevHub transitions stay behind exact confirmation checkpoints.
- [ ] Task checkbox-228: Add supervisor idle-recovery validation for tranche 2 proving completed boards synthesize new goal-aligned platform tasks without sleeping, duplicate tranche reuse, or blocked-task retry churn.
