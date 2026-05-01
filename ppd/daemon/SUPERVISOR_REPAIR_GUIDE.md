# PP&D Supervisor Repair Guide

This guide is operational context for supervisor-initiated repairs when the isolated PP&D daemon is blocked. It is source guidance only; it must not contain private DevHub state, raw crawl output, downloaded documents, credentials, payment data, or user-specific permit data.

## General Repair Rules

When a task is blocked by repeated validation failures, prefer a narrow daemon, test, or operations-doc repair that lets the next worker round make meaningful progress. Do not mark a task complete unless validation has accepted the implementation.

Repairs should be deterministic and fixture-only. They must not depend on live public crawl output, DevHub authentication, browser traces, official uploads, submissions, payments, certifications, cancellations, or inspection scheduling.

All generated file proposals must be complete file replacements. Avoid partial snippets, shell commands, or patches embedded in prose.

## Syntax and Compile Failure Recovery

If recent daemon rounds fail validation with Python `SyntaxError`, `py_compile` failures, or TypeScript parser errors such as `TS1005`, `TS1109`, or `TS1128`, treat that as a daemon-programming problem before retrying the same PP&D domain task.

A useful supervisor repair should improve prompt guidance, preflight checks, retry classification, or diagnostics so the worker asks for smaller syntactically valid proposals. Prefer repairs in `ppd/daemon/` or focused daemon tests. Do not use this path to implement the selected PP&D domain artifact directly.

The next worker proposal after a syntax loop should usually add a narrow module plus a narrow test or fixture. It should avoid broad rewrites of stable shared contracts unless the selected task directly requires changing those contracts.

## Task checkbox-15 Recovery

Task checkbox-15 is blocked on bounded public crawl dry-run work. Recent failed attempts show two concrete risks:

- HTML title extraction returned `None` for a fixture page that expected `PPD Fixture`.
- A robots disallow fixture was treated as allowed, so the dry-run incorrectly returned `ok == True`.

A useful next repair should keep the implementation small and test-first. The dry-run should fetch only the configured tiny seed set after both allowlist and robots checks pass. Robots denial must fail closed before any seed fetch. Fixture HTML parsing should use a deterministic standard-library parser or a tightly scoped title extraction helper that handles ordinary `...` markup.

The dry-run must not persist raw response bodies. Reports may include URLs, status codes, content type, title, byte counts, hashes, and policy decisions, but not full page contents.

## Task checkbox-17 Recovery

Task checkbox-17 is blocked on append-only accepted-work ledger generation. Recent failed attempts introduced unterminated Python string literals inside `ppd/daemon/ppd_daemon.py`. A useful repair should avoid complex regex rewrites or multiline string surgery.

The narrow implementation target is `persist_accepted_work`. After the existing manifest, patch, and stat files are written successfully, append one JSON object to a PP&D-local ledger such as `ppd/daemon/accepted-work/accepted-work.jsonl`.

The ledger entry should include:

- `created_at`
- `target_task`
- `summary`
- `impact`
- `changed_files`
- relative artifact paths for the manifest, patch, and stat files
- validation commands from the successful round

The ledger must be append-only and PP&D-scoped. It must not reuse TypeScript logic daemon ledgers or write outside `ppd/daemon/accepted-work/`.

## Validation Expectations

A supervisor repair is meaningful only if these commands remain safe and pass:

```bash
python3 ppd/tests/validate_ppd.py
python3 ppd/daemon/ppd_daemon.py --self-test
python3 -m unittest discover -s ppd/tests -p 'test_*.py'
```

Validation must remain network-free and fixture-based. If a repair adds tests, the tests should exercise the failure mode directly rather than relying on daemon watch mode or an LLM call.
