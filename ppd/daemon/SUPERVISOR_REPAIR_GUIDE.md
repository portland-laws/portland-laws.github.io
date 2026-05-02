# PP&D Supervisor Repair Guide

This guide is intentionally short because the daemon includes PP&D markdown files in worker prompt context. Use it when the supervisor reports repeated failed daemon rounds.

## Syntax-Preflight Recovery

When recent daemon failures include `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, the next worker proposal must be smaller than the failed proposal.

Required recovery behavior:

- Replace only the files needed for the selected task.
- Prefer one implementation file plus one focused test file, or one documentation repair file when the failure is supervisory.
- Do not rewrite shared contracts or broad validation suites while recovering from syntax failures.
- For Python, use ordinary annotations only in assignments, parameters, returns, dataclasses, and type aliases.
- Never write pseudo type-guard statements such as `if value list[str]:`, `if value tuple[str, ...]:`, or `if object.field dict[str, str]:`.
- Use `isinstance(value, list)`, `isinstance(value, tuple)`, or explicit helper functions for runtime validation.
- Keep every generated Python expression valid under `python3 -m py_compile` before returning JSON.

## Replenishment Task Guidance

For completed-board replenishment validation, avoid live daemon execution and avoid authenticated automation. A valid narrow implementation should prove the transition with deterministic data:

- a completed board snapshot,
- accepted-work history identifiers that are preserved,
- a new appended tranche with `[ ]` tasks,
- stale supervisor repair counters reset or excluded from the new tranche,
- validation that completed tasks remain completed and are not reselected.

Use fixtures or small pure-Python helpers. Do not write private DevHub state, raw crawl output, browser traces, screenshots, auth state, uploads, submissions, payments, certifications, cancellations, MFA, CAPTCHA, or inspection scheduling artifacts.

## Supervisor Diagnosis Checklist

Before broad validation, the daemon must be able to explain failures compactly enough for the next worker cycle:

- failure kind,
- changed files,
- failing command,
- parser or assertion diagnostic,
- whether edits were rolled back,
- whether the next proposal should shrink scope.

If a selected task has multiple syntax-preflight failures, the worker should repair syntax and tests first, not extend the domain implementation surface.
