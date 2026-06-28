Implemented a deterministic frame-logic audit expansion so slot-derived frame features are now audited as ontology terms.

### Changes
- Updated [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000026-20260518_101148/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:158) and [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000026-20260518_101148/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:584):
  - Added slot-frame predicate detection for `slot:selected_frame*` and `slot:frame_candidate*`.
  - Extended `_frame_ontology_value_from_feature` to treat these slot predicates as frame-ontology signals.
  - Numeric-only count/rank noise remains filtered by existing normalization.

- Added tests in [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000026-20260518_101148/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:385) and [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000026-20260518_101148/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:623):
  - Verifies term extraction from `slot:selected_frame_stem`, `slot:selected_frame_token`, and `slot:frame_candidate_ranked`.
  - Verifies `is_frame_ontology_feature_key` recognizes these new slot-derived frame signals.

### Tests run
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py` → 33 passed
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py tests/unit/logic/test_flogic_integration.py -k "frame_ontology or frame_terms"` → 7 passed
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "frame_ontology or frame_terms or audits_frame_terms or frame_decoder_audit_features"` → 5 passed
- `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py` → 7 passed