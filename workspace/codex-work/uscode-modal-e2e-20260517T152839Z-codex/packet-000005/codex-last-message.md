Implemented a deterministic ambiguity-policy update for temporal-dominant family conflicts and added focused tests.

**Code changes**
- Added lexical ambiguity-signal helper in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py#L471) and frame-context token set at [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py#L32).
- Added compiler config knob `modal_temporal_target_family_outvote_margin` at [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/ipfs_datasets_py/logic/modal/compiler.py#L53).
- Added explicit temporal-vs-target-family ambiguity emission in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/ipfs_datasets_py/logic/modal/compiler.py#L457), producing:
  - `temporal_conditional_normative_family_outvoted`
  - `temporal_frame_family_outvoted`
- Wired that policy into `_family_ambiguities` flow at [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/ipfs_datasets_py/logic/modal/compiler.py#L331).

**Tests added**
- New targeted tests at [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/tests/unit_tests/logic/modal/test_modal_codec.py#L263):
  - `test_modal_compiler_surfaces_temporal_conditional_family_outvote_ambiguity`
  - `test_modal_compiler_surfaces_temporal_frame_family_outvote_ambiguity`

**Validation run**
- `pytest` on the modal test file is currently blocked by a pre-existing repo issue: `NameError: __path__ is not defined` in [__init__.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000005-20260517_155233/__init__.py#L11).
- Syntax check passed:
  - `python3 -m py_compile ...` on all modified files.
- Runtime behavior check passed with direct compiler assertions for both new ambiguity types and existing primary-family ambiguity behavior.