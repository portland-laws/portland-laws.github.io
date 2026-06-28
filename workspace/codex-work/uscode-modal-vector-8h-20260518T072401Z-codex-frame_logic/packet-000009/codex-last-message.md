Implemented a deterministic frame-term audit improvement across selector, codec, and F-logic metadata.

Changed files:
- [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py#L11)
- [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130/ipfs_datasets_py/logic/modal/codec.py#L909)
- [flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130/ipfs_datasets_py/optimizers/logic/flogic_optimizer.py#L186)
- [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py#L76)
- [test_flogic_integration.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130/tests/unit/logic/test_flogic_integration.py#L431)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130/tests/unit_tests/logic/modal/test_modal_codec.py#L1785)

What changed:
1. Added deterministic ontology-term normalization:
- Drops stopwords (`and`, `the`, etc.) and numeric-only tokens.
- Exposed as `normalize_frame_ontology_term(...)`.

2. Improved `frame_ontology_terms(...)` generation:
- Prioritizes BM25 `matched_terms` before lower-priority frame text.
- Keeps frame ID canonical term, but avoids expanding frame ID into extra token atoms.
- Preserves deterministic ordering and `max_terms` cap behavior.

3. Aligned codec and F-logic metadata with the same normalization:
- Codec frame-term extraction now normalizes metadata/fallback frame terms consistently.
- F-logic optimizer now normalizes/de-duplicates frame-term metadata from triples before counting/reporting.

4. Added tests for:
- stopword/numeric filtering,
- matched-term priority under cap,
- F-logic metadata normalization,
- codec triple/feature suppression of non-informative frame terms.

Validation:
- `pytest` runs were blocked by an existing environment/bootstrap issue: `NameError: __path__ is not defined` in top-level `__init__.py` during test setup.
- Syntax checks passed:
  - `python3 -m py_compile` on all edited source and test files.
- Manual functional sanity checks via `python3` confirmed expected normalized outputs (e.g. `["final_order"]`, no `and`/`the`).