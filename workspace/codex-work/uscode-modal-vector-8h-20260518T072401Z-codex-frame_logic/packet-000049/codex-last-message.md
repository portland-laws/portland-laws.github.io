Implemented a focused frame-logic term-audit fix and regression coverage.

1. Updated metadata key handling to treat `matched_term` / `matched_terms` as value-bearing term keys, preventing key-name noise in audited ontology terms.  
[codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000049-20260518_135829/ipfs_datasets_py/logic/modal/codec.py#L217)

2. Updated `_frame_ontology_metadata_terms` to canonicalize slot-normalized source IDs (for example `us_code_54_101920_<digest>`) through the existing frame-feature parser, so audits keep deterministic `title_section` terms and drop digest-heavy noise.  
[codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000049-20260518_135829/ipfs_datasets_py/logic/modal/codec.py#L2801)

3. Added regression tests for:
- slot-normalized source IDs in frame-term metadata
- `matched_terms` metadata maps not leaking `"matched_terms"` as an ontology term  
[test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000049-20260518_135829/tests/unit_tests/logic/modal/test_modal_codec.py#L4209)

Validation run:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "slot_normalized_source_ids_from_frame_term_metadata or matched_terms_metadata_without_key_noise"` (2 passed)
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py` (95 passed)
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py` (56 passed)