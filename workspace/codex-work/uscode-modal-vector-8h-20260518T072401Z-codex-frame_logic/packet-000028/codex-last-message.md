Implemented a deterministic frame-ontology audit fix for `modal_family_count*` signals so frame-linked family-count features are no longer dropped from ontology-term auditing.

- Updated predicate recognition and value normalization in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000028-20260518_102425/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:83) and [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000028-20260518_102425/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:521):
  - `modal_family_count*` predicates are now treated as contextual frame-ontology signals.
  - Added deterministic parsing for:
    - `modal_family_count:family:count`
    - `modal_family_count_ranked:rank:family:count`
    - `modal_family_count_family:family`
    - `modal_family_count_<family>:count`
  - `modal_family_count_value:<count>` intentionally yields no ontology term.

Added/updated tests:
- [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000028-20260518_102425/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:440)
- [test_flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000028-20260518_102425/tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py:148)
- [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000028-20260518_102425/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:94)

Validation run:
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py` → `49 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k 'emits_frame_ontology_term_triples or audits_frame_terms_when_metadata_is_partial or audits_frame_terms_when_metadata_contains_weight_maps or frame_decoder_audit_features_use_canonical_feature_parser'` → `4 passed`