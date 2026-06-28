Implemented a narrow deterministic cue-table refinement for modal family classification, focused on the `compiler_registry` scope.

- Expanded deontic cues to better capture statutory obligation language (`duty/duties`, `powers and duties`, civil/criminal penalty phrasing, `is required to`) in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000272-20260519_162837/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:651).
- Expanded temporal cues with enactment/period phrasing (`date of enactment`, `on the date of enactment`, `during the period`) in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000272-20260519_162837/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:675).
- Expanded dynamic cues to include enforcement variants (`enforce`, `enforced`, `enforcement`) in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000272-20260519_162837/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:749).

Added/updated tests:

- Updated registry cue assertions and added a dynamic enforcement cue coverage test in [test_modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000272-20260519_162837/tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py:33).
- Added spaCy encoder cue extraction tests for `date of enactment` and `enforcement` in [test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000272-20260519_162837/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:2829).

Tests run:

1. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py`  
2. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py -k "temporal_date_of_enactment_cue or dynamic_enforcement_cue or deontic_obligation_phrase_cue"`  
3. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "powers_and_duties_as_deontic_scope_phrase or date_of_enactment_as_temporal_scope_signal or enforcement"`

All passed.