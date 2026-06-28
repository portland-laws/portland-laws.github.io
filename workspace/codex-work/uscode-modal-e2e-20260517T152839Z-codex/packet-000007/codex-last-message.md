Implemented a deterministic ambiguity policy for non-temporal, non-frame predictions that outvote a frame interpretation when frame signals are present.

**Changes**
- Added new compiler config threshold `modal_frame_target_family_outvote_margin` and new ambiguity branch `frame_scope_family_outvoted` in:
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000007-20260517_160912/ipfs_datasets_py/logic/modal/compiler.py)
- Added unit coverage for deontic-over-frame outvote behavior and made one existing assertion order-independent (to avoid brittleness from additional ambiguities):
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000007-20260517_160912/tests/unit_tests/logic/modal/test_modal_codec.py)

**Validation**
- Ran:
  - `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py --rootdir=tests`
- Result:
  - `16 passed`