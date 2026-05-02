# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles after repeated PP&D daemon failures. It is daemon programming guidance only: it must not implement the stalled PP&D domain task directly, does not download documents, does not create live crawl output, and does not create private DevHub artifacts.

## Current Failure Pattern

The recent failed rounds are parser preflight failures on PP&D domain work, especially proposed public frontier checkpoint files and public PDF extraction tests. Workers have repeatedly emitted TypeScript-style fragments inside Python expressions. Treat these exact patterns as banned strings in generated Python:

- `timeout_ms list[str]`
- `timeout_ms self.budget_ms`
- `page_number None`
- `page_number list[str]`
- `page_count list[str]`
- `if self.page_count list[str]`

Equivalent malformed expressions are also banned, including any conditional that places a type fragment where a comparison, membership check, boolean expression, or function call belongs.

## Parser-Failure Circuit Breaker

When the recent daemon history includes four validation rollbacks caused by `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, the supervisor must stop selecting the stalled PP&D domain task and emit a repair prompt before another worker attempt. The repair prompt must say that the next accepted proposal should be parser-clean before it is behavior-rich.

The daemon should classify this condition as syntax-preflight recovery, not as a normal domain validation failure. The next worker prompt must include these constraints:

- Change one file by default.
- Use two files only when the second file is a tiny focused JSON fixture or Python unittest for the same syntax guardrail.
- Do not create a new similarly named contract if an accepted committed contract already covers the same fixture shape.
- Run syntax-only preflight mentally for every changed Python or TypeScript file before returning JSON.
- Prefer adding or tightening daemon guidance, preflight, diagnostics, task selection, retry handling, or tests over editing PP&D crawler, DevHub, extraction, logic, or contract artifacts.

## Early Detection Scope Gate

Before full validation, the daemon or supervisor prompt should reject a syntax-recovery proposal that combines broad domain implementation with parser-bearing files. The early gate should fire when recent failures mention `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128` and the proposal touches frontier, crawler, PP&D contract, DevHub automation, extraction, or logic implementation paths.

Allowed retry shapes in syntax-recovery mode are:

- One syntax-valid Python file.
- One syntax-valid TypeScript file.
- One small JSON fixture plus one syntax-valid Python unittest file.
- One daemon prompt, diagnostic, preflight, retry, recovery, or task-selection file under `ppd/daemon/`.

Rejected retry shapes in syntax-recovery mode are:

- A contract file plus a test file plus a fixture in one proposal.
- A new near-duplicate domain contract while an accepted committed contract already covers the same fixture shape.
- Any proposal that mixes crawler code, crawl contracts, public fixtures, and tests before the parser-clean source file is accepted.
- Any proposal that resumes live crawl, authenticated DevHub automation, upload, submission, payment, certification, cancellation, or inspection scheduling work.

The supervisor prompt should name the failed syntax kind, name the failed file when known, and explicitly instruct the next worker to repair only that syntactic surface before adding richer assertions or domain behavior.

## Retry Scope

When three or more consecutive rounds fail with `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, shrink the next daemon attempt to one of these file sets:

- One syntax-valid Python unittest file.
- One small JSON fixture plus one syntax-valid Python unittest file.
- One daemon prompt, diagnostic, preflight, or task-selection file under `ppd/daemon/`.

Do not broaden the retry into contract rewrites, crawler changes, DevHub automation, or application/domain artifacts. If a fixture and a test are both needed, keep both files short and deterministic.

## Existing-Contract Reuse Rule

After repeated parser failures on a PP&D domain task, the next worker must first reuse existing committed contracts before proposing a new similarly named module. For the public frontier checkpoint loop, inspect and build on committed artifacts such as `ppd/contracts/frontier_checkpoint.py` and its accepted fixture/test coverage before creating any new `public_frontier_checkpoint` contract.

The daemon prompt should require the worker to state, in the proposal summary or impact, which existing committed contract, fixture, or validation helper is being reused. If no existing artifact can satisfy the task, the worker may add a new file only after keeping the proposal to one syntactically valid source file or one tiny fixture plus one syntactically valid unittest file. The worker must not add a parallel module with a near-duplicate name while an accepted contract already covers the same fixture shape.

## Python Guardrails

Every Python retry must satisfy these rules before normal validation:

- Every Python conditional uses complete comparisons such as `is None`, `is not None`, `==`, `!=`, `in`, or `isinstance(...)`.
- No Python file contains TypeScript-style expression fragments such as `value list[str]`, `value None`, or `field dict[str, str]` inside runtime code.
- Type annotations appear only in valid Python positions: function signatures, variable annotations, class attributes, or type aliases.
- Membership and presence checks use explicit Python expressions, for example `if value is None:` or `if not isinstance(value, list):`.
- Validation helpers return normally or raise `AssertionError`; they do not embed schema fragments in `if` statements.

## TypeScript Guardrails

Every TypeScript retry must satisfy these rules before normal validation:

- Object and array literals must be complete and balanced before the worker returns JSON.
- Function bodies, imports, exports, and type declarations must be syntactically complete.
- Do not mix Python syntax into TypeScript conditionals, object literals, or type declarations.
- Treat `TS1005`, `TS1109`, and `TS1128` as parser failures that require a smaller next proposal, not as normal contract-test failures.

## Required Preflight Order

For any retry that touches Python files, the daemon should run syntax-only checks before the full PP&D validation suite:

1. `python3 -m py_compile `
2. `python3 ppd/tests/validate_ppd.py`

For any retry that touches TypeScript files, the daemon should run strict TypeScript parsing before the full PP&D validation suite. If syntax preflight fails, reject the patch immediately and preserve the failure kind as `syntax_preflight`. Do not run broader validation after a syntax failure.

The syntax preflight should also reject broad parser-bearing retries before full validation. A retry that touches frontier, crawler, or PP&D contract paths after repeated parser failures may change only one Python or TypeScript source file. A tiny JSON fixture may accompany one focused Python unittest, but source-plus-contract-plus-test proposals must be split into separate daemon cycles.

## Separation From Domain Work

Supervisor repair is not a shortcut to complete checkbox-106, checkbox-108, or any other selected PP&D domain task. A repair patch may improve prompts, guides, retry logic, task selection, diagnostics, or validation sequencing. It must not implement the stalled PP&D domain task directly, must not add live public crawl artifacts, must not download documents, and must not create, modify, or reference private DevHub artifacts beyond naming the prohibited category.

## Recovery Behavior

After repeated syntax failures on the same task, the daemon should prefer the smallest valid step that can be accepted. If the active task needs both a fixture and assertions, split the work so the first accepted cycle creates or validates only the minimal syntactically valid scaffold. The next cycle can add richer assertions after the syntax loop has been broken.

If an accepted validation task already appears to cover the blocked task's fixture shape, the supervisor should recommend either superseding the blocked task in the task board or resuming it with one file only. The resumed worker should reference the accepted contract instead of creating another similarly named implementation.
