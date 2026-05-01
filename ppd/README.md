# PP&D Workspace

This directory is the isolated workspace for Portland Permitting & Development scraping, DevHub automation, process extraction, and formal guardrail work.

The project can reuse patterns from the existing TypeScript-port daemon, but PP&D work should keep its own source, data, daemon state, fixtures, accepted-work logs, and validation commands under `ppd/`.

## Boundary

PP&D implementation code should live here rather than in the existing Portland legal corpus or TypeScript logic-port directories.

Allowed write targets for PP&D work:

- `ppd/`
- `docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md`
- root-level package or CI wiring only when needed to call `ppd/` commands

Avoid writing PP&D daemon output to:

- `src/lib/logic/`
- `public/corpus/portland-or/current/`
- `ipfs_datasets_py/.daemon/`
- `docs/IPFS_DATASETS_LOGIC_TYPESCRIPT_PORT_PLAN.md`
- `docs/IPFS_DATASETS_LOGIC_PORT_DAEMON_ACCEPTED.md`

## Planned Layout

```text
ppd/
  daemon/       PP&D task board, status/progress files, accepted work, failed patches
  crawler/      public PP&D crawler and extractors
  devhub/       authenticated DevHub session recorder and guarded action executor
  extraction/   process, requirement, and source-diff extraction
  logic/        predicate/deontic/temporal guardrail compiler
  data/         public manifests plus ignored private user/session artifacts
  tests/        PP&D-specific fixtures and validation
```

## Reuse From Prior Daemons

Reuse the mechanics, not the state:

- markdown task board.
- one narrow task per cycle.
- validation before accepted changes.
- append-only accepted-work evidence.
- failed patch capture.
- heartbeat/status/progress files.
- blocked-task handling.
- rollback on validation failure.

The PP&D daemon should use its own allowlist and should initially accept changes only under `ppd/`.

## Version Control

`ppd/.gitignore` excludes private DevHub session artifacts, live crawl output, traces, daemon runtime state, and failed patches. Commit only curated, redacted fixtures and source code.

## Validation

Run the deterministic PP&D workspace validation command from the repository root:

```bash
python3 ppd/tests/validate_ppd.py
```

The validation command checks curated JSON fixtures and manifests, Python schema contracts, the PP&D daemon self-test, and private-data ignore coverage. It does not crawl public sites, open DevHub, authenticate, submit, upload, pay, or read private session artifacts.

## Daemon Control

Use the local control wrapper from the repository root:

```bash
bash ppd/daemon/control.sh start
bash ppd/daemon/control.sh status
bash ppd/daemon/control.sh logs
bash ppd/daemon/control.sh stop
```

The daemon validates PP&D work with its self-test, PP&D unit tests, Python compilation, and scoped TypeScript checks before accepting changes.
