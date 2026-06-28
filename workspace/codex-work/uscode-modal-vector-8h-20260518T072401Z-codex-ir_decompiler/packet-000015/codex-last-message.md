Implemented one generalized `modal.ir_decompiler` slot refinement across decompiler + triple projection:

- Added typed token slots for each formula `predicate` in decompiler output (`predicate_token_count`, `predicate_token_prefix`, `predicate_token_suffix`, `predicate_token`, `predicate_stem`).
- Added typed token slots for `citation_section` in decompiler citation slot expansion.
- Mirrored both enrichments in F-logic triple emission so IR-derived triples and decompiler slots stay aligned.

Changes:
- [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118/ipfs_datasets_py/logic/modal/decompiler.py:304)
- [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118/ipfs_datasets_py/logic/modal/decompiler.py:870)
- [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118/ipfs_datasets_py/logic/modal/codec.py:722)
- [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118/ipfs_datasets_py/logic/modal/codec.py:1055)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118/tests/unit_tests/logic/modal/test_modal_codec.py:1898)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118/tests/unit_tests/logic/modal/test_modal_codec.py:2014)

Validation run:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py`  
  Result: `63 passed`.