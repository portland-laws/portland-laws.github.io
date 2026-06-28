Implemented a narrow deterministic parser fallback plus a golden regression case for the claimed sample.

Changes:
- Added U.S.C. editorial-status fallback detection (`repealed|omitted|reserved|vacant|renumbered|terminated`) and formula emission when no modal cues are present, after existing codification fallback:
  - [legal_modal_parser.py:36](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000003-20260518_031532/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:36)
  - [legal_modal_parser.py:168](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000003-20260518_031532/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:168)
  - [legal_modal_parser.py:342](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000003-20260518_031532/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:342)
  - [legal_modal_parser.py:438](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000003-20260518_031532/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:438)
- Added golden parser regression for `us-code-18-3008-62db8e945327b1ec` / `18 U.S.C. 3008`:
  - [test_legal_modal_parser.py:141](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000003-20260518_031532/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:141)

Validation:
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k "codification_fallback or transferred_heading_zero_formula or editorial_status_zero_formula"` fails due a pre-existing repo bootstrap error: `NameError: __path__ is not defined` in repo-root `__init__.py`.
- Direct runtime verification of parser behavior passed for:
  - `§3008. Repealed.` + `18 U.S.C. 3008` -> emits frame fallback `__uscode_editorial_status_fallback__`
  - Existing transferred/codification fallback cases still emit expected frame fallbacks.