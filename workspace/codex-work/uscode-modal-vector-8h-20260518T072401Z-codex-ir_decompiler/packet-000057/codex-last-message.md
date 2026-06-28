Implemented a narrow deterministic slot refinement for `modal.ir_decompiler`: citation-to-source-id provenance alignment signals.

**What changed**
- Added formula-level alignment slots in decompiler output:
  - `citation_source_id_alignment` (`exact_match|title_only_match|section_only_match|mismatch|unparsed`)
  - `citation_source_id_title_match`
  - `citation_source_id_section_match`
  - `citation_source_id_title_section_key_match`
  - `citation_source_id_canonical_match`
- Emission point: [_decode_formula_phrases](//home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/decompiler.py:327), call added at [decompiler.py:576](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/decompiler.py:576), helper at [decompiler.py:940](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/decompiler.py:940).
- Mirrored the same logic into F-logic triple generation:
  - call at [codec.py:1119](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/codec.py:1119)
  - helper at [codec.py:1406](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/codec.py:1406)

**Tests added**
- Added mismatch fixture and new regression tests in [test_ir_decompiler_slots.py:43](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:43), [test_ir_decompiler_slots.py:2000](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:2000), and [test_ir_decompiler_slots.py:2021](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:2021).

**Validation**
- Ran: `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`
- Result: `33 passed` (previously 31; 2 new tests).