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

- [!] Task checkbox-63: Add a Playwright draft-action preview fixture test proving reversible draft fills are represented as previews and do not include upload, submit, certify, payment, cancellation, MFA, CAPTCHA, or inspection scheduling actions. Blocked pending a narrow fixture-shape retry plan after validation showed the committed fixture does not expose `draftActionPreviews`.
- [x] Task checkbox-64: Add a guardrail-to-Playwright mapping fixture that links one missing-information fact to one reversible form field and one explicit stop gate, with source evidence IDs and redacted before/after values only.
- [x] Task checkbox-65: Add a daemon stale-blocked-task reconciliation test proving superseded blocked tasks are not reselected when a later accepted task explicitly satisfies the same recovery goal.
- [x] Task checkbox-66: Add a daemon prompt/preflight guardrail for repeated no-accepted-patch LLM rounds. Keep this to `ppd/daemon/` only and add a synthetic self-test proving that after four consecutive failed or empty proposal rounds, the next prompt asks for one narrow fixture-first file set, requires complete JSON file replacements, and forbids live DevHub sessions or broad contract rewrites. Do not implement the DevHub form-state domain test in this task.
- [x] Task checkbox-67: Resume checkbox-62 only after checkbox-66 passes. Use one syntax-valid Python unittest file, or one small redacted fixture plus one unittest file, that validates the committed or synthetic DevHub draft-page form-state fixture shape with accessible selectors, labels, roles, required flags, redacted values, and no browser launch. Do not add Playwright runtime automation, private auth state, screenshots, traces, uploads, submissions, payments, MFA, CAPTCHA, cancellation, certification, or inspection scheduling.
- [x] Task checkbox-68: Add a daemon fixture-shape retry self-test for DevHub draft-action preview validation failures. Use only `ppd/daemon/` or `ppd/tests/`, keep it synthetic, and prove KeyError or assertion failures for absent fixture keys such as `draftActionPreviews` produce guidance to inspect the committed fixture shape before retrying. Do not edit DevHub fixtures or implement the domain validator in this task.
- [~] Task checkbox-69: Resume checkbox-63 only after checkbox-68 passes. Use at most one redacted fixture plus one syntax-valid Python unittest file, inspect the committed `ppd/tests/fixtures/devhub/draft_action_preview.json` shape first, and either align the test to existing keys or replace the fixture with the smallest preview-only shape. Do not add Playwright runtime automation, private auth state, screenshots, traces, uploads, submissions, payments, MFA, CAPTCHA, cancellation, certification, or inspection scheduling.

## Generated Status

Last updated: 2026-05-02T06:45:00Z

- Latest target: `Supervisor repair after repeated validation failure while targeting checkbox-63.`
- Latest result: `supervisor_repair_replanned`
- Latest summary: Blocked the draft-action preview domain retry behind a narrow daemon fixture-shape guidance self-test, then queued a constrained fixture-first retry.


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-02T16:44:47.272484Z

- Latest target: `Task checkbox-73: Task checkbox-68: Add a daemon fixture-shape retry self-test for DevHub draft-action preview validation failures. Use only `ppd/daemon/` or `ppd/tests/`, keep it synthetic, and prove KeyError or assertion failures for absent fixture keys such as `draftActionPreviews` produce guidance to inspect the committed fixture shape before retrying. Do not edit DevHub fixtures or implement the domain validator in this task.`
- Latest result: `accepted`
- Latest summary: Broadened daemon fixture-shape retry guidance to recognize absent-key KeyError/assertion failures and added synthetic DevHub preview guidance tests.
- Counts: `{"blocked": 1, "complete": 72, "in_progress": 0, "needed": 1}`

<!-- ppd-daemon-task-board:end -->
