# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles after repeated daemon validation rollbacks. It keeps recovery focused on daemon behavior, validation, task selection, retry policy, and diagnostics. It must not be used to implement the selected PP&D domain task directly.

## Syntax And Compile Rollback Recovery

When two recent failed daemon proposals for the same task include Python `SyntaxError`, `py_compile`, or TypeScript parser errors such as `TS1005`, `TS1109`, or `TS1128`, the next worker prompt must switch to syntax-recovery mode.

In syntax-recovery mode, instruct the worker to:

- edit the smallest possible file set, preferably one implementation file and one focused test file;
- avoid broad contract rewrites, shared schema rewrites, and multi-module refactors;
- avoid adding live crawl behavior, authenticated automation, private artifacts, raw crawl output, or downloaded documents;
- write plain Python in `.py` files and plain TypeScript in `.ts` files, with no mixed-language fragments;
- avoid complex regular expressions unless they are already present and known to compile;
- prefer simple conditionals and helper functions over dense inline expressions;
- include fixture-first or validation-first behavior before any live or authenticated behavior;
- return complete file replacements only.

The supervisor should treat repeated syntax failures as a prompt/programming problem, not as evidence that the PP&D domain task needs a larger implementation.

## Prompt Guardrail

For the next worker attempt after repeated syntax failures, add this instruction near the selected task:

```text
Recent validation rollbacks were syntax or compile failures. Return a smaller proposal than the failed attempts. Limit edits to the minimum files needed. Before returning JSON, mentally run Python `py_compile` on every `.py` file and TypeScript parsing on every `.ts` file. Do not use placeholders that are invalid syntax. Do not mix type annotation syntax with control-flow syntax. If unsure, choose simpler syntax.
```

If the active task is live-public-crawl preflight, the worker must only report eligible tiny seed URLs and must not fetch pages, persist crawl output, or create raw response fixtures.

## Retry Policy

After a syntax or compile rollback:

1. Keep the task selected only if the next proposal is explicitly smaller and syntax-first.
2. If a second syntax or compile rollback occurs on the same task, stop normal worker retries and run supervisor repair before another domain attempt.
3. Do not escalate to broader architecture changes unless validation failures are semantic and syntax-clean.
4. Keep the task board state unchanged except for normal daemon-generated status updates or explicit supervisor planning tasks.

## Diagnostics To Preserve

Failed-patch manifests should preserve:

- target task label;
- changed file paths;
- validation command;
- compact syntax error text;
- line number when available;
- whether the failure came from `py_compile`, unittest import, or TypeScript parsing.

Diagnostics should be compact and must not include private DevHub session files, auth state, traces, screenshots, raw crawl output, or downloaded documents.

## Supervisor Repair Scope

Valid supervisor repair edits include:

- daemon prompt text;
- preflight validation checks;
- retry and blocked-task policy;
- syntax-failure diagnostics;
- task-board repair planning;
- PP&D daemon operations documentation;
- focused tests for daemon supervision behavior.

Invalid repair edits include:

- implementing the selected PP&D domain task during repair;
- editing application or domain artifacts only to mark progress;
- creating private DevHub artifacts;
- automating CAPTCHA, MFA, account creation, payment, submission, certification, cancellation, official upload, or inspection scheduling.
