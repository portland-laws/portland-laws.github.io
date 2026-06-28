Implemented. I added a deterministic parser hardening plus a golden regression case for `us-code-2-59b-8902f0eb9b420bbe`.

Changed files:
- [`legal_modal_parser.py:1025`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000144-20260518_124510/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:1025)  
  Added a transferred-heading rule branch that accepts compact `§... transferred` headings even when citation tokenization is noisy.
- [`test_legal_modal_parser.py:183`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000144-20260518_124510/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:183)  
  Added `_USCODE_2_59B_PACKET_144_TEXT` golden text.
- [`test_legal_modal_parser.py:846`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000144-20260518_124510/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:846)  
  Extended the dataset zero-formula replay test to include `2 U.S.C. 59b` / sample id `us-code-2-59b-8902f0eb9b420bbe`.
- [`test_modal_codec.py:332`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000144-20260518_124510/tests/unit_tests/logic/modal/test_modal_codec.py:332)  
  Added the same golden text constant.
- [`test_modal_codec.py:725`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000144-20260518_124510/tests/unit_tests/logic/modal/test_modal_codec.py:725)  
  Extended regex compiler replay set with `2 U.S.C. 59b`.
- [`test_modal_codec.py:779`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000144-20260518_124510/tests/unit_tests/logic/modal/test_modal_codec.py:779)  
  Added a dedicated modal compiler regression test for `2 U.S.C. 59b` across both `regex` and `spacy` backends.

Validation run:
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "59b or dataset_zero_formula_cases_for_59b"` → `1 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "59b and (dataset_zero_formula_cases_for_59b or packet_todo_zero_formula_sample_for_2_59b)"` → `2 passed`