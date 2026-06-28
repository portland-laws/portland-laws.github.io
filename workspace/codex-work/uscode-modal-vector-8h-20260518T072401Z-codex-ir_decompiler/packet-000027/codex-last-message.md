Implemented a generalized `ir_decompiler` slot refinement that surfaces typed frame-candidate structure from IR.

- Updated [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000027-20260518_095515/ipfs_datasets_py/logic/modal/decompiler.py:178):
  - `decode_modal_ir_document` now emits frame-candidate phrases.
  - `selected_frame` now also emits typed identifier slots (e.g. `selected_frame_token`, `selected_frame_stem`).
- Added deterministic frame-candidate slot extraction in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000027-20260518_095515/ipfs_datasets_py/logic/modal/decompiler.py:781):
  - new slots: `frame_candidate`, `frame_candidate_rank`, `frame_candidate_ranked`, `frame_candidate_term`, plus typed token/stem/count variants.
  - candidates are sorted deterministically by score desc, then frame id.
- Added coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000027-20260518_095515/tests/unit_tests/logic/modal/test_modal_codec.py:3177):
  - `test_modal_decompiler_surfaces_ranked_frame_candidate_slots`.

Tests run:

1. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "frame_candidate_slots or falls_back_to_frame_logic_selected_frame"`  
   Result: `2 passed`
2. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "decompiler_and_triples or decompiler_preserves_context_without_formula_style_text or decompiler_recovers_condition_exception_and_citation_slots"`  
   Result: `12 passed`