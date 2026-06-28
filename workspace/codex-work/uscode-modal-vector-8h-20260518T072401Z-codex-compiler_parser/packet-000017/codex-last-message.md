Implemented a deterministic parser-rule widening for U.S.C. heading-only rows and added fixtures for the three TODO sample IDs.

- Updated heading-without-section fallback heuristics in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000017-20260518_085136/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:54):
  - increased heading-only token cap from `12` to `24`
  - allowed `, : ;` in heading-only rows
  - removed leading-stopword rejection
  - kept guards for verb-like text, editorial/codification/declarative hints, bracket punctuation, and multi-sentence fragments

- Added deterministic fixture coverage keyed to:
  - `us-code-15-1193-9a13ca81d6192eb7`
  - `us-code-22-1031-6f5844d1be055539`
  - `us-code-15-4712-dc1d9f66b7b15af0`
  in:
  - [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000017-20260518_085136/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:522)
  - [test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000017-20260518_085136/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:335)
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000017-20260518_085136/tests/unit_tests/logic/modal/test_modal_codec.py:578)

Tests run (all passed):

1. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py::test_parser_replays_heading_only_zero_formula_cases_for_15_1193_22_1031_and_15_4712 tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py::test_spacy_compiler_replays_heading_only_zero_formula_cases_for_15_1193_22_1031_and_15_4712 tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_compiler_replays_heading_only_zero_formula_cases_for_15_1193_22_1031_and_15_4712`
2. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py::test_parser_replays_heading_only_zero_formula_cases_for_25_422_48_1572_and_42_6323 tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py::test_spacy_compiler_replays_heading_only_zero_formula_cases_for_25_422_48_1572_and_42_6323 tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_compiler_replays_heading_only_zero_formula_cases_for_25_422_48_1572_and_42_6323`