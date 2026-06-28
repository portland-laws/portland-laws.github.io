Implemented a narrow IR/decompiler slot refinement for source-id sections with trailing punctuation.

- Updated decompiler source-id slot extraction so `source_id_section` is canonicalized to normalized section text, and added explicit `source_id_section_raw` when raw differs (for example `171a.` vs `171a`): [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000018-20260518_085809/ipfs_datasets_py/logic/modal/decompiler.py:633)
- Mirrored the same behavior in codec F-logic component emission to keep IR/decompiler/graph features aligned: [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000018-20260518_085809/ipfs_datasets_py/logic/modal/codec.py:1146)
- Added a regression test validating both decoded slot map and emitted triples for dotted section IDs: [test_modal_decompiler_source_id_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000018-20260518_085809/tests/unit/optimizers/logic_theorem_optimizer/test_modal_decompiler_source_id_slots.py:50)

Tests run:

1. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_decompiler_source_id_slots.py` passed.
2. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_public_exports.py` passed.