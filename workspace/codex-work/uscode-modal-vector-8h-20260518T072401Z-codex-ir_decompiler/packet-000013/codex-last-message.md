Implemented a deterministic typed-slot refinement for `modal.ir_decompiler` focused on underrepresented fallback metadata.

**What changed**
1. Added tokenized sub-slots in decompiler output for `fallback_rule`, `status_keyword`, and `statement_hint`:
   - `*_token_count`
   - `*_token_prefix`
   - `*_token_suffix`
   - repeated `*_token`
   - `*_version` (when suffix matches `v\d+`)
   - `*_stem`
   - File: [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000013-20260518_082742/ipfs_datasets_py/logic/modal/decompiler.py)

2. Mirrored the same decomposition into F-logic triples so graph projection and slot decoding stay aligned.
   - File: [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000013-20260518_082742/ipfs_datasets_py/logic/modal/codec.py)

3. Extended unit coverage for editorial fallback and declarative statement cases to assert these new slots/triples.
   - File: [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000013-20260518_082742/tests/unit_tests/logic/modal/test_modal_codec.py)

**Validation run**
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "editorial_fallback_slots or declarative_statement_hint_slot"` → `2 passed`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "recovers_condition_exception_and_citation_slots or expand_alphanumeric_citation_section_slots or include_statutory_scope_reference_slots or surface_editorial_fallback_slots or supports_autoencoder_feature_codec_protocol"` → `5 passed`