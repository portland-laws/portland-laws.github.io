Implemented a scoped `frame_logic` audit improvement to reduce ontology-term noise while keeping citation/source coordinates.

- Updated metadata-key handling in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000055-20260518_144737/ipfs_datasets_py/logic/modal/codec.py:246):
  - Added structural keys (`citation(s)`, `sample_id(s)`, `hint_id(s)`, `source_id(s)`) so those key names are not emitted as ontology terms.
  - Added opaque-ID detection for metadata values with long hex-like identifiers and filtered those out when they are not source/citation coordinates ([codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000055-20260518_144737/ipfs_datasets_py/logic/modal/codec.py:3399)).
  - Tightened key-name filtering to exclude `*_ids` and `*_keys` from term-like keys ([codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000055-20260518_144737/ipfs_datasets_py/logic/modal/codec.py:3381)).

- Added regression coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000055-20260518_144737/tests/unit_tests/logic/modal/test_modal_codec.py:4349):
  - Verifies citation/sample metadata still yields canonical terms (`43_641`, `42_295`, `21_619`).
  - Verifies structural key noise (`citations`, `sample_ids`, `hint_ids`) and opaque hint IDs are not emitted as selected ontology terms.

Tests run:

- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "matched_terms_metadata_without_key_noise or citation_and_sample_metadata_without_structural_key_noise or audits_frame_feature_keys_from_term_metadata"`  
  - 3 passed
- `pytest -q tests/unit/logic/test_flogic_integration.py -k "frame_ontology_terms"`  
  - 4 passed