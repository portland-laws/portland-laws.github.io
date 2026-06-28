Implemented deterministic regression fixtures for packet `000519` by adding replay tests (and sample text fixtures) for all 3 cited sample IDs in both parser and compiler test suites.

**What changed**
- Added new packet text fixtures and assertions in spaCy compiler tests:  
  [test_spacy_modal_codec.py:92](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000519-20260518_132944/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:92)  
  [test_spacy_modal_codec.py:504](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000519-20260518_132944/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py:504)
- Added matching parser-level replay fixtures/assertions:  
  [test_legal_modal_parser.py:77](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000519-20260518_132944/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:77)  
  [test_legal_modal_parser.py:1006](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000519-20260518_132944/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py:1006)

**Coverage added**
- `us-code-25-507-e22029a3cea8b735`: asserts deterministic codification fallback (`__uscode_codification_fallback__`, `uscode_transferred_heading_v1`) so the prior zero-formula case is guarded.
- `us-code-10-167-c04be565137bd57c` and `us-code-38-8112-c323ef8fcde15329`: assert non-empty symbolic output, citation provenance preservation, and deontic-family presence for symbolic-validity regression protection.

**Validation run**
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py::test_spacy_compiler_replays_packet_todo_samples_for_25_507_10_167_and_38_8112 tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py::test_parser_replays_packet_todo_samples_for_25_507_10_167_and_38_8112`
- Result: `2 passed`