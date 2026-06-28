Implemented a deterministic frame-ontology audit improvement that keeps legally meaningful numeric terms (like section numbers) when they come from citation/source-id/statutory-scope predicates, while still filtering generic numeric noise.

- Updated contextual predicate coverage and numeric-term handling in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000019-20260518_091328/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:73).
- Added `keep_numeric_tokens` support in normalization and predicate-aware extraction from both triples and feature keys in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000019-20260518_091328/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:304).
- Added focused regression tests in [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000019-20260518_091328/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:1).

Validation run:

- `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py`
- Result: `3 passed`