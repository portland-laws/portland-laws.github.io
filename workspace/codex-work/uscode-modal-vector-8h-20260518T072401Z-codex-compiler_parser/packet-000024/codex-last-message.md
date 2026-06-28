Implemented deterministic replay fixtures for the three claimed samples and wired them into existing parser/compiler golden tests.

- Added `2 U.S.C. 130a` transferred-heading fixture and included it in the parser zero-formula replay case set: [test_legal_modal_parser.py:126](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000024-20260518_095913/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:126), [test_legal_modal_parser.py:571](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000024-20260518_095913/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:571).
- Added compiler-level replay coverage for `us-code-2-130a-a14e984db7a8af87` in the existing zero-formula regression test: [test_modal_codec.py:635](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000024-20260518_095913/tests/unit_tests/logic/modal/test_modal_codec.py:635).
- Added symbolic-validity fixtures for `4 U.S.C. 123` and `5 U.S.C. 5564` and extended symbolic replay assertions (both regex/spacy backends): [test_modal_codec.py:251](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000024-20260518_095913/tests/unit_tests/logic/modal/test_modal_codec.py:251), [test_modal_codec.py:274](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000024-20260518_095913/tests/unit_tests/logic/modal/test_modal_codec.py:274), [test_modal_codec.py:981](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000024-20260518_095913/tests/unit_tests/logic/modal/test_modal_codec.py:981).

Validation run:

```bash
pytest -q \
  tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py::test_parser_replays_dataset_zero_formula_cases_for_130a_31a_2b_60a_2_and_8906 \
  tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_compiler_replays_dataset_zero_formula_cases_for_130a_31a_2b_60a_2_and_8906 \
  tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_compiler_replays_symbolic_validity_samples_for_4_123_5_5564_16_6410_16_47a_16_6808_7_614_and_7_7656
```

Result: `3 passed`.