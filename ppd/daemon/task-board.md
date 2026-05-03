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
- When a fixture-validator task fails because expected fields are absent, do not immediately rewrite the fixture or add a broader contract. First add a daemon diagnostic or prompt guardrail that reports the committed fixture shape and constrains the next retry to the fields actually present unless the task explicitly permits fixture replacement.
- After four consecutive daemon rounds without an accepted patch while the daemon is in calling_llm, pause the active domain task and append a narrow daemon prompt/preflight repair before retrying the domain task.

## Completed Work

- [x] Task checkbox-01 through checkbox-171: Completed PP&D bootstrap, validation, fixture, provenance, DevHub draft-planning, formal-logic guardrail, supervisor recovery, and replenishment tasks preserved from the existing board.
- [x] Task checkbox-172: Add supervisor validation-failure classification coverage proving forbidden-marker self-triggering fixture fields are detected and converted into neutral absence-field repair guidance.
- [x] Task checkbox-173: Add daemon prompt-repair coverage proving validation failures from forbidden marker substrings produce a JSON-only retry instruction with neutral artifact field names.
- [x] Task checkbox-174: Add supervisor stale-status reconciliation coverage proving a no-eligible or calling_llm status with a completed board triggers deterministic replanning instead of observe or restart churn.
- [x] Task checkbox-175: Add daemon LLM result-persistence coverage proving parse, timeout, validation-interrupted, and vanished-child failures are recorded before the worker exits or restarts.

## Built-In Goal Replenishment Tranche 11

- [!] Task checkbox-176: Add a fixture-only public source lineage rollup plus focused validation that summarizes PP&D seed URLs, processor handoff manifests, normalized document IDs, source freshness records, and skipped-action reasons without live crawling or raw response bodies.
- [x] Task checkbox-177: Add validation for source lineage rollups proving every lineage edge is citation-backed, uses stable public identifiers, excludes private DevHub artifacts, and marks stale or conflicting evidence review-needed before downstream guardrails reuse it.
- [~] Task checkbox-178: Add a fixture-only DevHub draft-readiness decision matrix plus focused validation that combines missing facts, redacted file placeholders, selector confidence, upload-readiness gates, fee notices, and exact-confirmation defaults while refusing official actions.
- [ ] Task checkbox-179: Add a fixture-only formal-logic contradiction packet plus focused validation that detects incompatible PP&D obligations or prerequisites, preserves both provenance chains, marks affected predicates blocked, and asks for human review before agent planning continues.

## Built-In Supervisor Planning Notes

- The supervisor reviewed the completed PP&D backlog against the original crawl, extraction, DevHub drafting, and formal-logic guardrail goals and appended the next fixture-first tranche without implementing domain artifacts.
- This tranche keeps the next daemon cycles ordered: public lineage fixture first, validation second, draft-readiness planning third, and formal-logic contradiction handling fourth.
- No live crawl, authenticated DevHub session, raw document download, payment, upload, certification, submission, cancellation, CAPTCHA, MFA, account creation, or inspection scheduling work is authorized by these tasks.
## Built-In Supervisor Repair Notes

- Parked repeated LLM parse/runtime loop for `Add a fixture-only public source lineage rollup plus focused validation that summarizes PP&D seed URLs, processor handoff manifests, normalized document IDs, source freshness records, and skipped-action reasons without live crawling or raw response bodies.` so the daemon can continue with the next independent selectable task. Resume only after prompt, parser, or retry policy has been updated.


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-03T05:26:31.840884Z

- Latest target: `Task checkbox-177: Add validation for source lineage rollups proving every lineage edge is citation-backed, uses stable public identifiers, excludes private DevHub artifacts, and marks stale or conflicting evidence review-needed before downstream guardrails reuse it.`
- Latest result: `accepted`
- Latest summary: Add a narrow source lineage rollup validator with deterministic fixtures and tests.
- Counts: `{"blocked": 1, "complete": 6, "in_progress": 0, "needed": 2}`

<!-- ppd-daemon-task-board:end -->
