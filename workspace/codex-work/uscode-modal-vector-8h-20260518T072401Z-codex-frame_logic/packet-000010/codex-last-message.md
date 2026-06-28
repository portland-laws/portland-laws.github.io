Implemented a deterministic frame-term audit improvement across frame selection, codec, and F-logic metadata.

**What changed**
- Added reusable frame-term audit extractors from triples and feature keys in [frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py#L35):
  - `frame_ontology_terms_from_triples(...)`
  - `frame_ontology_terms_from_feature_keys(...)`
- Updated F-logic optimizer to use the shared triple-based frame-term audit path (now includes frame predicates like `selected_ontology_frame`), in [flogic_optimizer.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/ipfs_datasets_py/optimizers/logic/flogic_optimizer.py#L186).
- Updated codec to:
  - record `frame_ontology_term_audit_count` and `frame_ontology_term_audit_terms` in IR metadata,
  - build audit terms from both frame-linked feature keys and emitted triples,
  - make `_frame_ontology_terms_by_frame` robust when metadata is partial (fills missing frame entries from deterministic fallback),
  in [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/ipfs_datasets_py/logic/modal/codec.py#L275) and [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/ipfs_datasets_py/logic/modal/codec.py#L1021).

**Tests added/updated**
- [test_frame_bm25_selector.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/tests/unit/optimizers/logic_theorem_optimizer/test_frame_bm25_selector.py#L119)
- [test_flogic_integration.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/tests/unit/logic/test_flogic_integration.py#L460)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000010-20260518_075932/tests/unit_tests/logic/modal/test_modal_codec.py#L1863)

**Verification run**
- `pytest` targeted run attempted, but blocked by pre-existing repo bootstrap issue: root `__init__.py` raises `NameError: __path__ is not defined` during test setup.
- Successfully ran:
  - `python3 -m py_compile` on all changed source/test files.
  - A direct `python3` smoke script covering:
    - new frame-term extractor behavior,
    - F-logic metadata term extraction from frame predicates,
    - partial metadata fallback path in `modal_ir_to_flogic_triples`.
