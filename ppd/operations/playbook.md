# PP&D Operations Playbook

This playbook covers safe operator procedures for PP&D public crawl dry-runs, attended DevHub sessions, validation, recrawl cadence, privacy checks, and daemon recovery gates. It is intentionally operational: use deterministic fixtures and validation first, and do not run live or authenticated automation until every applicable gate passes.

## Baseline Gates

Before any live public crawl dry-run or attended DevHub session:

1. Confirm the run target is PP&D-related and within the documented source scope.
2. Run deterministic fixture validation first.
3. Confirm no private credentials, browser auth state, traces, raw crawl output, downloaded documents, or private DevHub session files will be committed.
4. Confirm the operator can stop the run immediately if the site presents CAPTCHA, MFA, payment, account creation, certification, upload, submission, cancellation, or another irreversible action.
5. Confirm logs are written only to approved local runtime locations and are reviewed before promotion to committed fixtures.

## Safe Live Public Crawl Dry-Runs

Live public crawl dry-runs are for validating selectors, source availability, and crawl boundaries against public PP&D pages. They are not production recrawls.

Required controls:

- Use a dry-run mode when available.
- Limit scope to a small allowlisted seed set.
- Prefer HEAD or metadata checks where content download is not required.
- Use conservative rate limits and stop on repeated 4xx, 5xx, timeout, or redirect-loop responses.
- Do not bypass access controls, robots guidance, rate limits, CAPTCHA, or anti-abuse prompts.
- Do not persist full raw responses unless the output location is explicitly temporary and excluded from commits.
- Promote only minimized deterministic fixtures under `ppd/tests/fixtures/...` after privacy review.

Dry-run pass criteria:

- The crawler stays within the allowlisted PP&D public source scope.
- The run produces no private session material.
- The run produces no downloaded permit documents or user-specific records.
- The operator records source URLs, timestamps, status counts, and any boundary decisions in an operations note outside committed private artifacts.

## Attended DevHub Sessions

DevHub sessions must remain attended because authentication and user-specific records can be involved.

Allowed attended actions:

- Manual login by the authorized operator.
- Read-only navigation to confirm page structure and labels.
- Manual capture of non-sensitive selector observations.
- Immediate stop when a workflow requires submission, upload, certification, cancellation, payment, MFA enrollment, account creation, or CAPTCHA handling.

Disallowed automation:

- CAPTCHA solving or bypass.
- MFA automation.
- Account creation.
- Payment.
- Submission, upload, certification, cancellation, or other state-changing actions.
- Persisting browser auth state, private traces, raw authenticated pages, screenshots with personal data, or downloaded private documents in the repository.

DevHub pass criteria:

- The session was attended throughout.
- No state-changing action was automated.
- No private artifacts were committed.
- Any fixture derived from observations is synthetic, minimized, and stored under `ppd/tests/fixtures/...`.

## Validation Commands

Run validation before live dry-runs, after fixture changes, and before marking a PP&D operations task complete.

Minimum validation:

```bash
python3 ppd/daemon/ppd_daemon.py --self-test
```

Recommended when Python files under `ppd/` changed:

```bash
python3 -m py_compile $(find ppd -name '*.py' -print)
```

Recommended when PP&D tests are available:

```bash
python3 -m pytest ppd/tests
```

A live dry-run or attended DevHub observation is not a substitute for deterministic validation.

## Source Recrawl Cadence

Use this cadence unless a source-specific plan says otherwise:

- Public PP&D index and landing pages: monthly.
- Public forms, fee schedules, checklists, and instructions: monthly, plus within 7 days of a visible source update.
- Permit process guidance and policy pages: monthly.
- High-volatility public notices or service alerts: weekly while active.
- DevHub authenticated observations: only when an operator-approved task requires it, and always attended.

Recrawl promotion gates:

- Diff source metadata before replacing fixtures.
- Keep fixture updates narrow and deterministic.
- Record source URL and retrieval date in fixture metadata when the local fixture format supports it.
- Re-run validation before promotion.

## Privacy Checks

Before committing any PP&D fixture, log, note, or derived artifact, verify it does not contain:

- Names, email addresses, phone numbers, mailing addresses, signatures, or account identifiers from private sessions.
- Permit records or documents tied to a specific person unless the source is intentionally public and the fixture is minimized for test coverage.
- Browser auth state, cookies, tokens, local storage, session storage, HAR files, Playwright traces, screenshots, or downloaded private documents.
- Payment data, uploaded document contents, certification text submitted by a user, or MFA material.

Fixture privacy pass criteria:

- The fixture is synthetic or public-source-minimized.
- The fixture is stored under `ppd/tests/fixtures/...`.
- The fixture contains only the fields needed for deterministic validation.

## Supervisor And Daemon Recovery Gates

Use recovery gates when a PP&D supervisor, daemon, crawl worker, or validation process fails, restarts, or leaves partial output.

Recovery sequence:

1. Stop scheduling new live or authenticated work.
2. Preserve failure logs in the approved runtime location.
3. Identify whether the failed run touched public dry-run output, authenticated session material, daemon ledgers, or fixtures.
4. Delete or quarantine partial raw crawl output and private session material outside the repository.
5. Re-run deterministic validation.
6. Resume only after validation passes and the operator confirms no private artifacts are pending commit.

Resume gates:

- `python3 ppd/daemon/ppd_daemon.py --self-test` passes.
- No private DevHub session files, auth state, traces, raw crawl output, or downloaded documents are present in commit scope.
- Any fixture changes are deterministic and privacy-reviewed.
- Any failed live dry-run has an explicit boundary decision before retry.

Escalation gates:

- Repeated parse/runtime failures: reduce the proposal to the smallest syntax-valid file replacement.
- Unexpected authenticated prompt or state-changing flow: stop automation and require operator review.
- Possible private data exposure: stop promotion, quarantine the artifact outside the repository, and rerun privacy checks before continuing.
