Implemented a focused IR/decompiler slot refinement: citation/source-id numeric signatures are now emitted for title numbers and section numbers (including positioned section variants), in both decoded phrase slots and F-logic triples.

Changed files:
- [decompiler.py:820](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/decompiler.py:820)
- [decompiler.py:1336](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/decompiler.py:1336)
- [decompiler.py:1540](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/decompiler.py:1540)
- [decompiler.py:1807](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/decompiler.py:1807)
- [codec.py:1185](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/codec.py:1185)
- [codec.py:1267](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/codec.py:1267)
- [codec.py:1502](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/codec.py:1502)
- [codec.py:1770](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/codec.py:1770)
- [test_ir_decompiler_slots.py:949](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:949)

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` (18 passed)