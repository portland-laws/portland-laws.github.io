Implemented a focused IR/decompiler slot refinement: document-level `modal_family_counts` metadata is now surfaced as deterministic decompiler slots and mirrored F-logic triples.

- Decompiler now emits `modal_family_count*` slots from `modal_ir.metadata["modal_family_counts"]`:
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000029-20260518_101414/ipfs_datasets_py/logic/modal/decompiler.py#L178)
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000029-20260518_101414/ipfs_datasets_py/logic/modal/decompiler.py#L705)

- Triple projection now emits matching document-level predicates:
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000029-20260518_101414/ipfs_datasets_py/logic/modal/codec.py#L677)
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000029-20260518_101414/ipfs_datasets_py/logic/modal/codec.py#L1261)

- Added regression coverage for both slot and triple emission:
  - [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000029-20260518_101414/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py#L283)

Tests run:

1. `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` (8 passed)
2. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "surface_uscode_source_id_slots or include_statutory_scope_reference_slots or surface_declarative_statement_hint_slot"` (3 passed)