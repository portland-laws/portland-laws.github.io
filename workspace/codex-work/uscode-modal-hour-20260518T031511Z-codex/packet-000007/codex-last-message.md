Implemented a narrow deterministic ambiguity-policy improvement for `modal.compiler.ambiguity`:

- Added a new compiler ambiguity rule: `temporal_deontic_scope_family_outvoted`.
- It triggers when the top family is `temporal` or `deontic`, the opposite family has lexical/score evidence, and existing outvote thresholds indicate the opposite family is outvoted.
- It records explicit `predicted_family`, `target_family`, and `family_margin` metadata for review.

Updated files:
- [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000007-20260518_034150/ipfs_datasets_py/logic/modal/compiler.py:372)
- [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000007-20260518_034150/ipfs_datasets_py/logic/modal/compiler.py:798)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000007-20260518_034150/tests/unit_tests/logic/modal/test_modal_codec.py:568)
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000007-20260518_034150/tests/unit_tests/logic/modal/test_modal_codec.py:734)

Validation run:
- `pytest` (targeted) could not run due a pre-existing setup error: `NameError: __path__ is not defined` in repo-root `__init__.py`.
- Runtime spot-check via `python3` confirmed the new ambiguity type appears for both directions (`temporal -> deontic` and `deontic -> temporal`).
- `python3 -m py_compile` passed for edited files.