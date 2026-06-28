Implemented a narrow deterministic parser improvement plus golden regressions for the claimed `15 U.S.C. 688` no-formula case.

**Changes**
- Broadened the U.S.C. codification fallback trigger to include transferred headings and added citation-section-aware heading detection in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000012-20260517_164232/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:32) and [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000012-20260517_164232/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:243).
- Added a golden parser replay test keyed to sample id `us-code-15-688-3977b0476c11fbf1` in [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000012-20260517_164232/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:105).
- Added a compiler-level regression ensuring this transferred-heading case no longer emits `missing_modal_formula` ambiguity in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000012-20260517_164232/tests/unit_tests/logic/modal/test_modal_codec.py:152).

**Validation**
- Attempted targeted pytest runs, but test startup fails in this repo due an existing bootstrap issue in root `__init__.py` (`NameError: __path__ is not defined`) before test bodies execute.
- Confirmed syntax with:
  - `python3 -m py_compile ...` on all changed files.
- Confirmed behavior with a direct runtime check:
  - parser now produces 1 formula for `§688. Transferred.` with fallback rule `uscode_transferred_heading_v1`.
  - compiler (`parser_backend="regex"`) produces 1 formula and no `missing_modal_formula` ambiguity for the same input.