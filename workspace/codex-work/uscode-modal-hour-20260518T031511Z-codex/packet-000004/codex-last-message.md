Implemented the ambiguity-policy refinement for modal family mismatches by widening deterministic scope signals and wiring them into compiler ambiguity checks.

**What changed**
1. Added stronger deterministic ambiguity signals for conditional/deontic scope in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:32) and [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:574):
- Added `notwithstanding` as conditional scope phrase/token.
- Added deontic scope tokens/phrases (e.g., `obligation`, `duty`, `liable`, `under an obligation to`).
- Exposed new lexical flags: `has_conditional_scope_token`, `has_deontic_scope`, `has_deontic_scope_phrase`.

2. Updated deontic target-family ambiguity gating to use scope-level deontic evidence (not just cue hits) in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227/ipfs_datasets_py/logic/modal/compiler.py:691).

3. Added regression tests for the missing ambiguity patterns in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227/tests/unit_tests/logic/modal/test_modal_codec.py:311), [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227/tests/unit_tests/logic/modal/test_modal_codec.py:481), and [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227/tests/unit_tests/logic/modal/test_modal_codec.py:536).

**Validation run**
- Attempted:
`python3 -m pytest tests/unit_tests/logic/modal/test_modal_codec.py -k "notwithstanding or deontic_scope_phrase or deontic_scope_family_outvote_ambiguity or temporal_conditional_family_outvote_ambiguity" -q`
- Blocked by existing environment/setup issue:
`NameError: name '__path__' is not defined` at repo-root `__init__.py:11` (not introduced by this change).

- Runtime sanity check via direct Python execution confirmed the three expected ambiguity types are now emitted:
`temporal_conditional_normative_family_outvoted`, `conditional_scope_family_outvoted`, `deontic_scope_family_outvoted`.