Implemented the ambiguity-policy TODO by extending adaptive explicit ambiguity coverage for deontic conflicts.

Changes made:
- Added `deontic -> temporal` and `deontic -> alethic` to adaptive target-family checks in [`compiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000012-20260518_041230/ipfs_datasets_py/logic/modal/compiler.py:543).
- Added two regression tests for explicit adaptive ambiguities:
  - `adaptive_deontic_temporal_outvoted_margin_low`
  - `adaptive_deontic_alethic_outvoted_margin_low`
  in [`test_modal_codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000012-20260518_041230/tests/unit_tests/logic/modal/test_modal_codec.py:405).

Validation:
- Attempted targeted pytest run, but test setup fails in this repo due existing bootstrap issue at [`__init__.py:11`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000012-20260518_041230/__init__.py:11) (`NameError: __path__ is not defined`).
- Ran a focused `python3` runtime check to verify behavior; it now emits:
  - `adaptive_deontic_temporal_outvoted_margin_low`
  - `adaptive_deontic_alethic_outvoted_margin_low`
  alongside corresponding `adaptive_family_margin_low` entries.