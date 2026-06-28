Implemented a focused IR/decompiler slot refinement for U.S.C. citations so mixed section IDs are represented compositionally, not just as one opaque `citation_section` string.

### What changed
- Added structured citation section slots in decompiler output:
  - `citation_section_primary`
  - `citation_section_component_count`
  - `citation_section_component`
  - `citation_section_number`
  - `citation_section_suffix`
- Kept existing slots unchanged (`citation_title`, `citation_code`, `citation_section`) for backward compatibility.
- Mirrored the same structure in F-logic triples so feature extraction gets the same typed signal.
- Added de-duplication preserving deterministic order for the new slot/triple emissions.

### Files
- [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000012-20260518_082114/ipfs_datasets_py/logic/modal/decompiler.py:754)
- [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000012-20260518_082114/ipfs_datasets_py/logic/modal/codec.py:885)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000012-20260518_082114/tests/unit_tests/logic/modal/test_modal_codec.py:1680)

### Validation
Ran targeted tests:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "citation_slots or alphanumeric_citation_section_slots"` → 2 passed
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "condition_exception_and_citation_slots or alphanumeric_citation_section_slots or autoencoder_feature_codec_protocol"` → 3 passed