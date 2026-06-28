Implemented a deterministic `ir_decompiler` refinement for range-aware provenance alignment: source-id vs citation now exposes explicit range endpoint and connector pair/match slots, with codec/decompiler parity.

- Added new alignment slots in decompiler:
  - `citation_source_id_section_range_start_pair|match|presence_match`
  - `citation_source_id_section_range_end_pair|match|presence_match`
  - `citation_source_id_section_range_connector_pair|match|presence_match`
  - Location: [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000073-20260518_144041/ipfs_datasets_py/logic/modal/decompiler.py:1473)

- Mirrored the same logic in triple projection so predicates stay aligned with decompiler slots:
  - Location: [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000073-20260518_144041/ipfs_datasets_py/logic/modal/codec.py:1874)

- Added regression coverage with both exact-range alignment and connector mismatch (`to` vs `through`):
  - New sample helper: [_range_connector_mismatch_sample_document](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000073-20260518_144041/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:147)
  - Slot-map assertions: [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000073-20260518_144041/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:2732)
  - Triple assertions: [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000073-20260518_144041/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:3004)

Tests run:

1. `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py -k "citation_source_id_alignment_slots or numeric_section_range_relation_slots or section_range_slots"` → `7 passed`
2. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py` → `8 passed`