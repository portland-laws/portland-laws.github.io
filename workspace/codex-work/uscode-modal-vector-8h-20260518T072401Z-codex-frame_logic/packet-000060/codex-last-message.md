Implemented a deterministic frame-term audit improvement for `frame_logic` by expanding how metadata evidence is parsed and harvested.

- Added structured-string parsing in frame feature extraction so serialized JSON payloads (for example `dedupe_signature`) are recursively unpacked before term/key filtering.  
  [frame_bm25_selector.py:656](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000060-20260518_153202/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:656)

- Expanded codec metadata audit inputs to include citation fields and feature-list fields (`feature*`, `frame_feature*`, `top_*_features`, `dedupe_signature`) from both document metadata and frame-logic metadata, so frame-linked evidence is more consistently audited into ontology terms.  
  [codec.py:3925](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000060-20260518_153202/ipfs_datasets_py/logic/modal/codec.py:3925)

- Added a regression test proving serialized JSON metadata values produce expected frame ontology keys/terms.  
  [test_frame_bm25_selector.py:299](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000060-20260518_153202/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:299)

Validation run:

- `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py` (18 passed)
- `python3 -m compileall -q ipfs_datasets_py/logic/modal/codec.py ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`