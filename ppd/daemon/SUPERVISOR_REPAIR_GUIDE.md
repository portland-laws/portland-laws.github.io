# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles after repeated daemon rollbacks. It must not implement the stalled PP&D domain task directly. Its job is to restore useful autonomous progress by narrowing the next daemon prompt, preflight, retry, selection, or diagnostics work.

## Recent Parser Failure Patterns

Treat these exact malformed fragments as parser-failure examples that require a smaller retry before any broader feature work:

- `page_number None`
- `page_number list[str]`
- `page_count list[str]`
- `if self.page_count list[str]`

These are not business-rule failures. They are syntax and code-generation failures. A retry should repair daemon supervision or add a very small validation guardrail before the worker attempts another DevHub, crawler, extraction, logic, or fixture bundle.

## Allowed Recovery Shapes

Use one of these shapes after SyntaxError, py_compile, TS1005, TS1109, or TS1128 failures:

- One syntax-valid Python unittest file
- One syntax-valid daemon helper file
- One small JSON fixture plus one syntax-valid Python unittest file
- One daemon operations document that tightens retry instructions

Avoid source-plus-fixture-plus-test bundles until the parser-bearing file has passed syntax preflight. Every Python conditional uses complete comparisons such as `is None`, `is not None`, `==`, `!=`, `in`, or `isinstance(...)`. No Python file contains TypeScript-style expression fragments.

## Separation From Domain Work

A supervisor repair cycle must not implement the stalled PP&D domain task directly. It may describe how to unblock later work, but it does not download documents, does not create private DevHub artifacts, does not open authenticated DevHub sessions, and does not automate upload, payment, submission, certification, cancellation, inspection scheduling, CAPTCHA, MFA, account creation, or password recovery.

## Prompt Guidance

When the board has only blocked work, append or select a narrow daemon-repair task first. The next prompt should ask for JSON only, complete file replacements only, and a small file set. If the recent failure is parser-related, require the worker to mentally run py_compile for changed Python files or strict TypeScript parsing for changed TypeScript files before returning JSON.
