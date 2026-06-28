Implemented the ambiguity-policy update in the compiler scope and added focused tests.

**What Changed**
- Passed frame selection context into modal-family ambiguity evaluation so adaptive ambiguity can use structural frame evidence:
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/ipfs_datasets_py/logic/modal/compiler.py#L158)
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/ipfs_datasets_py/logic/modal/compiler.py#L259)
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/ipfs_datasets_py/logic/modal/compiler.py#L525)

- Adaptive ambiguity now treats BM25 frame lexical matches as valid frame-support evidence (`has_frame_bm25_support`), enabling explicit temporal-vs-frame ambiguity even when frame-context token heuristics are absent:
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/ipfs_datasets_py/logic/modal/compiler.py#L545)
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/ipfs_datasets_py/logic/modal/compiler.py#L644)

- Expanded conditional-scope phrase signals to include “for purposes of” / “for the purposes of”:
  - [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py#L32)

- Added targeted tests for both new policies:
  - BM25-backed temporal/frame adaptive ambiguity:
    - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/tests/unit_tests/logic/modal/test_modal_codec.py#L372)
  - “for purposes of” conditional signal:
    - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305/tests/unit_tests/logic/modal/test_modal_codec.py#L624)

**Validation**
- Attempted targeted pytest run, but test setup fails in this repo environment due root `__init__.py` (`NameError: __path__ is not defined`) before test execution.
- Syntax validation passed:
  - `python3 -m py_compile ipfs_datasets_py/logic/modal/compiler.py ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py tests/unit_tests/logic/modal/test_modal_codec.py`