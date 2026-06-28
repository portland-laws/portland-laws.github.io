Implemented a narrow `compiler_registry` policy refinement: dynamic self-family ambiguity is now explicitly covered.

- Added `("dynamic", "dynamic")` to compiler-required adaptive family pairs in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000274-20260519_165114/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:83).  
  This propagates through existing target-order/signal-free logic and allows explicit adaptive low-margin self-pair handling for dynamic family.

- Added regression coverage in [test_legal_modal_parser_deterministic_rules.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000274-20260519_165114/ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py:978) with `test_compiler_marks_dynamic_self_pair_as_compiler_required_policy`.

Validation run:

- `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py -k "dynamic_self_pair_as_compiler_required_policy or deontic_self_pair_for_low_family_margin"`  
  Result: `2 passed, 33 deselected`
- `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py`  
  Result: `35 passed`