Implemented a deterministic `modal.ir_decompiler` slot refinement for provenance alignment comparisons.

- Added new comparative alignment slots in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000069-20260518_140942/ipfs_datasets_py/logic/modal/decompiler.py:1219):
  - `citation_source_id_title_pair`
  - `citation_source_id_section_pair`
  - `citation_source_id_title_section_key_pair`
  - `citation_source_id_canonical_pair`
  - `citation_source_id_title_number_relation` / `_span`
  - `citation_source_id_section_primary_number_relation` / `_span`
  - `citation_source_id_section_primary_suffix_pair` / `_match` / `_presence_match`
  - `citation_source_id_section_primary_component_signature_pair` / `_match`

- Mirrored the same slot logic in F-logic triple projection in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000069-20260518_140942/ipfs_datasets_py/logic/modal/codec.py:1651) so decoded slot and triple outputs stay aligned.

- Extended regression coverage for aligned/mismatch/trailing-punctuation mismatch cases (both decode and triple paths) in [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000069-20260518_140942/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:2570).

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` (44 passed)