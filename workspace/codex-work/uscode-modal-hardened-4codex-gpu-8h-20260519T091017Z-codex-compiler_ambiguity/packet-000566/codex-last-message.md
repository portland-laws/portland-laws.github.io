Implemented the compiler ambiguity hardening for packet `000566` and added targeted regression coverage.

**Changes**
- Updated non-self adaptive ambiguity margin metadata to round from the raw computed margin (instead of subtracting rounded shares), preserving deterministic sign/precision in edge cases:
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000566-20260519_162452/ipfs_datasets_py/logic/modal/compiler.py#L947)
  - [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000566-20260519_162452/ipfs_datasets_py/logic/modal/compiler.py#L1469)
- Added packet-specific regression test for the three requested policy pairs (`deontic->deontic`, `frame->conditional_normative`, `frame->dynamic`) with the provided margins/priorities and explicit ambiguity typing checks:
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000566-20260519_162452/tests/unit_tests/logic/modal/test_modal_codec.py#L14505)
- Added a precision regression test to ensure non-self `family_margin` metadata is derived from rounded raw delta:
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000566-20260519_162452/tests/unit_tests/logic/modal/test_modal_codec.py#L14764)
- Updated one existing expectation to align with raw-margin rounding semantics:
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000566-20260519_162452/tests/unit_tests/logic/modal/test_modal_codec.py#L7414)

**Validation**
- Ran focused new tests:
  - `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "packet_000566 or rounds_non_self_family_margin_from_raw_delta"`
- Ran full module:
  - `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py`
- Result: `211 passed`.