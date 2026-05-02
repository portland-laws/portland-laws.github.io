# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles after repeated PP&D daemon failures. It is daemon programming guidance only: it must not implement the stalled PP&D domain task directly, does not download documents, does not create live crawl output, and does not create private DevHub artifacts.

## Current Failure Pattern

The recent failed rounds are Python syntax preflight failures in `ppd/tests/test_public_pdf_extraction_fixtures.py`. The worker keeps emitting TypeScript-style fragments inside Python expressions. Treat these exact patterns as banned strings in generated Python:

- `page_number None`
- `page_number list[str]`
- `page_count list[str]`
- `if self.page_count list[str]`

Equivalent malformed expressions are also banned, including any conditional that places a type fragment where a comparison or function call belongs.

## Retry Scope

When three or more consecutive rounds fail with `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, shrink the next daemon attempt to one of these file sets:

- One syntax-valid Python unittest file
- One small JSON fixture plus one syntax-valid Python unittest file

Do not broaden the retry into contract rewrites, crawler changes, DevHub automation, or application/domain artifacts. If a fixture and a test are both needed, keep both files short and deterministic.

## Python Guardrails

Every Python retry must satisfy these rules before normal validation:

- Every Python conditional uses complete comparisons such as `is None`, `is not None`, `==`, `!=`, `in`, or `isinstance(...)`.
- No Python file contains TypeScript-style expression fragments such as `value list[str]`, `value None`, or `field dict[str, str]` inside runtime code.
- Type annotations appear only in valid Python positions: function signatures, variable annotations, class attributes, or type aliases.
- Membership and presence checks use explicit Python expressions, for example `if value is None:` or `if not isinstance(value, list):`.
- Validation helpers return normally or raise `AssertionError`; they do not embed schema fragments in `if` statements.

## Required Preflight Order

For any retry that touches Python files, the daemon should run syntax-only checks before the full PP&D validation suite:

1. `python3 -m py_compile `
2. `python3 ppd/tests/validate_ppd.py`

If syntax preflight fails, reject the patch immediately and preserve the failure kind as `syntax_preflight`. Do not run broader validation after a syntax failure.

## Separation From Domain Work

Supervisor repair is not a shortcut to complete checkbox-106 or any other selected PP&D domain task. A repair patch may improve prompts, guides, retry logic, task selection, diagnostics, or validation sequencing. It must not implement the stalled PP&D domain task directly, must not add live public crawl artifacts, must not download documents, and must not create, modify, or reference private DevHub artifacts beyond naming the prohibited category.

## Recovery Behavior

After repeated syntax failures on the same task, the daemon should prefer the smallest valid step that can be accepted. If the active task needs both a fixture and assertions, split the work so the first accepted cycle creates or validates only the minimal syntactically valid scaffold. The next cycle can add richer assertions after the syntax loop has been broken.
