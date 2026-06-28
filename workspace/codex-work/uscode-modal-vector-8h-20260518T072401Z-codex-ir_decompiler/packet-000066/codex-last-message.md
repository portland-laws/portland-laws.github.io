Implemented a deterministic decompiler/IR slot refinement for section components by adding explicit number+suffix pair slots (including positioned, primary, and terminal variants), then mirrored the same predicates in triple projection.

- Added new slots in decompiler section parsing:
  - `citation_section_number_suffix_pair`
  - `citation_section_number_suffix_pair_positioned`
  - `citation_section_primary_number_suffix_pair`
  - `citation_section_terminal_number_suffix_pair`
  - in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000066-20260518_135253/ipfs_datasets_py/logic/modal/decompiler.py:1963)

- Added the same component predicates to F-logic projection path so `modal_ir_to_flogic_triples` stays slot-parity aligned with decompiler:
  - in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000066-20260518_135253/ipfs_datasets_py/logic/modal/codec.py:1897)

- Extended regression coverage for both decoded slot maps and emitted triples across mixed/alphanumeric/numeric/range section shapes:
  - in [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000066-20260518_135253/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:1546)

Validation run:

- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py -k "section_profile_and_number_relation"` → 2 passed
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` → 40 passed