Implemented a deterministic slot refinement for modal IR/decompiler citation sections: explicit terminal section identity and primary-vs-terminal relation slots are now emitted in both decoded slots and F-logic triples.

- Added new citation/source-id section slots in decompiler extraction:
  - `*_section_terminal`
  - `*_section_primary_equals_terminal`
  - `*_section_primary_terminal_pair`
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000056-20260518_125201/ipfs_datasets_py/logic/modal/decompiler.py#L1526)
- Mirrored the same logic in triple component extraction so slot/triple parity stays aligned:
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000056-20260518_125201/ipfs_datasets_py/logic/modal/codec.py#L1492)
- Extended regression coverage for both decode and triple paths (single-component and range citations):
  - [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000056-20260518_125201/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py#L647)
  - [test_modal_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000056-20260518_125201/tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py#L36)

Validation run:

- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py`
- Result: `33 passed`