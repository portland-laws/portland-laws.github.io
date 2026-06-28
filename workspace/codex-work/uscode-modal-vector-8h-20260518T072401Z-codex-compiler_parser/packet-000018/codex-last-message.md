Implemented a deterministic parser-rule improvement for long U.S.C. heading lines with subsection markers, plus regression coverage for your three cited samples.

**Code changes**
- Added a new fallback path that extracts a short heading prefix before a long `(a)`-style subsection body when no modal cues are found, then emits a frame formula instead of returning zero formulas.
  - [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000018-20260518_090021/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:54)
  - [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000018-20260518_090021/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:706)
  - [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000018-20260518_090021/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:848)

- Added regression fixtures/tests for sample IDs:
  - `us-code-42-15362.-c7a145faec5f2ad6`
  - `us-code-26-3201-bd4f34df4d869df4`
  - `us-code-42-3796ff-59f170d1c742e9af`
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000018-20260518_090021/tests/unit_tests/logic/modal/test_modal_codec.py:183)
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000018-20260518_090021/tests/unit_tests/logic/modal/test_modal_codec.py:588)

**Validation run**
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "long_subsection_heading_zero_formula_cases_for_15362_3201_and_3796ff"`  
  - Result: `1 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "heading_only_zero_formula_cases_for_25_422_48_1572_and_42_6323 or spacy_replays_sec_prefixed_heading_zero_formula_sample_for_15_1693l"`  
  - Result: `2 passed`