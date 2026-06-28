Implemented a deterministic slot refinement for citation/source-id section delimiters so the IR/decompiler preserves punctuation structure (`hyphen`, `dot`, `mixed`) instead of only split components.

- Added delimiter parsing and emitted new slots in decompiler citation section logic:  
  [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000035-20260518_105210/ipfs_datasets_py/logic/modal/decompiler.py#L1411)  
  New slots include: `*_section_has_delimiter`, `*_section_delimiter_count`, `*_section_delimiter`, `*_section_delimiter_positioned`, `*_section_delimiter_token`, `*_section_delimiter_token_positioned`, `*_section_delimiter_char_count`, `*_section_delimiter_char_count_positioned`, `*_section_delimiter_pattern`, `*_section_delimiter_distinct_count`.

- Mirrored the same delimiter slot logic in codec triple projection to keep decompiler and F-logic parity:  
  [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000035-20260518_105210/ipfs_datasets_py/logic/modal/codec.py#L1382)

- Extended slot regression tests with:
  - hyphen-delimited assertions on existing samples,
  - explicit no-delimiter assertions on range samples,
  - new dot-delimited fixture and assertions for both decode and triples:  
  [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000035-20260518_105210/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py#L121)

Validation run:
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`  
- Result: `12 passed`