Implemented a deterministic slot refinement for alpha suffix structure in the modal IR/decompiler path.

- Added new alpha-signature slots/components:
  - `*_repeat_kind` (`single`, `uniform_repeat`, `all_distinct`, `mixed_repeat`)
  - `*_max_run_length` (longest consecutive repeated-letter run)
- This now captures distinctions like `300mm`/`283ff` vs `21b`/`80p` directly in both decoded slots and F-logic triples.

Changed files:
- [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000062-20260518_132601/ipfs_datasets_py/logic/modal/decompiler.py:2262)
- [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000062-20260518_132601/ipfs_datasets_py/logic/modal/codec.py:2225)
- [test_modal_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000062-20260518_132601/tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py:202)

Validation run:
1. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py` (4 passed)
2. `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py -k "suffix_initial_ordinal_and_unique_char_count_slots or emits_positional_citation_slots"` (1 passed, 35 deselected)