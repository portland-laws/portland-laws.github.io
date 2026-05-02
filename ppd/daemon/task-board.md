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

## Completed Work

The previous PP&D daemon tranche is complete. Preserve these completed entries as historical markers; do not reopen them unless a supervisor repair task explicitly asks for a recovery.

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

## Next Ordered Tranche

- [x] Task checkbox-37: Add a fixture-only process-model schema test for one public PP&D permit process record. Validate required fields only: `processId`, `sourceEvidenceIds`, `stages`, `requiredInputs`, `requiredDocuments`, `stopGates`, and `lastReviewed`. Do not add live crawling or DevHub automation.
- [x] Task checkbox-38: Add the smallest committed synthetic public-process fixture that passes checkbox-37. Use redacted/public-only values and at least two source evidence IDs already represented by existing fixture style.
- [x] Task checkbox-39: Add one mutation test proving process-model validation rejects a stage without source evidence. Keep the edit limited to the new process-model test file or its adjacent fixture.
- [x] Task checkbox-40: Add one mutation test proving process-model validation rejects a required document without a cited source evidence ID. Keep this separate from stage validation.
- [x] Task checkbox-41: Add a fixture-only missing-information schema test that derives missing user facts from the committed process fixture. Validate only reversible request fields, not browser actions.
- [x] Task checkbox-42: Add the smallest committed missing-information fixture for checkbox-41 using placeholder user case facts and public-only citations. Do not store PII, account state, screenshots, traces, or uploads.
- [x] Task checkbox-43: Add one mutation test proving missing-information validation rejects a requested user fact that has no linked process requirement.
- [x] Task checkbox-44: Add a fixture-only guardrail mapping test that maps one process stop gate to an agent action gate. Validate action class, consequence summary, and source evidence IDs only.
- [x] Task checkbox-45: Add the smallest committed guardrail mapping fixture for checkbox-44. Use only safe read-only or reversible draft-edit examples; do not include submission, payment, certification, cancellation, upload, or inspection scheduling automation.
- [x] Task checkbox-46: Add one mutation test proving guardrail mapping validation rejects consequential or financial actions unless an explicit confirmation field is present and false by default in fixtures.
- [x] Task checkbox-47: Add a public-crawl dry-run plan fixture that lists seed URLs, allowlist decisions, robots/no-persist preflight fields, timeout policy, and skipped-URL reason codes without performing network access.
- [!] Task checkbox-48: Add validation for the public-crawl dry-run plan fixture from checkbox-47. The validator must fail closed on missing allowlist, robots, timeout, no-persist, or processor-adapter preflight fields. Blocked pending fixture-shape diagnostics after repeated validators expected fields that were absent from the committed fixture.
- [x] Task checkbox-49: Add a daemon syntax-preflight step that checks only changed Python and TypeScript files before full validation. Python files must use `py_compile`; TypeScript files must use the existing strict `tsc --noEmit` command scoped to changed `.ts`/`.tsx` files. On parser failure, rollback immediately with failure kind `syntax_preflight` and compact diagnostics.
- [x] Task checkbox-50: Add daemon prompt guidance and failure-context diagnostics for syntax-preflight rollbacks. When recent failures include `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, the prompt must ask for a one-file or one-test-plus-fixture proposal and forbid broad shared-contract rewrites.
- [!] Task checkbox-51: Resume checkbox-48 with the smallest fixture-first validator after checkbox-49 and checkbox-50 pass. Limit the proposal to one syntax-valid Python test file or one syntax-valid helper plus one test fixture path correction; do not add live crawling or authenticated automation. Blocked because the last validator retry did not match the committed fixture shape.
- [x] Task checkbox-52: Wire the existing `ppd/daemon/syntax_preflight.py` helper into `ppd/daemon/ppd_daemon.py` apply flow. After file replacements are written and before full validation, run changed-file syntax preflight; on parser failure, roll back immediately with failure kind `syntax_preflight`, compact diagnostics, and no broad unittest run. Keep this to one daemon file if possible.
- [x] Task checkbox-53: Add daemon self-test coverage that proves syntax-preflight runs no commands when no changed Python or TypeScript files are present.
- [x] Task checkbox-54: Add one daemon unit-style fixture for syntax-preflight failure classification using a synthetic changed Python filename and compact parser diagnostics only.
- [!] Task checkbox-55: Resume checkbox-48 only after checkbox-52 through checkbox-54 pass. Use a single syntax-valid Python test file that validates the committed `ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json` fixture in place; do not introduce `ppd/contracts/planned_crawl_manifest.py`, live crawling, authenticated automation, or broad shared-contract rewrites. Blocked until the daemon adds fixture-shape diagnostics and retry guidance.
- [x] Task checkbox-56: Add a narrow daemon fixture-shape diagnostic helper under `ppd/daemon/` for JSON fixtures. It must accept a repository-relative fixture path, report top-level keys, obvious list fields, and first object keys only, and include self-test coverage using an in-memory or temporary synthetic JSON object. Do not validate PP&D domain semantics in this helper.
- [~] Task checkbox-57: Wire the fixture-shape diagnostic into daemon failure-context guidance for validation failures that mention missing required fields in JSON fixtures. The prompt must instruct the next worker to inspect the committed fixture shape before writing a validator and must forbid adding broad contracts or live crawl code for the retry.
- [ ] Task checkbox-58: Add daemon self-test coverage proving the fixture-shape guidance appears after a failed validator reports absent fields such as missing seed URLs or missing preflight policy fields. Keep the test synthetic and under `ppd/daemon/` or `ppd/tests/`; do not edit crawler fixtures.
- [ ] Task checkbox-59: Resume checkbox-48 only after checkbox-56 through checkbox-58 pass. Use one syntax-valid Python test file that validates the existing public-crawl dry-run fixture according to its actual committed structure, or use one test file plus one minimal fixture path correction if the fixture path is wrong. Do not add `ppd/contracts/planned_crawl_manifest.py`, live crawling, authenticated automation, or broad shared-contract rewrites.


## Generated Status

Last updated: 2026-05-02T06:20:00Z

- Latest target: `Task checkbox-55: Resume checkbox-48 only after checkbox-52 through checkbox-54 pass. Use a single syntax-valid Python test file that validates the committed ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json fixture in place; do not introduce ppd/contracts/planned_crawl_manifest.py, live crawling, authenticated automation, or broad shared-contract rewrites.`
- Latest result: `supervisor_repair_replanned`
- Latest summary: Blocked the validator retry because it did not match the committed fixture shape, then added narrow daemon-repair tasks for fixture-shape diagnostics before resuming checkbox-48.
- Counts: `{"blocked": 3, "complete": 54, "in_progress": 0, "needed": 4}`


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-02T06:14:32.561678Z

- Latest target: `Task checkbox-61: Task checkbox-56: Add a narrow daemon fixture-shape diagnostic helper under `ppd/daemon/` for JSON fixtures. It must accept a repository-relative fixture path, report top-level keys, obvious list fields, and first object keys only, and include self-test coverage using an in-memory or temporary synthetic JSON object. Do not validate PP&D domain semantics in this helper.`
- Latest result: `accepted`
- Latest summary: Add fixture-shape diagnostic helper for JSON fixtures
- Counts: `{"blocked": 3, "complete": 58, "in_progress": 0, "needed": 3}`

<!-- ppd-daemon-task-board:end -->
