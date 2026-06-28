Implemented a narrow frame-logic audit fix: single-digit numeric suffix tokens are now preserved when numeric ontology tokens are explicitly allowed (e.g., citation/source-id fields), so `78u-3` and `410r-1` are retained as `78u_3` and `410r_1`.

Updated files:
- [_is_informative_ontology_token` numeric-token ordering]( /home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000022-20260518_093846/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py#L430 )
- [Regression tests for triple + feature-key extraction of single-digit suffixes]( /home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000022-20260518_093846/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py#L46 )

Validation run:
- `python3 -m pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py`
- Result: `5 passed`