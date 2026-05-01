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
- [x] Add fixture-only PDF normalized-document conversion metadata for page text, form fields, checkboxes, signatures, and fee-table hints without downloading live PDFs.
- [x] Add deterministic source-diff comparator tests that classify added, removed, and changed public guidance requirements from fixtures.
- [x] Add a first permit-process fixture for the Single PDF Process with stages, required documents, file rules, and citation-backed evidence.
- [x] Add requirement extraction validation for Single PDF Process obligations, preconditions, deadlines, exceptions, confidence, and formalization status.
- [x] Add guardrail compiler fixture tests for document completeness, PDF file rules, missing user facts, and explicit-confirmation gates.
- [x] Add mocked DevHub workflow snapshot fixtures with redacted field values, semantic selectors, validation messages, upload controls, and navigation edges.
- [x] Add DevHub fixture privacy validation that rejects credentials, auth state, traces, screenshots with private values, and unredacted PII.
- [x] Add a fixture-backed public crawl dry-run report command that uses injected responses by default and writes no raw crawl output.
- [x] Add a live-public-crawl preflight task that only reports eligible tiny seed URLs after allowlist, robots, timeout, and no-persist checks.
- [x] Add daemon-side proposal validation that runs `py_compile` on every proposed Python replacement before broader test discovery, with a fixture proving syntax errors are rejected without retrying the same task blindly.
- [x] Add a narrow supervisor diagnostic fixture that classifies repeated Python `SyntaxError` failures as a syntactic-validity repair hint and recommends smaller file sets.
- [x] Add a fixture-only crawl session manifest schema that records planned public fetch URLs, policy decisions, and no raw response bodies.
- [x] Add validation for crawl session manifests that rejects private DevHub session paths, raw crawl output paths, response bodies, credentials, traces, screenshots, and downloaded documents.
- [x] Add fixture-only public document provenance validation that ties normalized HTML and PDF records back to canonical URL, retrieval timestamp, checksum, and source-index entry.
- [x] Add a second permit-process fixture for a PP&D trade permit with plan review, including required facts, required documents, file rules, stages, and citation-backed action gates.
- [x] Add requirement extraction validation for the trade-permit-with-plan-review fixture, covering eligibility preconditions, upload requirements, fee/payment checkpoints, correction paths, and explicit-confirmation gates.
- [x] Add guardrail compiler fixture tests for trade-permit-with-plan-review missing facts, required documents, payment stop points, and correction-upload confirmation gates.
- [~] Add mocked DevHub recorder transition fixtures for save-for-later, back/continue navigation, upload validation messages, and draft-resume states using only redacted fixture data.
- [ ] Add DevHub action-classifier tests for inspection scheduling, correction upload, cancellation, certification, and payment actions, ensuring consequential and financial actions require exact explicit user confirmation.
- [ ] Add a PP&D archive adapter contract that treats `ipfs_datasets_py/ipfs_datasets_py/processors` as the website archival backend and records processor name, version, content hash, source URL, and PP&D policy decision.
- [ ] Add fixture tests for the PP&D archive adapter proving it refuses non-allowlisted URLs, private DevHub paths, raw response-body persistence, credentials, traces, screenshots, and downloaded private documents before invoking processor archival code.
- [ ] Add a crawl-to-processor handoff manifest fixture that maps public PP&D seed URLs to `ipfs_datasets_py` web archive / legal scraper processor jobs without forking processor implementation into `ppd/`.
- [ ] Add Playwright fixture contracts for DevHub form states that include accessible-name selectors, label text, role, nearby heading, URL state, field requirement status, and redacted values.
- [ ] Add a Playwright form-drafting scaffold that can fill reversible draft fields only in mocked DevHub fixtures and produces an action preview instead of touching live DevHub.
- [ ] Add Playwright guardrail tests proving upload, submit, certify, pay, cancel, schedule inspection, MFA, CAPTCHA, account creation, and password recovery actions are refused unless exact user confirmation is present.
- [ ] Add a Playwright audit-event fixture that records selector basis, source requirement, user-confirmation state, action classification, and before/after redacted field state for draft-only form edits.


<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: 2026-05-01T18:47:38.507067Z

- Latest target: `Task checkbox-38: Add guardrail compiler fixture tests for trade-permit-with-plan-review missing facts, required documents, payment stop points, and correction-upload confirmation gates.`
- Latest result: `accepted`
- Latest summary: Add deterministic trade-permit-with-plan-review guardrail fixture tests for missing facts, required documents, payment stop points, and correction-upload confirmation gates.
- Counts: `{"blocked": 0, "complete": 38, "in_progress": 0, "needed": 9}`

<!-- ppd-daemon-task-board:end -->
