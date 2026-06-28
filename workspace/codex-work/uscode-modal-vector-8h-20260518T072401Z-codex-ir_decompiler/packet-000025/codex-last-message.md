Implemented a deterministic slot refinement for citation/source-id alphanumeric suffixes so case information is preserved in both the decompiler and typed triples.

- Added new slots in decompiler + triple expansion:
  - `citation_section_suffix_normalized`
  - `citation_section_suffix_case` (`lower|upper|mixed`)
  - `citation_section_suffix_case_positioned`
  - Source-id equivalents are inherited via existing `citation_section* -> source_id_section*` mapping.
- Added shared helper `_alpha_case_kind(...)` in both paths.

Changed files:
- [decompiler.py:1065](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317/ipfs_datasets_py/logic/modal/decompiler.py:1065)
- [decompiler.py:1213](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317/ipfs_datasets_py/logic/modal/decompiler.py:1213)
- [codec.py:1297](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317/ipfs_datasets_py/logic/modal/codec.py:1297)
- [codec.py:1538](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317/ipfs_datasets_py/logic/modal/codec.py:1538)
- [test_ir_decompiler_slots.py:50](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:50)
- [test_modal_codec.py:2389](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317/tests/unit_tests/logic/modal/test_modal_codec.py:2389)

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` -> `2 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "alphanumeric_citation_section_slots or surface_uscode_source_id_slots"` -> `2 passed, 69 deselected`