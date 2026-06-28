Implemented a deterministic frame-audit unification so frame-linked scoring features are recognized through one canonical parser path.

- Added canonical feature-key helpers in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000017-20260518_085715/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:345): `is_frame_ontology_feature_key(...)` and `frame_ontology_feature_keys(...)`, and exported them.
- Switched codec decoder-audit feature extraction to use the canonical helper in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000017-20260518_085715/ipfs_datasets_py/logic/modal/codec.py:1353), removing hardcoded prefix drift.
- Updated optimizer metadata/audit flow in [flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000017-20260518_085715/ipfs_datasets_py/optimizers/logic/flogic_optimizer.py:192) to track filtered frame-audit keys separately (`frame_audit_feature_key_count`, `frame_audit_feature_keys`) while preserving existing `frame_feature_keys`.

Added/updated tests:

- [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000017-20260518_085715/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:344) for new helper behavior.
- [test_flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000017-20260518_085715/tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py:19) for new metadata fields.
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000017-20260518_085715/tests/unit_tests/logic/modal/test_modal_codec.py:2868) to verify codec audit extraction now follows canonical parsing.

Validation run:

- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py tests/unit_tests/logic/modal/test_modal_codec.py` → `90 passed`
- `pytest -q tests/unit/logic/test_flogic_integration.py` → `37 passed`