Implemented a narrow `compiler_ambiguity` hardening in the compiled-primary adaptive path.

- Updated compiled-primary ambiguity evaluation to canonicalize family tokens before margin math, pair checks, and metadata emission in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000565-20260519_161559/ipfs_datasets_py/logic/modal/compiler.py#L1344) and [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000565-20260519_161559/ipfs_datasets_py/logic/modal/compiler.py#L1590).
- This prevents spurious explicit ambiguities (or missed ones) when inputs use mixed tokens like `DEONTIC`, `TEMPORAL`, or `ModalLogicFamily.FRAME` instead of canonical lowercase family ids.
- Added regression coverage for this case in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000565-20260519_161559/tests/unit_tests/logic/modal/test_modal_codec.py#L8091).

Validation run:

1. `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "canonicalizes_compiled_primary_family_shares_for_policy_margin_filtering or canonicalizes_frame_family_tokens_for_priority_policy_margins or emits_explicit_ambiguity_for_todo_evidence_margin_pairs or marks_todo_policy_pairs_as_compiler_ambiguity_bundle"`  
   Result: `4 passed`.
2. `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py -k "compiler_ambiguity or compiled_primary_family or alethic_to_deontic or frame_to_temporal or temporal_to_deontic or deontic_self or temporal_self"`  
   Result: `6 passed`.
3. `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_modal_registry.py -k "compiler_ambiguity_policy_targets_are_ordered_and_directional or signal_free_adaptive_ambiguity_targets_are_ordered_and_directional or priority_signal_free_policy_covers_recurrent_compiler_ambiguity_pairs"`  
   Result: `3 passed`.