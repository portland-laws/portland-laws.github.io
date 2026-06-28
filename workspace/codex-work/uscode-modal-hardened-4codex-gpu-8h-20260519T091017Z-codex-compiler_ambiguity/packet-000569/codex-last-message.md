Implemented the compiler ambiguity policy hardening for this packet by promoting `alethic -> frame` to required/priority adaptive handling and adding regression coverage.

**Changes**
- Added `alethic -> frame` to required adaptive ambiguity pairs in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000569-20260519_164522/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:52).
- Added `alethic -> frame` to priority signal-free adaptive ambiguity pairs in [modal_registry.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000569-20260519_164522/ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py:452).
- Expanded regression expectations to include `alethic->frame` recurrent policy coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000569-20260519_164522/tests/unit_tests/logic/modal/test_modal_codec.py:3076).
- Added a new zero-margin regression asserting `alethic->frame` resolves to explicit `outvoted` ambiguity (priority + required) in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000569-20260519_164522/tests/unit_tests/logic/modal/test_modal_codec.py:9438).
- Added `required-alethic-frame-margin-doc` scenario to required-bundle evidence tests in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000569-20260519_164522/tests/unit_tests/logic/modal/test_modal_codec.py:13602).

**Tests run**
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "recurrent_policy_pairs or zero_margin_alethic_frame or required_margin_bundle_pairs"`
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "alethic_frame or deontic_epistemic or frame_conditional or deontic_temporal or deontic_conditional"`
- `pytest -q ipfs_datasets_py/optimizers/logic_theorem_optimizer/test_legal_modal_parser_deterministic_rules.py -k "frame_to_conditional or deontic_to_conditional or deontic_to_frame_and_temporal or alethic_to"`

All passed.