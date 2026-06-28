Implemented a deterministic U.S.C. parser improvement so zero-cue legal headings still compile to frame IR, including the three cited samples (`10 U.S.C. 2672`, `26 U.S.C. 45N`, `12 U.S.C. 548`).

**Code changes**
- Relaxed citation section matching to support `Sec`/`Sec.` and additional section delimiters (including dash variants), and reused that in both contains/start checks:  
[legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:50), [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:396), [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:418).
- Expanded section-heading fallback selection from only short “starts with section” spans to:
1) short start-matches, then
2) bounded longer start-matches, then
3) bounded embedded section-reference spans.  
This prevents empty-formula outcomes for common heading layouts:  
[legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py:591).

**Tests added**
- Parser replay fixtures for the 3 claimed sample IDs:  
[test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:228).
- spaCy compiler replay fixtures for the same 3 samples:  
[test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:147).
- Modal compiler-level replay test (regex backend) for the same 3 samples:  
[test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/tests/unit_tests/logic/modal/test_modal_codec.py:254).

**Small test-harness fix**
- Guarded repo-root package bootstrap so `__path__` is initialized before use during pytest collection:  
[__init__.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000013-20260518_081003/__init__.py:8).

**Validation run**
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py::test_parser_replays_embedded_sec_heading_zero_formula_samples tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py::test_spacy_compiler_replays_embedded_sec_heading_zero_formula_cases tests/unit_tests/logic/modal/test_modal_codec.py::test_modal_compiler_handles_embedded_sec_headings_for_known_uscode_samples` → `3 passed`.
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py tests/unit_tests/logic/modal/test_modal_codec.py -k "embedded_sec_heading or sec_prefixed or editorial_status_zero_formula or declarative_statement_zero_formula or transferred_heading"` → `19 passed, 65 deselected`.