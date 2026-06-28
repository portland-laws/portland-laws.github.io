Implemented a narrow deterministic cue-rule refinement in the compiler registry lane.

**Changes**
- Expanded conditional-scope phrase cues to capture relative-clause legal conditions (`any person who`, `whoever`, etc.) in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000271-20260519_162140/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:33).
- Expanded statutory-reference phrases (`under this subchapter/part/subpart/subtitle/division`) in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000271-20260519_162140/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:62).
- Added temporal phrase variants (`at such times`, `at such times as`) in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000271-20260519_162140/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:169).
- Added deontic policy phrases (`it is the policy of`, `it shall be the policy of`) in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000271-20260519_162140/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:604).

**Tests added**
- New lexical-signal tests in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000271-20260519_162140/tests/unit_tests/logic/modal/test_modal_codec.py:9610):
  - policy phrase -> deontic scope
  - `any person who` -> conditional scope
  - `under this subchapter` -> statutory scope reference

**Validation**
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "policy_of_phrase or any_person_who or under_this_subchapter or powers_and_duties or date_of_enactment or deontic_temporal_adaptive_ambiguity or signal_free_pair_policy_for_alethic_deontic_adaptive_ambiguity or signal_free_pair_policy_for_frame_conditional_adaptive_ambiguity or signal_free_pair_policy_for_frame_temporal_adaptive_ambiguity"` passed.
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py` passed (`211 passed`).