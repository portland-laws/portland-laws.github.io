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
- [ ] Add formal guardrail compiler skeleton for deterministic predicates, deontic rules, temporal rules, and support maps.
- [ ] Add missing-information detector fixtures for user document-store comparison.
- [ ] Add PP&D validation command that checks fixtures, schemas, daemon self-test, and private-data ignore coverage.
- [ ] Add a bounded public crawl dry-run that fetches only a tiny seed set after robots/crawl-policy checks.
- [ ] Add source diff report artifacts for changed PP&D guidance pages.
- [ ] Add append-only accepted-work ledger generation for successful PP&D daemon rounds.
- [ ] Add operations documentation for starting, stopping, and inspecting the PP&D daemon.

<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-01T15:09:23.227722Z

- Latest target: `Task checkbox-11: Add requirement extraction fixtures for obligations, preconditions, deadlines, exceptions, and source evidence.`
- Latest result: `accepted`
- Latest summary: Added deterministic PP&D requirement extraction fixtures covering obligations, preconditions, deadlines, exceptions, and source evidence.
- Counts: `{"blocked": 0, "complete": 11, "in_progress": 0, "needed": 7}`

<!-- ppd-daemon-task-board:end -->
