Implemented a narrow ambiguity-policy expansion so temporal-heavy clauses now surface explicit conditional-normative ambiguity when they use scoped phrasing like `with respect to`.

- Added `"with respect to"` to conditional scope phrase signals in [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000007-20260518_055036/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:32).
- Added regression coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000007-20260518_055036/tests/unit_tests/logic/modal/test_modal_codec.py:655) (`test_modal_compiler_treats_with_respect_to_as_conditional_scope_ambiguity_signal`).

Validation run:
- `pytest` slice attempted, but blocked by a pre-existing repo bootstrap issue: `__init__.py:11 NameError: __path__ is not defined`.
- Direct runtime check passed via `python3` assertion snippet; it produced `temporal_conditional_normative_family_outvoted` with `target_share == 0.0` and `has_conditional_scope_phrase == True`.