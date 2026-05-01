# PP&D Daemon Operations

This document describes how to start, stop, and inspect the isolated PP&D daemon from the repository root. The daemon is scoped to the `ppd/` workspace and should not write to the Portland legal corpus, TypeScript logic daemon ledgers, `ipfs_datasets_py/.daemon/`, private DevHub session storage, or live crawl output directories.

## Scope

The PP&D daemon operates on the PP&D task board at `ppd/daemon/task-board.md` and records PP&D-specific runtime evidence under `ppd/daemon/`.

Expected local runtime files include:

- `ppd/daemon/status.json`
- `ppd/daemon/progress.json`
- `ppd/daemon/ppd-daemon.pid`
- `ppd/daemon/ppd-daemon.log`
- append-only accepted-work records under `ppd/daemon/accepted-work/`

These runtime files are operational evidence, not source fixtures. They must not contain private DevHub credentials, authentication state, trace archives, downloaded documents, raw crawl output, payment data, or user-specific permit data.

## Start

Start the daemon from the repository root with the local control wrapper:

```bash
bash ppd/daemon/control.sh start
```

Starting the daemon should create or update the local PID, status, progress, and log files under `ppd/daemon/`. The daemon should work one task-board item at a time and validate changes before accepting them.

Before accepting any generated work, the daemon is expected to run deterministic PP&D validation only. The current validation path must remain fixture-based and must not crawl live public sites, open DevHub, authenticate, submit, upload, pay, cancel, certify, or schedule inspections.

## Stop

Stop the daemon from the repository root:

```bash
bash ppd/daemon/control.sh stop
```

Stopping should terminate the local daemon process identified by the PP&D daemon PID file. It should not delete accepted-work records or failed-patch records. If a task was in progress, inspect `ppd/daemon/status.json`, `ppd/daemon/progress.json`, and `ppd/daemon/ppd-daemon.log` before restarting.

## Status

Inspect the daemon status:

```bash
bash ppd/daemon/control.sh status
```

Use status output to confirm whether the daemon is running, which task it is targeting, and whether the latest result was accepted, blocked, failed validation, or still in progress.

The structured status file is `ppd/daemon/status.json`. It is intended for quick operational inspection and should stay scoped to daemon metadata such as current task, phase, timestamps, and result state.

## Supervisor

The supervisor watches the daemon heartbeat, task-board blockage, and repeated failure streaks. It can restart the daemon when the worker is down, and it can invoke Codex for a narrow, validated patch to `ppd/daemon/` or daemon tests when the worker is stuck or its own programming needs improvement.

Run one supervised repair cycle:

```bash
bash ppd/daemon/control.sh doctor
```

Run the supervisor continuously:

```bash
bash ppd/daemon/control.sh supervisor-start
```

Inspect or stop it:

```bash
bash ppd/daemon/control.sh supervisor-status
bash ppd/daemon/control.sh supervisor-stop
```

Supervisor state is written to `ppd/daemon/supervisor-status.json` and `ppd/daemon/supervisor-actions.jsonl`. These are runtime files and must not contain private DevHub data or raw crawl artifacts.

## Progress

Inspect detailed progress in `ppd/daemon/progress.json`. This file should summarize the active task, validation phase, recent heartbeat, and narrow operational state needed to understand a running or recently stopped daemon cycle.

Progress metadata should not include raw crawler responses, private account data, browser traces, uploaded file names from a real user case, credentials, MFA details, payment data, or permit application contents.

## Logs

Inspect recent daemon logs:

```bash
bash ppd/daemon/control.sh logs
```

Logs are for operational debugging. They should record task selection, validation commands, acceptance or failure classification, and bounded error messages. Logs must not contain private DevHub session data, credentials, raw crawl output, downloaded document contents, payment information, or user-specific permitting facts.

## Accepted Work

Accepted daemon rounds are recorded under `ppd/daemon/accepted-work/`. Accepted-work records should be append-only evidence for successful rounds and should include enough information to audit what changed and what validation passed.

Accepted-work records should not be reused from other daemon systems. The PP&D daemon must keep its accepted-work evidence separate from TypeScript logic daemon ledgers and other repository automation state.

## Failed Work

Failed patches are recorded under `ppd/daemon/failed-patches/` when validation fails or the daemon cannot safely apply a generated change. Failed records should classify the failure and preserve enough context to diagnose it without storing private or raw crawl artifacts.

A blocked task should be marked explicitly rather than repeatedly retried without new evidence.

## Validation

The deterministic workspace validation command is:

```bash
python3 ppd/tests/validate_ppd.py
```

The daemon self-test command is:

```bash
python3 ppd/daemon/ppd_daemon.py --self-test
```

These commands should remain safe to run without network access, DevHub authentication, private session files, live crawl output, payment actions, uploads, submissions, certifications, cancellations, or inspection scheduling.

## Restart Checklist

Before restarting after a stop, failure, or interrupted run:

1. Check `ppd/daemon/status.json` for the last task and result.
2. Check `ppd/daemon/progress.json` for the last phase and heartbeat.
3. Check `ppd/daemon/ppd-daemon.log` for validation or patch errors.
4. Confirm any failed patch under `ppd/daemon/failed-patches/` does not contain private data.
5. Run `python3 ppd/daemon/ppd_daemon.py --self-test` before starting unattended operation.

## Safety Rules

The daemon must not automate CAPTCHA, MFA, account creation, payment, submission, certification, cancellation, official upload, or inspection scheduling. Authenticated DevHub workflows require explicit user authorization and separate guarded action handling.

The daemon should prefer deterministic fixtures and validation before any live public crawl. Live crawl dry-runs must remain bounded, robots-aware, and limited to approved public seed sets.
