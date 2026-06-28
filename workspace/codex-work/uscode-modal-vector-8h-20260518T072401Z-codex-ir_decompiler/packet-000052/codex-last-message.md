Implemented a targeted `ir_decompiler` slot refinement for Roman-vs-alpha suffix typing.

**Changes**
- Updated suffix classification in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000052-20260518_122448/ipfs_datasets_py/logic/modal/decompiler.py:1322) and [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000052-20260518_122448/ipfs_datasets_py/logic/modal/codec.py:2244) to avoid misclassifying repeated Roman-token suffixes like `cc` as `roman`.
- Added `_is_probable_statutory_roman_suffix` in both files to preserve true clause-like Roman suffixes (for example `iii`) while treating repeated non-`i` tokens (`cc`, `xx`, etc.) as alpha.
- Added regression coverage for `42 U.S.C. 3797cc` in [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000052-20260518_122448/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:251) with decode and triple assertions.

**Validation**
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` (29 passed)
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_decompiler_surfaces_metadata_citation_slots_without_formulas tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_decompiler_and_triples_expand_alphanumeric_citation_section_slots` (2 passed)