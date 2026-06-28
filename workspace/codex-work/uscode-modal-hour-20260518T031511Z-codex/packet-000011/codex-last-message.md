Implemented the ambiguity-policy update so adaptive low-margin conflicts now surface explicit ambiguity types directly.

Changes made:
- Added explicit adaptive ambiguity records (pair-specific `ambiguity_type`) alongside the existing generic `adaptive_family_margin_low` record in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000011-20260518_040821/ipfs_datasets_py/logic/modal/compiler.py:565).
- Reused shared metadata for both records and added `adaptive_base_ambiguity_type` on explicit records for deterministic linkage in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000011-20260518_040821/ipfs_datasets_py/logic/modal/compiler.py:581).
- Updated adaptive-margin test coverage to assert explicit adaptive ambiguity types are emitted as first-class ambiguities in [`test_modal_codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000011-20260518_040821/tests/unit_tests/logic/modal/test_modal_codec.py:299).

Validation run:
- `python3 -m py_compile ipfs_datasets_py/logic/modal/compiler.py tests/unit_tests/logic/modal/test_modal_codec.py` passed.
- `python3 -m pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "adaptive_family_margin"` is currently blocked by an existing repo bootstrap error: `NameError: __path__ is not defined` in root [`__init__.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000011-20260518_040821/__init__.py:11).
- Direct runtime check confirmed emitted types now include:
  - `adaptive_temporal_conditional_normative_outvoted_margin_low`
  - `adaptive_temporal_deontic_outvoted_margin_low`
  - `adaptive_temporal_frame_outvoted_margin_low`