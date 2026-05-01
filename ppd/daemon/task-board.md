# PP&D Daemon Task Board

This is the controlling backlog for the PP&D autonomous daemon. The daemon should work one narrow item at a time and should only accept changes that pass PP&D validation.

Legend: `[ ]` needed, `[~]` in progress, `[x]` complete, `[!]` blocked or failing.

## Checklist

- [x] Create the isolated `ppd/` workspace marker and local ignore rules.
- [x] Add the PP&D daemon implementation with autonomous status, progress, accepted-work, and failed-patch evidence.
- [x] Add public PP&D seed manifest and crawler allowlist for Portland.gov, DevHub, PortlandOregon.gov, and Portland Maps references.
- [x] Add robots and crawl-policy preflight helpers for PP&D public source discovery.
- [x] Add HTML extraction fixtures from public PP&D guidance pages.
- [x] Add PDF extraction fixture definitions for public PP&D applications and checklists.
- [x] Add normalized document TypeScript/Python data contracts under `ppd/`.
- [x] Add process model data contracts for permit processes, workflow stages, required facts, required documents, and action gates.
- [x] Add DevHub workflow-state recorder interfaces with no live login or submission behavior.
- [x] Add guarded action classification for read-only, draft-edit, consequential, and financial DevHub actions.
- [x] Add requirement extraction fixtures for obligations, preconditions, deadlines, exceptions, and source evidence.
- [x] Add formal guardrail compiler skeleton for deterministic predicates, deontic rules, temporal rules, and support maps.
- [x] Add missing-information detector fixtures for user document-store comparison.
- [x] Add PP&D validation command that checks fixtures, schemas, daemon self-test, and private-data ignore coverage.
- [!] Add a bounded public crawl dry-run that fetches only a tiny seed set after robots/crawl-policy checks.
- [x] Add source diff report artifacts for changed PP&D guidance pages.
- [!] Add append-only accepted-work ledger generation for successful PP&D daemon rounds.
- [x] Add operations documentation for starting, stopping, and inspecting the PP&D daemon.


## Generated Status

Last updated: 2026-05-01T15:17:47.497853Z

- Latest target: `Task checkbox-14: Add PP&D validation command that checks fixtures, schemas, daemon self-test, and private-data ignore coverage.`
- Latest result: `accepted`
- Latest summary: Added deterministic PP&D validation command for fixture JSON, Python schema contracts, daemon self-test, and private-data ignore coverage.
- Counts: `{"blocked": 0, "complete": 14, "in_progress": 0, "needed": 4}`


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-01T16:36:17.643891Z

- Latest target: `Task checkbox-15: Add a bounded public crawl dry-run that fetches only a tiny seed set after robots/crawl-policy checks.`
- Latest result: `validation`
- Latest summary: Add deterministic bounded PP&D public crawl dry-run
- Counts: `{"blocked": 2, "complete": 16, "in_progress": 0, "needed": 0}`

<!-- ppd-daemon-task-board:end -->
