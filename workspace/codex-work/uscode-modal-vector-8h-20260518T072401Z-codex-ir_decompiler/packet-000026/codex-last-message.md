Implemented a deterministic section-range slot refinement for `modal.ir_decompiler` and mirrored it in triple emission.

- Updated [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000026-20260518_095026/ipfs_datasets_py/logic/modal/decompiler.py:64) to:
  - Accept U.S.C. sections with range connectors (`to|through|thru`) in citation parsing.
  - Detect range sections in `_citation_section_slots` and emit typed slots:
    - `citation_section_range`
    - `citation_section_range_start`
    - `citation_section_range_end`
    - `citation_section_range_connector`
  - Continue emitting positioned component/number/suffix slots using range endpoints.

- Updated [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000026-20260518_095026/ipfs_datasets_py/logic/modal/codec.py:104) with the same logic in `_citation_components` / `_citation_section_components`, so F-logic triples stay aligned with decompiler slots (including mapped `source_id_section_*` range slots).

- Added regression coverage in [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000026-20260518_095026/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:129):
  - `test_decode_modal_ir_document_emits_section_range_slots`
  - `test_modal_ir_to_flogic_triples_emits_section_range_slots`
  - Uses `45 U.S.C. 228a to 228c` and `us-code-45-228a to 228c-...` to verify both citation and source-id range slots.

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` -> `4 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "expand_alphanumeric_citation_section_slots or surface_uscode_source_id_slots"` -> `2 passed, 70 deselected`