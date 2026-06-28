Implemented a narrow `modal.ir_decompiler` slot refinement for trailing section punctuation and kept codec/decompiler parity.

- Added deterministic negative-slot emission when trailing punctuation is absent:
  - `*_section_has_trailing_punct = "false"`
  - `*_section_trailing_punct_count = "0"`
  - in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519/ipfs_datasets_py/logic/modal/decompiler.py:890) and [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519/ipfs_datasets_py/logic/modal/codec.py:1289)

- Added typed trailing punctuation kind slots when present:
  - `citation_section_trailing_punct_kind`
  - `source_id_section_trailing_punct_kind`
  - helper in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519/ipfs_datasets_py/logic/modal/decompiler.py:1470) and [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519/ipfs_datasets_py/logic/modal/codec.py:1982)

- Extended modal slot regressions for the new negative and kind slots in [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:369)

- Updated existing codec-level expectations for mixed punctuated/non-punctuated formula sets in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519/tests/unit_tests/logic/modal/test_modal_codec.py:2958)

Validation run:

- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` -> 31 passed
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "citation_section or source_id_section"` -> 1 passed