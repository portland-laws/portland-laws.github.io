Implemented a narrow IR/decompiler slot refinement for trailing punctuation presence/absence, aligned across decompiler and F-logic triple emission.

- Added explicit negative slots when no trailing punctuation is present:
  - `*_section_has_trailing_punct = "false"`
  - `*_section_trailing_punct_count = "0"`
- Kept positive behavior unchanged (`"true"` + actual punct + count).

Updated files:
- [decompiler.py:844](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130/ipfs_datasets_py/logic/modal/decompiler.py:844)
- [decompiler.py:1376](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130/ipfs_datasets_py/logic/modal/decompiler.py:1376)
- [codec.py:1222](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130/ipfs_datasets_py/logic/modal/codec.py:1222)
- [codec.py:1293](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130/ipfs_datasets_py/logic/modal/codec.py:1293)
- Added regression tests for absence case:
  - [test_ir_decompiler_slots.py:753](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:753)
  - [test_ir_decompiler_slots.py:766](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:766)

Validation:
- Ran `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`
- Result: `20 passed`