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
- [x] Add a bounded public crawl dry-run that fetches only a tiny seed set after robots/crawl-policy checks.
- [x] Add source diff report artifacts for changed PP&D guidance pages.
- [x] Add append-only accepted-work ledger generation for successful PP&D daemon rounds.
- [x] Add operations documentation for starting, stopping, and inspecting the PP&D daemon.
- [x] Add source-index record fixtures and validation for canonical URL, redirects, content hash, timestamps, and crawl status.
- [x] Add fixture-only frontier expansion output with discovered links, content-type classifications, and skipped-URL reason codes.
- [x] Add fixture-only HTML-to-normalized-document conversion for headings, ordered steps, tables, links, and modified-date evidence.
- [~] Add fixture-only PDF normalized-document conversion metadata for page text, form fields, checkboxes, signatures, and fee-table hints without downloading live PDFs.
- [ ] Add deterministic source-diff comparator tests that classify added, removed, and changed public guidance requirements from fixtures.
- [ ] Add a first permit-process fixture for the Single PDF Process with stages, required documents, file rules, and citation-backed evidence.
- [ ] Add requirement extraction validation for Single PDF Process obligations, preconditions, deadlines, exceptions, confidence, and formalization status.
- [ ] Add guardrail compiler fixture tests for document completeness, PDF file rules, missing user facts, and explicit-confirmation gates.
- [ ] Add mocked DevHub workflow snapshot fixtures with redacted field values, semantic selectors, validation messages, upload controls, and navigation edges.
- [ ] Add DevHub fixture privacy validation that rejects credentials, auth state, traces, screenshots with private values, and unredacted PII.
- [ ] Add a fixture-backed public crawl dry-run report command that uses injected responses by default and writes no raw crawl output.
- [ ] Add a live-public-crawl preflight task that only reports eligible tiny seed URLs after allowlist, robots, timeout, and no-persist checks.



## Generated Status

Last updated: 2026-05-01T17:23:00Z

- Latest target: `Task checkbox-20: Add fixture-only frontier expansion output with discovered links, content-type classifications, and skipped-URL reason codes.`
- Latest result: `manual_acceptance`
- Latest summary: Added fixture-only frontier expansion contracts, fixtures, and validation.
- Counts: `{"blocked": 0, "complete": 20, "in_progress": 0, "needed": 10}`


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-01T17:34:38.148828Z

- Latest target: `Task checkbox-22: Add fixture-only PDF normalized-document conversion metadata for page text, form fields, checkboxes, signatures, and fee-table hints without downloading live PDFs.`
- Latest result: `validation`
- Latest summary: Added fixture-only PDF normalized-document conversion metadata contracts, fixture data, and deterministic validation for page text, form fields, checkboxes, signatures, and fee-table hints.
- Counts: `{"blocked": 0, "complete": 21, "in_progress": 0, "needed": 9}`

<!-- ppd-daemon-task-board:end -->
