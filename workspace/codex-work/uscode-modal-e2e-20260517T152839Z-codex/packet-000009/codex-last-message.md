Implemented a narrow ambiguity-policy expansion for modal family conflicts and added focused coverage.

- Added two compiler ambiguity policies in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144/ipfs_datasets_py/logic/modal/compiler.py:53):
  `conditional_scope_family_outvoted` and `deontic_scope_family_outvoted`, with explicit `predicted_family`, `target_family`, and `family_margin` metadata, and new config thresholds.
- Wired those policies into family ambiguity evaluation in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144/ipfs_datasets_py/logic/modal/compiler.py:355).
- Strengthened deterministic temporal ambiguity signaling in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:32) by:
  temporal phrase detection (`not later than`, `effective date`, `fiscal year`, etc.) and a new `has_deontic_cue` signal in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:509).
- Added targeted tests for the new policies and the `not later than` temporal signal in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144/tests/unit_tests/logic/modal/test_modal_codec.py:366).

Validation run:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "..."` failed due a pre-existing test environment issue: root [`__init__.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144/__init__.py:11) raises `NameError: __path__ is not defined`.
- Verified new behavior with direct `python3` assertion script invoking the compiler; it completed successfully (`ok`).

Next step:
1. If you want, I can patch the root `__init__.py` guard so pytest can run these tests normally in this worktree.