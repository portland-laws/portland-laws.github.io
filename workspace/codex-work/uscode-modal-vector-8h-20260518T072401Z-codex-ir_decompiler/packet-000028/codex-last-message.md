Implemented a narrow IR/decompiler slot refinement for U.S.C. section structure: citation/source-id section parsing now emits explicit **primary** and **terminal** component roles (number/suffix/component-kind), which better represents sections like `190l`, `60e-3`, and `460bbb-5`.

### Changes
- Added new section-role slot/triple emissions in decompiler slot extraction:
  - `citation_section_primary_number`, `citation_section_terminal_number`
  - `citation_section_primary_suffix`, `citation_section_terminal_suffix`
  - `citation_section_primary_component_kind`, `citation_section_terminal_component_kind`
  - plus normalized/case variants for primary/terminal suffixes
- Mirrored the same logic in codec triple component extraction so decompiler slots and F-logic triples stay aligned.
- Extended focused regression tests to cover:
  - primary/terminal role slots on multi-component section IDs
  - primary/terminal role slots on single-component alphanumeric section IDs (`190l`)

Files:
- [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000028-20260518_100545/ipfs_datasets_py/logic/modal/decompiler.py)
- [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000028-20260518_100545/ipfs_datasets_py/logic/modal/codec.py)
- [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000028-20260518_100545/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py)

### Validation
Ran:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` (6 passed)
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "expand_alphanumeric_citation_section_slots or surface_uscode_source_id_slots"` (2 passed)