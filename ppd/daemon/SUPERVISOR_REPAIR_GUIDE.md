# PP&D Supervisor Repair Guide

Use this guide when the PP&D daemon stalls after repeated rejected patches.

## Current Recovery Rule

When recent failures are validator assertion failures against a committed JSON fixture, the next daemon cycle must not guess the fixture schema. Add or use a daemon diagnostic that reports the committed fixture shape first, then constrain the retry to that observed shape.

## Narrow Retry Pattern

1. Keep the failed domain task blocked while repairing supervision.
2. Add a deterministic helper or prompt guardrail under `ppd/daemon/` that reports only structural JSON information: top-level keys, candidate list fields, and first object keys.
3. Add synthetic self-test coverage for the helper or prompt guardrail.
4. Resume the domain task with one syntax-valid test file, or one test file plus one minimal fixture path correction only when the fixture path is wrong.

## Do Not Do This During Repair

- Do not add `ppd/contracts/planned_crawl_manifest.py` for the public-crawl fixture retry.
- Do not rewrite broad shared contracts to satisfy one fixture validator.
- Do not perform live crawling or authenticated DevHub automation.
- Do not create private session, trace, screenshot, raw crawl, or downloaded document artifacts.
- Do not change application or domain artifacts just to mark progress.

## Acceptance Signal

A repair cycle is meaningful when the daemon can explain the fixture shape in compact diagnostics and the next selected task is narrow enough to complete in one cycle without inventing fields that are absent from the committed fixture.
