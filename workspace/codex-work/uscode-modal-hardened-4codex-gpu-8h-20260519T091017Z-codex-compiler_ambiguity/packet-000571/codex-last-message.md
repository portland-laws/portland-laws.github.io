Implemented the `compiler_ambiguity` policy update for packet `000571` and added regression coverage.

**Changes**
- Added `conditional_normative -> temporal` to the compiler ambiguity bundle table in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000571-20260519_170248/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py).
- Updated registry expectations in [test_modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000571-20260519_170248/tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py) to reflect:
  - the new `conditional_normative -> temporal` bundle pair
  - existing `alethic -> epistemic` bundle membership/order
- Added packet-specific regression test `test_modal_compiler_surfaces_packet_000571_compiler_ambiguity_policy_pairs` in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000571-20260519_170248/tests/unit_tests/logic/modal/test_modal_codec.py), covering all four evidence pairs:
  - `frame -> conditional_normative`
  - `frame -> temporal`
  - `temporal -> temporal`
  - `conditional_normative -> temporal`

**Validation**
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py -k "compiler_ambiguity_policy_pair_helper_matches_declared_bundle or compiler_ambiguity_policy_targets_are_ordered_and_directional"` passed.
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "packet_000571_compiler_ambiguity_policy_pairs"` passed.