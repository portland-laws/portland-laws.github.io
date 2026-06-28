Implemented a focused `ir_decompiler` slot refinement for coarse U.S.C. heading fallbacks.

**Changes**
- Updated heading-tail extraction to support both fallback rules:
  - `uscode_section_heading_v1`
  - `uscode_section_heading_coarse_v1`
- Applied in both decompiler and triple-emission paths:
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000048-20260518_115943/ipfs_datasets_py/logic/modal/decompiler.py:61)
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000048-20260518_115943/ipfs_datasets_py/logic/modal/codec.py:203)

- Added coarse-fallback regression coverage (decoded slots + F-logic triples):
  - [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000048-20260518_115943/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:261)

**Validation**
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` → `25 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "surface_section_heading_tail_slots or surface_fallback_text_for_heading_without_section_reference"` → `2 passed`