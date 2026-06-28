Implemented a deterministic status-heading slot refinement in the IR decompiler lane:

- In [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000072-20260518_143011/ipfs_datasets_py/logic/modal/decompiler.py#L745), `_fallback_surface_text` now normalizes truncated `U.S.` status spans (e.g., `Transferred From the U`) to a stable status surface (`Transferred`) when a status fallback rule is detected.
- Added helper [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000072-20260518_143011/ipfs_datasets_py/logic/modal/decompiler.py#L788) `_status_heading_surface_text` for that deterministic collapse rule.
- Mirrored the same logic in KG triple generation so slot/triple parity stays aligned: [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000072-20260518_143011/ipfs_datasets_py/logic/modal/codec.py#L2945) and helper [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000072-20260518_143011/ipfs_datasets_py/logic/modal/codec.py#L2990).

Added regression coverage:

- New test in [test_modal_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000072-20260518_143011/tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py#L421) verifies both decoded slots and triples emit `fallback_surface_text == "Transferred"` for a `U.S.`-abbreviation-truncated transferred heading case.

Tests run:

1. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py` (8 passed)
2. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "transferred_status_keyword_slot or editorial_fallback_slots or fallback_text_for_heading_without_section_reference"` (3 passed)