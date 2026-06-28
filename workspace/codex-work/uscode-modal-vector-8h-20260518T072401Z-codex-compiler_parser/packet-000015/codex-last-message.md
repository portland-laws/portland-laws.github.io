Implemented a fixture-focused compiler parser update by adding exact replay goldens for the three claimed samples and asserting deterministic parse behavior across both backends.

- Added three new dataset-text constants for:
  - `25 U.S.C. 478-1`
  - `42 U.S.C. 6930.`
  - `46 U.S.C. 60101.`
  at [test_modal_codec.py:66](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000015-20260518_083424/tests/unit_tests/logic/modal/test_modal_codec.py:66)

- Added a new golden replay test that validates for `regex` and `spacy`:
  - non-empty formula output
  - no `missing_modal_formula` ambiguity
  - citation provenance preserved
  - expected modal-family presence
  - expected transferred-heading fallback for `25 U.S.C. 478-1`
  at [test_modal_codec.py:462](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000015-20260518_083424/tests/unit_tests/logic/modal/test_modal_codec.py:462)

Validation run:

- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k 'replays_dataset_samples_for_478_1_6930_and_60101 or replays_dataset_zero_formula_cases_for_31a_2b_and_8906'`
- Result: `2 passed, 61 deselected`