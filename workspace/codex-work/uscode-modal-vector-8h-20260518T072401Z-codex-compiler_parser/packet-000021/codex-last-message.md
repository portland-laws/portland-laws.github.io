Added deterministic regression fixtures for the three claimed TODO samples and wired them into existing parser/compiler golden replay tests.

- Added exact text fixtures for:
  - `us-code-2-60a-2-ee0af9802f887e89`
  - `us-code-16-6808-655096c0f6deada6`
  - `us-code-7-7656-ba2dced7f1b0e6ea`
  in [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000021-20260518_093123/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py#L119) and [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000021-20260518_093123/tests/unit_tests/logic/modal/test_modal_codec.py#L237).
- Extended zero-formula fallback replay coverage to include `2 U.S.C. 60a-2` in:
  - [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000021-20260518_093123/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py#L534)
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000021-20260518_093123/tests/unit_tests/logic/modal/test_modal_codec.py#L543)
- Extended symbolic-validity replay coverage to include `16 U.S.C. 6808` and `7 U.S.C. 7656` in:
  - [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000021-20260518_093123/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py#L636)
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000021-20260518_093123/tests/unit_tests/logic/modal/test_modal_codec.py#L823)

Tests run:

- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "31a_2b_60a_2_and_8906 or 16_6808 or 7_7656"` -> 2 passed
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "31a_2b_60a_2_and_8906 or 16_6808 or 7_7656"` -> 2 passed