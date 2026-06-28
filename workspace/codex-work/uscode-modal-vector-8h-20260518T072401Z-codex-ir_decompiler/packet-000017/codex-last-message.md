Implemented a narrow IR/decompiler slot refinement for US Code section IDs with terminal punctuation.

**What changed**
- Added new citation slots in decompiler extraction:
  - `citation_section_raw`
  - `citation_section_normalized`
  - `citation_section_trailing_punct`
  - See [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000017-20260518_085309/ipfs_datasets_py/logic/modal/decompiler.py:965)
- Added `source_id_section_trailing_punct` in decompiler source-id slots.
  - See [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000017-20260518_085309/ipfs_datasets_py/logic/modal/decompiler.py:600)
- Mirrored the same behavior in F-logic triple projection / typed components so KG triples and slot features stay aligned.
  - See [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000017-20260518_085309/ipfs_datasets_py/logic/modal/codec.py:1072)

**Tests updated**
- Expanded citation-slot test to include `51 U.S.C. 60604.` and assert new trailing-punctuation slots/triples.
- Added assertions for `source_id_section_trailing_punct` in source-id slot test.
- See [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000017-20260518_085309/tests/unit_tests/logic/modal/test_modal_codec.py:2066)

**Validation run**
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "expand_alphanumeric_citation_section_slots or surface_uscode_source_id_slots"` → 2 passed
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "recovers_condition_exception_and_citation_slots"` → 1 passed
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_public_exports.py` → 2 passed