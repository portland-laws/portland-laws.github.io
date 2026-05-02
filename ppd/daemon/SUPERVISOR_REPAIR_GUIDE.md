# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles after repeated daemon rounds fail without an accepted patch. It is intentionally narrow and applies to daemon prompt, preflight, retry, recovery, and diagnostics work only.

## Current Recovery Target

Recent failed patches repeatedly targeted the public PDF extraction fixture validator and were rolled back by Python syntax preflight. The recurring malformed fragments looked like Python conditionals polluted with TypeScript-style type fragments, including these exact failure shapes:

- `page_number None`
- `page_number list[str]`
- `page_count list[str]`
- `if self.page_count list[str]`

A supervisor repair patch must not implement the stalled PP&D domain task directly. It should improve the daemon instructions, diagnostics, or retry constraints so a later worker can resume the domain task with a smaller syntactically valid patch.

## Required Retry Shape

When the previous failure kind is `syntax_preflight`, the next domain retry must use one of these shapes:

- One syntax-valid Python unittest file
- One small JSON fixture plus one syntax-valid Python unittest file

The retry should not broaden schemas, rewrite multiple unrelated contracts, or create a new live automation path. If a fixture is needed, keep it small, redacted, and committed under `ppd/tests/fixtures/`.

## Python Syntax Guardrails

Every Python file proposed after a syntax-preflight rollback must satisfy these rules before full validation:

- Every Python conditional uses complete comparisons such as `value is None`, `value is not None`, `isinstance(value, list)`, or `len(value) > 0`.
- No Python file contains TypeScript-style expression fragments such as `field list[str]`, `field string`, `field?:`, or inline type fragments inside `if`, `return`, `assert`, list comprehensions, or boolean expressions.
- Python type hints may appear only in valid Python locations: function signatures, variable annotations, class attributes, or `typing` aliases.
- The daemon should run `python3 -m py_compile` for changed Python files before broader unittest or repository validation.

## Repair Scope Boundaries

Supervisor repair changes stay in daemon programming, diagnostics, preflight, retry policy, task selection, or recovery documentation. A repair patch must not implement the stalled PP&D domain task directly, does not download documents, does not crawl live public pages, and does not create private DevHub artifacts.

Forbidden repair outputs include:

- private DevHub artifacts
- auth state, cookies, sessions, traces, screenshots, or browser storage
- raw crawl output, raw PDF bytes, OCR dumps, or downloaded documents
- upload, submit, certify, pay, cancel, inspection scheduling, MFA, CAPTCHA, account creation, or password recovery automation

## Supervisor Action Rule

If the daemon has failed four or more consecutive rounds on the same parser or compiler error family, pause that domain task and accept only a narrow repair patch that improves prompt constraints or diagnostics. After the repair passes validation, resume the domain task with the smallest fixture-first retry shape listed above.
