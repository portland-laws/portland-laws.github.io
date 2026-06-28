Implemented a narrow deterministic parser improvement for the compiler/parser scope and added golden regression coverage for the 3 cited sample IDs.

- Updated article-prefixed heading heuristics in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000769-20260518_141203/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:96):
  - Added heading noun support for `commission/offices/condition(s)`.
  - Added explicit allowance for `The terms and conditions ...` headings.
- Updated declarative fallback behavior in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000769-20260518_141203/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:727):
  - Preserved strict citation-section matching when section refs are present.
  - Added standalone declarative fallback for short `There is/are established...` style clauses when no in-text section reference exists.
- Added deterministic golden regression tests in [test_legal_modal_parser_deterministic_rules.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000769-20260518_141203/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py:1):
  - `us-code-2-121f-6dce78c9ec9c6d4b` (previous no-formula shape).
  - `us-code-42-290aa-a8d1719e0c2a8388` (declarative establishment clause).
  - `us-code-16-820-e78ad24dbc049dea` (terms/conditions heading).
  - Compiler integration check ensures no `missing_modal_formula` ambiguity for these cases on `spacy` backend.

Validation run:
- `IPFS_DATASETS_PY_MINIMAL_IMPORTS=1 IPFS_DATASETS_AUTO_INSTALL=false IPFS_KIT_AUTO_INSTALL_DEPS=0 pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py`
- Result: `4 passed`.