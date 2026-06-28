Implemented a focused IR/decompiler slot refinement for citation/source-id alignment by adding raw-section and trailing-punctuation agreement signals.

**Changes**
- Added new provenance alignment slots in decompiler output:
  - `citation_source_id_section_raw_match`
  - `citation_source_id_section_raw_pair`
  - `citation_source_id_section_trailing_punct_presence_match`
  - `citation_source_id_section_trailing_punct_match`
  - `citation_source_id_section_trailing_punct_pair`
  - File: [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000058-20260518_130350/ipfs_datasets_py/logic/modal/decompiler.py:940)

- Mirrored the same alignment components in F-logic triple projection so IR/decompiler and triple paths stay consistent.
  - File: [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000058-20260518_130350/ipfs_datasets_py/logic/modal/codec.py:1406)

- Added regression coverage including a punctuation-only mismatch case (`source_id` has `10318.` while citation has `10318`) and assertions for all new slots in both decompiler slot maps and triple predicates.
  - File: [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000058-20260518_130350/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:69)
  - File: [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000058-20260518_130350/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:2026)

**Validation**
- Ran:
  - `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py`
- Result: `35 passed`