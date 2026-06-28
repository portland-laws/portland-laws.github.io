Implemented a targeted frame-logic audit improvement by making synthesis hint extraction use the canonical frame feature parser.

- Updated [`synthesis.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000046-20260518_133133/ipfs_datasets_py/logic/modal/synthesis.py):190 to derive `audit_frame_logic_terms` evidence from `frame_ontology_feature_keys(...)` instead of a narrow prefix check.  
  This now captures frame-linked variants like `selected-frame-term:*`, `slot:selected_frame:*`, `family:selected_frame:*`, `cue:frame:*`, etc.
- Added regression coverage in [`test_modal_codec.py`](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000046-20260518_133133/tests/unit_tests/logic/modal/test_modal_codec.py):4441 to verify those variants are preserved in `audit_frame_logic_terms` hint evidence.

Tests run:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "autoencoder_synthesis_hint_extracts_frame_linked_feature_variants or autoencoder_introspection_guides_typed_synthesis_hints"` → 2 passed
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py` → 65 passed