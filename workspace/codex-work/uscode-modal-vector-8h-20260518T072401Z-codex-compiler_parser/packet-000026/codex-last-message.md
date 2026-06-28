Implemented a narrow deterministic parser improvement for heading-only U.S. Code text and added packet-specific replay fixtures.

### What changed
- Relaxed heading-only fallback detection in [`legal_modal_parser.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000026-20260518_102017/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py#L67):
  - allow single-token headings (`min tokens` from `2` → `1`)
  - allow compact comma/semicolon heading punctuation while still rejecting stronger clause punctuation
  - keeps existing verb/hint guards intact
- Added parser replay fixtures/tests for:
  - `us-code-6-314-afaf3a4084d6428b`
  - `us-code-35-4-50bdd346f6009649`
  - `us-code-7-7316-85781f95eae6399d`
  in [`test_legal_modal_parser.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000026-20260518_102017/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py#L542).
- Added compiler-level replay test for the same three packet samples in [`test_modal_codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000026-20260518_102017/tests/unit_tests/logic/modal/test_modal_codec.py#L746), asserting no `missing_modal_formula` ambiguity and expected frame fallback metadata.

### Tests run
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "packet_todo_heading_only_samples_for_6_314_35_4_and_7_7316"` ✅
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "packet_todo_heading_only_samples_for_6_314_35_4_and_7_7316"` ✅
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "heading_only_zero_formula_cases_for_25_422_48_1572_and_42_6323 or packet_todo_samples_for_7_431_6_257_and_45_81_to_92"` ✅
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "heading_only_zero_formula_cases_for_25_422_48_1572_and_42_6323 or packet_todo_samples_for_7_431_6_257_and_45_81_to_92"` ✅