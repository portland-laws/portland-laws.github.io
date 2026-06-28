Implemented a deterministic slot refinement for citation/source-id section parsing by adding explicit suffix-presence booleans and validating them end-to-end.

- Added new section slots in both decompiler and triple projection:
  - `citation_section_has_suffix`
  - `citation_section_primary_has_suffix`
  - `citation_section_terminal_has_suffix`
  - `source_id_section_has_suffix` / `source_id_section_primary_has_suffix` / `source_id_section_terminal_has_suffix` (via existing `citation_section`→`source_id_section` mapping)
- Code updates:
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000034-20260518_104523/ipfs_datasets_py/logic/modal/decompiler.py:1555)
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000034-20260518_104523/ipfs_datasets_py/logic/modal/codec.py:1526)
- Expanded regression coverage across mixed/alphanumeric, range, single-component, and numeric-with-trailing-punct cases:
  - [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000034-20260518_104523/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:149)

Tests run:
1. `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`  
2. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "expand_alphanumeric_citation_section_slots or surface_uscode_source_id_slots"`

Both passed.