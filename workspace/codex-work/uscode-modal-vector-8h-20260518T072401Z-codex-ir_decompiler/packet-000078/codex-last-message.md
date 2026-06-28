Implemented a generalized IR/decompiler slot refinement for span structure, not sample-specific fixes.

**What changed**
- Added deterministic span-metric slots to decompiler output in [`decompiler.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000078-20260518_152400/ipfs_datasets_py/logic/modal/decompiler.py):
  - `modal_formula_count`
  - `source_text_char_count`
  - `modal_span_count`
  - `modal_span_char_count`
  - `source_context_span_count`
  - `source_context_span_char_count`
  - `support_span_start_char`, `support_span_end_char`, `support_span_width`
  - `modal_span_coverage_percent`
  - `modal_span_coverage_bucket` (`no_source_text`, `no_modal_span`, `sparse_coverage`, `partial_coverage`, `majority_coverage`, `high_coverage`, `full_coverage`)
  - plus numeric signature sub-slots via existing typed slot logic.
- Mirrored the same metrics into F-logic triple projection in [`codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000078-20260518_152400/ipfs_datasets_py/logic/modal/codec.py) so slot/triple surfaces stay aligned.
- Added regression tests in [`test_ir_decompiler_slots.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000078-20260518_152400/ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py) covering:
  - span metric slot emission,
  - span metric triple emission,
  - zero-formula `no_modal_span` behavior.

**Validation**
- `pytest -q ipfs_datasets_py/logic/modal/test_ir_decompiler_slots.py` passed.
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_ir_decompiler_slots.py` passed.
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py` passed.