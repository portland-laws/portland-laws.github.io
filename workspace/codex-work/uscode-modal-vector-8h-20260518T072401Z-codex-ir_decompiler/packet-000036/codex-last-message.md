Implemented a deterministic slot refinement for citation/source-id section suffix morphology, focused on the residual pattern in the TODO samples (`460iii-4`, `460aa-6`, `617t.`, etc.).

- Added new suffix morphology signals in decompiler slot extraction:
  - `*_section_suffix_kind` / `*_section_suffix_kind_positioned`
  - `*_section_primary_suffix_kind` / `*_section_terminal_suffix_kind`
  - `*_section_has_roman_suffix`
  - `*_section_primary_suffix_is_roman` / `*_section_terminal_suffix_is_roman`
  - `*_section_roman_suffix_component_count`
  - Roman detection is deterministic (`len>1` + Roman numeral regex), otherwise `alpha`.
  - Changes: [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657/ipfs_datasets_py/logic/modal/decompiler.py:1273), [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657/ipfs_datasets_py/logic/modal/decompiler.py:1389)

- Mirrored the same slot family in F-logic triple projection so decode/triple outputs stay aligned.
  - Changes: [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657/ipfs_datasets_py/logic/modal/codec.py:1360), [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657/ipfs_datasets_py/logic/modal/codec.py:1921)

- Extended regression tests:
  - Added a `16 U.S.C. 460iii-4` sample and assertions for roman suffix slots in both decompiler slot map and triples.
  - Added explicit non-roman assertions on existing positional sample.
  - Changes: [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:147), [test_ir_decompiler_slots.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py:464)

Validation run:

- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py`
- Result: `14 passed`