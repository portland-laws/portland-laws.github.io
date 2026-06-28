Implemented a focused frame-logic audit improvement: selected-frame modal family signals are now emitted as explicit frame-linked features (`family:selected_frame:<family>`) and included in ontology term auditing.

**Changes**
- Added selected-frame modal family feature emission in sample feature extraction and audit feature key generation in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000051-20260518_141144/ipfs_datasets_py/logic/modal/codec.py#L600), [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000051-20260518_141144/ipfs_datasets_py/logic/modal/codec.py#L3058).
- Added helper to deterministically derive modal families for selected-frame auditing from formulas plus `modal_family_counts` metadata in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000051-20260518_141144/ipfs_datasets_py/logic/modal/codec.py#L3112).

**Tests**
- Updated/asserted codec feature-key protocol includes selected-frame family features in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000051-20260518_141144/tests/unit_tests/logic/modal/test_modal_codec.py#L4004).
- Added new coverage for frame-audit metadata tracking selected-frame modal families in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000051-20260518_141144/tests/unit_tests/logic/modal/test_modal_codec.py#L4492).

Executed:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "supports_autoencoder_feature_codec_protocol or frame_ontology_audit_tracks_selected_frame_modal_families"` (passed)
- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_flogic_optimizer.py -k "tracks_selected_frame_family_terms"` (passed)
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "frame_ontology_audit_tracks"` (passed)