# PP&D Supervisor Repair Guide

This guide is for supervisor repair cycles when the isolated PP&D daemon is blocked by repeated invalid proposals or rollback loops.

## Current Repair Priority

When recent failures include `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, prioritize daemon apply-flow repair before retrying the domain task.

The next repair proposal should be narrow and deterministic:

- Replace only `ppd/daemon/ppd_daemon.py` when wiring apply-flow behavior.
- Import the existing `ppd.daemon.syntax_preflight.run_apply_flow_syntax_preflight` helper.
- Run changed-file syntax preflight immediately after proposed file replacements are written and before full validation.
- If syntax preflight fails, restore all changed files from backups immediately.
- Set `failure_kind` to `syntax_preflight`.
- Persist compact syntax diagnostics in failed work.
- Do not run the broad unittest or full TypeScript validation suite after a syntax-preflight failure.
- Keep the patch limited to daemon apply, rollback, and prompt diagnostics logic.

## Required Apply Flow

The daemon apply path should follow this order:

1. Validate proposal write paths.
2. Write complete file replacements and collect backups.
3. Build the patch text for diagnostics.
4. Run changed-file syntax preflight on `proposal.changed_files`.
5. On syntax failure, restore backups, persist failed work with `syntax_preflight`, and return.
6. Only after syntax preflight passes, run the normal validation command set.
7. On normal validation failure, restore backups and persist failed work with `validation`.
8. On success, persist accepted work and let the daemon mark the selected task complete.

## Prompt Recovery Rule

If syntax-preflight diagnostics are present in recent failure context, the daemon prompt should include this guidance:

Return one syntax-valid replacement file only, or one narrow syntax-valid test file plus one adjacent deterministic fixture when the fixture is required by the test. Do not rewrite broad shared contracts. Do not add live crawling or authenticated automation. Ensure changed Python files pass `py_compile` before broader validation.

## Resume Rule

After apply-flow syntax preflight is wired and `ppd/daemon/ppd_daemon.py --self-test` passes, resume the blocked public-crawl dry-run validator task fixture-first. The validator task should remain limited to deterministic fixture validation for the committed public crawl dry-run plan, failing closed on missing allowlist, robots, timeout, no-persist, or processor-adapter preflight fields.
