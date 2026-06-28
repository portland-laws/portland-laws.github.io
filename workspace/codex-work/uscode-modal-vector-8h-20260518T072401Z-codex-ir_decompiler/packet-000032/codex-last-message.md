Implemented a narrow IR/decompiler slot refinement for numeric section structure.

- Added digit-count-by-position and digit-count-by-role slots in decompiler section parsing:
  - `citation_section_number_digit_count_positioned`
  - `citation_section_primary_number_digit_count`
  - `citation_section_terminal_number_digit_count`
  - Changes in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000032-20260518_103537/ipfs_datasets_py/logic/modal/decompiler.py:1432)

- Mirrored the same slot/predicate emission in codec F-logic projection (`modal_ir_to_flogic_triples` path via `_citation_section_components`) so decompiler slots and triple predicates stay aligned:
  - Changes in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000032-20260518_103537/ipfs_datasets_py/logic/modal/codec.py:1403)

- Extended regression coverage for mixed, single-component, and range citations/source IDs in both decoded slot maps and triple outputs:
  - Changes in [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000032-20260518_103537/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:95)

Validation run:

- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` passed (8/8).