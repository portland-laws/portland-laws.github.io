Implemented a deterministic parser improvement for heading-only U.S.C. text (no `§`/`Sec.` marker), plus golden regressions for the three claimed samples.

- Parser rule update in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:54):
  - Added bounded heading-only heuristics (`_USCODE_HEADING_ONLY_*`) and `_looks_like_heading_without_section_reference(...)` at [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:836).
  - Extended section-heading fallback selection to use this path when explicit section references are absent at [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:693).
  - Emits fallback metadata rule `uscode_heading_without_section_reference_v1` for these cases at [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:735).

- Added golden regression fixtures/tests for:
  - `us-code-25-422-f3f166961e45b585`
  - `us-code-48-1572.-8711c64e2d6b256c`
  - `us-code-42-6323.-1c7e7d2f53c36e15`
- Test additions are in:
  - [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:476)
  - [test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:288)
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000016-20260518_084236/tests/unit_tests/logic/modal/test_modal_codec.py:524)

Validation run:

- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py tests/unit_tests/logic/modal/test_modal_codec.py`
- Result: `98 passed`