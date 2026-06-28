Implemented a narrow deterministic parser improvement plus packet-specific golden replay tests.

**What Changed**
- Extended U.S.C. section-reference parsing to recognize plural/prefixed forms (`§§`, `secs.`, `sections`) and reuse that consistently in citation extraction and heading/reference detection:
  - [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000025-20260518_100756/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:46)
  - [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000025-20260518_100756/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:458)
- Added deterministic replay fixtures/tests for the three TODO sample IDs (`7 U.S.C. 431`, `6 U.S.C. 257`, `45 U.S.C. §§ 81 to 92.`) in parser, spaCy compiler, and modal compiler suites:
  - [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000025-20260518_100756/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:491)
  - [test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000025-20260518_100756/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:172)
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000025-20260518_100756/tests/unit_tests/logic/modal/test_modal_codec.py:687)

**Validation**
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "packet_todo_samples_for_7_431_6_257_and_45_81_to_92 or editorial_status_zero_formula_sample_for_18_3008 or sec_prefixed_heading_zero_formula_sample_for_15_1693l"`  
  - `3 passed`
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py -k "packet_todo_samples_for_7_431_6_257_and_45_81_to_92 or editorial_status_zero_formula_cases or sec_prefixed_heading_zero_formula_sample_for_15_1693l"`  
  - `3 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "packet_todo_samples_for_7_431_6_257_and_45_81_to_92 or dataset_zero_formula_cases_for_130a_31a_2b_60a_2_and_8906"`  
  - `2 passed`