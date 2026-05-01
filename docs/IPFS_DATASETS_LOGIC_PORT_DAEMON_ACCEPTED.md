# Logic Port Daemon Accepted Work

This file is append-only daemon evidence for validated work that changed files used by the TypeScript port.

New accepted daemon rounds append the target task, impact statement, changed files, and validation commands here.
## 2026-04-28 13:59:04 UTC

- Target: `Task checkbox-56: Capture Python `DeonticConverter(use_ml=True)` confidence outputs for the same fixtures as development fixtures only.`
- Summary: Captured Python DeonticConverter(use_ml=True) confidence outputs for existing deontic parity fixtures.
- Impact: The shared Python parity fixture file now carries development-only DeonticConverter confidence captures, and existing Jest validation loads those captures from both the parity suite and the deontic converter suite so the TypeScript port can track Python confidence behavior without adding browser-to-Python runtime calls.
- Changed files: `src/lib/logic/deontic/converter.test.ts`, `src/lib/logic/parity/parity.test.ts`, `src/lib/logic/parity/python-parity-fixtures.json`
- Validation: `git apply -` -> `0`, `npx tsc --noEmit` -> `0`, `npm run validate:logic-port` -> `0`

## 2026-04-28 15:40:31 UTC

- Target: `Task checkbox-57: Add parity fixtures with raw text, regex-only output, spaCy-enabled output, ML confidence, and expected tolerances.`
- Summary: Add a focused Python parity capture fixture for raw text, regex output, spaCy-style extraction, ML confidence, and numeric tolerances.
- Impact: The parity fixture is loaded by src/lib/logic/parity/parity.test.ts and validated against the browser-native FOL parser, deterministic spaCy-style extraction fallback, FOLConverter ML/NLP path, and ML confidence feature/scoring helpers. This makes the fixture directly usable by the TypeScript logic-port validation suite.
- Changed files: `src/lib/logic/parity/parity.test.ts`, `src/lib/logic/parity/python-parity-fixtures.json`
- Evidence: `ipfs_datasets_py/.daemon/accepted-work/20260428T154031Z-add-a-focused-python-parity-capture-fixture-for-raw-text-regex-output-spacy-styl.json`, `ipfs_datasets_py/.daemon/accepted-work/20260428T154031Z-add-a-focused-python-parity-capture-fixture-for-raw-text-regex-output-spacy-styl.patch`, `ipfs_datasets_py/.daemon/accepted-work/20260428T154031Z-add-a-focused-python-parity-capture-fixture-for-raw-text-regex-output-spacy-styl.stat.txt`
- Validation: `npx tsc --noEmit` -> `0`, `npm run validate:logic-port` -> `0`

## 2026-04-29 05:55:47 UTC

- Target: `Task checkbox-112: Add Python parity fixtures for each TDFOL rule category.`
- Summary: Replace the malformed diff with complete parity test and fixture file contents for TDFOL rule categories.
- Impact: The TypeScript validation suite imports src/lib/logic/parity/python-parity-fixtures.json from src/lib/logic/parity/parity.test.ts, then parses and applies browser-native TDFOL rules against Python-captured fixture conclusions for each rule category.
- Changed files: `src/lib/logic/parity/parity.test.ts`, `src/lib/logic/parity/python-parity-fixtures.json`
- Evidence: `ipfs_datasets_py/.daemon/accepted-work/20260429T055547Z-replace-the-malformed-diff-with-complete-parity-test-and-fixture-file-contents-f.json`, `ipfs_datasets_py/.daemon/accepted-work/20260429T055547Z-replace-the-malformed-diff-with-complete-parity-test-and-fixture-file-contents-f.patch`, `ipfs_datasets_py/.daemon/accepted-work/20260429T055547Z-replace-the-malformed-diff-with-complete-parity-test-and-fixture-file-contents-f.stat.txt`
- Validation: `npx tsc --noEmit` -> `0`, `npm run validate:logic-port` -> `0`

