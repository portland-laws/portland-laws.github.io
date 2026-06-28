Implemented a deterministic frame-logic audit normalization fix for citation/source-id range connectors so frame-linked range signals are retained as ontology terms.

### What changed
- Added canonical range-connector aliases (`to`, `thru`, `through` → `through`) in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000040-20260518_122702/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py#L129).
- Applied this normalization for predicates ending in `_range_connector` inside `_normalized_frame_ontology_value(...)` in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000040-20260518_122702/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py#L628).
- Added helper `_normalized_range_connector_ontology_value(...)` in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000040-20260518_122702/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py#L671).

### Tests added
- New selector-level coverage for triple + feature-key normalization in [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000040-20260518_122702/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py#L137).
- New optimizer-level metadata assertion in [test_flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000040-20260518_122702/tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py#L247).

### Validation run
- `IPFS_DATASETS_PY_MINIMAL_IMPORTS=1 pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py -k "range_connector or frame_ontology or source_id_citation"` → **12 passed**
- `IPFS_DATASETS_PY_MINIMAL_IMPORTS=1 pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "frame_ontology or frame_decoder_audit or source_id_citation or modal_family_count"` → **5 passed**