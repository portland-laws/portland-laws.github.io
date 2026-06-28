Implemented a narrow `modal.ir_decompiler` slot refinement focused on U.S.C. section morphology consistency.

- Updated [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000043-20260518_113358/ipfs_datasets_py/logic/modal/decompiler.py:834) and [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000043-20260518_113358/ipfs_datasets_py/logic/modal/decompiler.py:1358) to always emit:
  - `source_id_section_raw`
  - `source_id_section_normalized`
  - `citation_section_raw`
  - `citation_section_normalized`
  even when raw and normalized values are identical.

- Mirrored the same deterministic behavior in F-logic triple generation in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000043-20260518_113358/ipfs_datasets_py/logic/modal/codec.py:1212) and [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000043-20260518_113358/ipfs_datasets_py/logic/modal/codec.py:1280).

- Added regression coverage in [test_modal_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000043-20260518_113358/tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py:1) for:
  - punctuated section (`1437q.`)
  - non-punctuated section (`3902`)
  across both decoded slot maps and emitted triples.

Tests run:
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py` (passed)
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_public_exports.py` (passed)