Implemented a narrow frame-logic audit fix: single-letter modal symbols from frame-linked features are now preserved as ontology terms instead of being dropped.

**Changes**
1. Updated [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000039-20260518_121739/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py) to allow single-character alpha tokens for:
- `modal_operator`
- `modal_system`

This fixes cases like `flogic:modal_operator:P`, `flogic:modal_operator:O|`, `flogic:modal_system:D`.

2. Added selector coverage in [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000039-20260518_121739/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py):
- `test_frame_ontology_terms_from_triples_keep_single_letter_modal_symbols`
- `test_frame_ontology_terms_from_feature_keys_keep_single_letter_modal_symbols`
- updated contextual expectation to include `"o"` from `modal_operator:O`.

3. Added optimizer metadata coverage in [test_flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000039-20260518_121739/tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py):
- `test_flogic_optimizer_tracks_single_letter_modal_symbol_terms`

**Validation run**
1. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py` → `50 passed`
2. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py` → `10 passed`
3. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "frame_ontology or frame_logic or frame-term"` → `6 passed`