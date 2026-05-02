# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles after the PP&D daemon records repeated failed rounds without an accepted patch.

## Immediate Recovery Rule

When recent failures include no proposed files, invalid JSON generation, Python `SyntaxError`, `py_compile` failures, or TypeScript parser errors such as `TS1005`, `TS1109`, or `TS1128`, the next daemon task must be smaller than the failed task.

Prefer one of these recovery shapes:

- One syntax-valid Python test file under `ppd/tests/`.
- One small daemon guidance or diagnostic file under `ppd/daemon/`.
- One minimal fixture correction plus one matching fixture-only test.
- One task-board update that appends narrow unchecked tasks without changing completed tasks.

Do not retry broad daemon rewrites, shared contract rewrites, live crawler code, or authenticated automation until a narrow fixture-first or validation-first task has passed.

## Fixture-First Retry Checklist

Before writing a validator for an existing JSON fixture, the worker must inspect the committed fixture shape first. The validator should match the actual fixture structure instead of assuming field names from a desired future contract.

For missing-field validation failures, the worker should:

1. Identify the exact fixture path from the failed test output or task text.
2. Inspect top-level keys, list fields, and first object keys.
3. Write assertions against the committed structure.
4. Keep PP&D domain semantics out of generic fixture-shape diagnostics.
5. Avoid adding live network access, DevHub login, browser state, raw crawl output, or downloaded documents.

## Syntax Guardrail

When editing Python files, keep generated replacements small enough to review visually. Avoid large raw multiline prompt rewrites inside Python string literals unless they are already covered by syntax preflight.

When editing TypeScript files, avoid broad object-literal or template-string rewrites after `TS1005`, `TS1109`, or `TS1128` failures. Prefer a small test, fixture, or helper that does not require changing parser-sensitive daemon flow.

A successful recovery task should pass:

- `python3 ppd/daemon/ppd_daemon.py --self-test`
- `python3 -m unittest discover -s ppd/tests -p test_*.py`
- the PP&D TypeScript typecheck when TypeScript files exist

## Current Safe Next-Step Pattern

For source-provenance continuity work, keep the next patch fixture-only and validation-only. Link existing public crawl dry-run records, source index records, normalized document fixtures, and requirement fixtures by canonical URL or source evidence ID. Do not fetch live pages, invoke processors, log in to DevHub, or create private session artifacts.

If the fixture relationship is unclear, add a diagnostic or test that reports the missing linkage narrowly rather than inventing a broad manifest contract.
