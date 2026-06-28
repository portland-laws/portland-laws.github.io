Implemented a deterministic parser rule extension for U.S. Code editorial-status headings and added golden replay cases for the three TODO sample IDs.

**Changes**
- Extended editorial-status prefix handling in parser fallback so split headings like `§<section>. Renumbered/Terminated/Vacant.` produce a frame fallback formula instead of zero formulas: [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000011-20260518_075352/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py#L42), [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000011-20260518_075352/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py#L587).
- Added parser golden cases for:
  - `us-code-15-8563-3b998304c368f8a4` (`15 U.S.C. 8563`, `§8563. Renumbered.`)
  - `us-code-2-74b-55df9e8ab40ae3a5` (`2 U.S.C. 74b`, `§74b. Terminated.`)
  - `us-code-42-11924.-096a2b2493c6c5cf` (`42 U.S.C. 11924.`, `§11924. Vacant.`)
  in [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000011-20260518_075352/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py#L197).
- Added equivalent spaCy compiler golden cases in [test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000011-20260518_075352/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py#L95).
- Added deterministic modal compiler (regex backend) golden cases in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000011-20260518_075352/tests/unit_tests/logic/modal/test_modal_codec.py#L266).

**Validation**
- Ran focused runtime verification script covering parser fallback, spaCy fallback compiler, and `DeterministicModalCompiler(parser_backend="regex")` for all three new cases: passed (`verified_new_editorial_status_cases=ok`).
- Attempted narrow `pytest` execution, but test collection fails in this worktree due a pre-existing root `__init__.py` `__path__` error unrelated to this patch.