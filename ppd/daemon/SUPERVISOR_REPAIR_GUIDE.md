# PP&D Supervisor Repair Guide

This guide is used when the PP&D supervisor detects repeated daemon validation rollbacks caused by syntax or compile failures.

## Syntax Failure Recovery

Trigger this mode when recent failed proposals include any of these signals:

- Python `SyntaxError`
- Python `py_compile` failure
- TypeScript `TS1005`
- TypeScript `TS1109`
- TypeScript `TS1128`

When this mode is active, the next daemon worker prompt must steer toward a smaller syntactically valid proposal instead of a broader contract rewrite.

## Worker Prompt Requirements

Add these guardrails to the next worker request:

- Return the smallest useful proposal for the selected task.
- Touch no more than three files unless the task cannot be validated otherwise.
- Prefer one implementation file, one fixture, and one focused test.
- Do not rewrite stable shared contracts while recovering from syntax failures unless the selected task is specifically a shared-contract repair.
- Keep Python and TypeScript syntax separate.
- Avoid complex regular expressions during recovery; prefer explicit string checks, parsed JSON, and small helper functions.
- Use ordinary control flow over dense one-line expressions.
- Before returning JSON, mentally check that every changed Python file can pass `python3 -m py_compile` and every changed TypeScript file can parse under `tsc --noEmit`.

## Preflight Policy

The supervisor should classify changed-file syntax failures before running the full validation suite.

Recommended preflight order:

1. Validate returned JSON shape and allowed write paths.
2. Apply file replacements to a rollback-capable workspace.
3. Run `python3 -m py_compile` on changed `.py` files only.
4. Run a parser/typecheck preflight on changed `.ts` and `.tsx` files only.
5. If any changed-file syntax preflight fails, roll back immediately and record failure kind `syntax_preflight`.
6. Run the full PP&D validation suite only after changed-file syntax preflight passes.

## Retry Policy

For a task with repeated syntax failures:

- First syntax failure: retry with syntax recovery guidance.
- Second syntax failure on the same task: require an even smaller file set and avoid editing shared contracts.
- Third syntax failure on the same task: block the task and append a narrow repair task to the task board.

Blocked syntax tasks should name the exact file and parser error that failed, then request a fixture-first repair rather than a feature expansion.

## Diagnostic Summary Format

When reporting a syntax rollback, include:

- target task label
- failure kind: `syntax_preflight` or `validation`
- changed files
- exact parser command
- first syntax error line
- whether rollback completed
- next recommended file limit

Do not include private DevHub session state, traces, raw crawl output, credentials, screenshots with private values, or downloaded documents in diagnostics.

## Current Recovery Recommendation

Recent PP&D daemon failures are syntax failures in newly proposed Python modules. The next worker should not broaden the selected public crawl dry-run task. It should produce a narrow replacement with at most these files:

- `ppd/crawler/public_crawl_report.py`
- one small committed fixture under `ppd/tests/fixtures/`
- one focused test under `ppd/tests/`

The worker should avoid shared contract edits and should use simple Python only: imports, plain functions, dataclasses only if necessary, explicit validation branches, and no complex regex syntax.
