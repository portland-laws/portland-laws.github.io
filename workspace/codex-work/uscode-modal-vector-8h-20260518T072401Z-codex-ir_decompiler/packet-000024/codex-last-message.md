Implemented a generalized citation-structure slot refinement for the IR/decompiler path: section components now keep deterministic positional pairing (component/number/suffix/kind), which improves representation of patterns like `360bbb-0`, `2349cc-1`, and trailing-dot-normalized sections.

Changed files:
- Added positional citation slots in decompiler extraction at [ipfs_datasets_py/logic/modal/decompiler.py:1166](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000024-20260518_093639/ipfs_datasets_py/logic/modal/decompiler.py:1166)
- Added matching positional citation components in codec/F-logic extraction at [ipfs_datasets_py/logic/modal/codec.py:1264](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000024-20260518_093639/ipfs_datasets_py/logic/modal/codec.py:1264)
- Added regression tests at [ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:1](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000024-20260518_093639/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:1)

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`
- Result: `2 passed`