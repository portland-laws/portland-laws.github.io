Implemented deterministic parser fixtures for the three claimed symbolic-validity TODO samples (2 U.S.C. 5602, 5 U.S.C. 5348, 42 U.S.C. 15251.) across both parser backends by adding explicit replay test cases and sample texts.

Updated files:
- [tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000034-20260518_112516/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py):257
- [tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000034-20260518_112516/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py):1102
- [tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000034-20260518_112516/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py):92
- [tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000034-20260518_112516/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py):564

Validation run:
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "symbolic_validity_todo_samples_for_2_5602_5_5348_and_42_15251"` passed
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py -k "symbolic_validity_todo_samples_for_2_5602_5_5348_and_42_15251"` passed