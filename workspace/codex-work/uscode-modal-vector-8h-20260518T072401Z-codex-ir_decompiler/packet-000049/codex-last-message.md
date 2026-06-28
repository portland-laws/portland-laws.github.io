Implemented a deterministic numeric-slot refinement for `ir_decompiler` by extending numeric signatures with zero-pattern features.

- Added three slots to numeric signatures in both decompiler and codec:
  - `*_zero_digit_count`
  - `*_has_zero_digit`
  - `*_trailing_zero_count`
- Updated implementations in:
  - [decompiler.py:1856](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000049-20260518_120429/ipfs_datasets_py/logic/modal/decompiler.py:1856)
  - [codec.py:1805](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000049-20260518_120429/ipfs_datasets_py/logic/modal/codec.py:1805)

Expanded regression coverage for these new slots (including a TODO-aligned `43 U.S.C. 1470.` sample) in:
- [_zero_digit_signature_sample_document in test_ir_decompiler_slots.py:291](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000049-20260518_120429/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:291)
- [numeric signature decode test:1163](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000049-20260518_120429/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:1163)
- [numeric signature triples test:1301](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000049-20260518_120429/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:1301)

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py -k "numeric_signature"`: 2 passed
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`: 25 passed