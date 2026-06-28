Implemented a narrow compiler ambiguity-policy update for frame-vs-competing-family margins.

**Changes made**
- Added explicit frame-family ambiguity detection in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000003-20260517_154258/ipfs_datasets_py/logic/modal/compiler.py:246).
- New ambiguity type: `low_frame_modal_family_margin` (when a frame formula exists, but frame cue share is outmargined by another family under `modal_primary_family_margin`) at [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000003-20260517_154258/ipfs_datasets_py/logic/modal/compiler.py:328).
- Added focused unit coverage in [`test_modal_codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000003-20260517_154258/tests/unit_tests/logic/modal/test_modal_codec.py:222) asserting explicit frame/deontic ambiguity and negative margin metadata.

**Validation run**
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "family_margin_ambiguity"`  
  - Blocked by existing repo setup error: `NameError: name '__path__' is not defined` from root [`__init__.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000003-20260517_154258/__init__.py:11).
- Performed direct runtime check with `python3` to verify behavior:
  - ambiguity types include `low_frame_modal_family_margin`
  - candidate IDs `['frame', 'deontic']`
  - computed `family_margin` is negative as expected.