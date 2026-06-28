Implemented a deterministic frame-logic audit improvement so structured evidence fields can be audited even when they are not already encoded as canonical feature keys.

**What changed**
- Added key-to-feature synthesis for semantic fields in nested evidence payloads:
  - `selected_frame` / `selected_ontology_frame` / `frame_id` → `frame:*`
  - `candidate_frame` / `candidate_ontology_frame` → `frame-candidate:*`
  - `selected_*_term` / `candidate_*_term` → `selected-frame-term:*` / `frame-term:*`
  - `predicted_family` / `target_family` / `modal_family` → `family:selected_frame:*`
- Wired this into nested value extraction used by frame ontology audits.

Code:
- [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000061-20260518_154038/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:254)
- [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000061-20260518_154038/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:628)
- [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000061-20260518_154038/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py:694)

**Tests added**
- New selector test for semantic-field synthesis in nested hint evidence:
  - [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000061-20260518_154038/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py:1436)
- New optimizer integration test confirming synthesized keys become ontology terms:
  - [test_flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000061-20260518_154038/tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py:538)

**Validation run**
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py` → `85 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "frame_ontology_audit or frame_feature_keys_from_term_metadata or structured_hint_evidence"` → `8 passed`