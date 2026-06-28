Implemented a deterministic U.S. Code “citation-context” rescue fallback so `modal.compiler` no longer emits empty IR when text has no modal cues and no recoverable section-heading pattern.

### Changes
- Added a final fallback stage in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000033-20260518_111719/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:312) that:
  - runs only for U.S.C. citations with zero extracted cues
  - derives a compact context segment
  - emits a deterministic frame formula with:
    - `cue="__uscode_citation_context_fallback__"`
    - `fallback_rule="uscode_citation_context_v1"`
- Implemented helper methods in [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000033-20260518_111719/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:1085) and token-threshold constants at [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000033-20260518_111719/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:70).

### Regression tests added
- Parser-level packet-citation coverage in [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000033-20260518_111719/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:1067).
- Compiler-level (both `regex` and `spacy` backends) coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000033-20260518_111719/tests/unit_tests/logic/modal/test_modal_codec.py:1394).

### Targeted test runs
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py -k uscode_citation_context_fallback` → `1 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k uscode_citation_context_fallback` → `1 passed`