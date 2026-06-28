Implemented the compiler ambiguity policy update for packet `000570` with deterministic coverage.

- Added `dynamic->dynamic` to the compiler ambiguity policy bundle in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000570-20260519_165320/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:186).
- Updated registry tests to include the new dynamic self-pair and align expected policy/target tables with the declared bundle in [test_modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000570-20260519_165320/tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py:162).
- Added a packet-specific compiler ambiguity test for the three evidence pairs (`dynamic->dynamic`, `frame->conditional_normative`, `frame->deontic`) with exact margin/priority assertions in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000570-20260519_165320/tests/unit_tests/logic/modal/test_modal_codec.py:14844).

Validation run:

- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py` -> `19 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "packet_000570_compiler_ambiguity_policy_pairs"` -> `1 passed`