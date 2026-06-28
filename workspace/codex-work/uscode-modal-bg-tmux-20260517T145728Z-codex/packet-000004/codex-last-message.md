Implemented the modal ambiguity policy as deterministic compiler logic.

- Added `family_score_margin` config (default `0.15`) and family-margin ambiguity detection in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000004-20260517_151320/ipfs_datasets_py/logic/modal/compiler.py:47).
- Compiler now computes modal-family probabilities from existing encoding cues and emits `low_modal_family_margin` when `target_probability - best_other_probability <= family_score_margin` in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000004-20260517_151320/ipfs_datasets_py/logic/modal/compiler.py:268).
- Ambiguity metadata includes `family_margin`, `target_family`, `predicted_family`, probabilities, and candidate families in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000004-20260517_151320/ipfs_datasets_py/logic/modal/compiler.py:315).
- Added a focused unit test for this behavior in [`test_modal_codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000004-20260517_151320/tests/unit_tests/logic/modal/test_modal_codec.py:146).

Validation run:

- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "modal_compiler_decompiler_are_explainable_and_deterministic or modal_compiler_exposes_low_family_margin_ambiguity"`  
  failed before running tests due existing repo issue: `NameError: name '__path__' is not defined` in top-level `__init__.py`.
- `python3 -m py_compile ipfs_datasets_py/logic/modal/compiler.py tests/unit_tests/logic/modal/test_modal_codec.py` passed.
- Direct runtime sanity check with `python3` confirmed:
  `low_modal_family_margin` is emitted, with `target_family=deontic`, `best_other_family=temporal`, `family_margin=0.0`.

Patch artifact generated as requested:

- [`changes.patch`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000004-20260517_151320/changes.patch)