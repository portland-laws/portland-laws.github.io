Implemented a narrow ambiguity-policy improvement for temporal-vs-deontic conflicts.

**Edits**
- Expanded deterministic deontic scope signals so heading-style normative text (without explicit deontic cue terms) is still treated as deontic evidence in ambiguity detection:
  - Added tokens like `prohibition`, `prohibitions`, `requirement`, `requirements`, `liabilities`.
  - Added phrases like `prohibition on`, `prohibition of`, `requirements for`, `requirement that`, `liability for`.
  - File: [spacy_modal_codec.py:200](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000008-20260518_055554/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py:200)

- Added a focused regression test asserting explicit adaptive ambiguity is surfaced for temporal text with deontic heading semantics:
  - Checks `adaptive_family_margin_low` for `["temporal","deontic"]`
  - Checks explicit type `adaptive_temporal_deontic_outvoted_margin_low`
  - File: [test_modal_codec.py:905](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000008-20260518_055554/tests/unit_tests/logic/modal/test_modal_codec.py:905)

**Validation**
- Ran:
  - `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "prohibition_heading_as_adaptive_deontic_signal or deontic_scope_phrase_as_ambiguity_signal"`
- Result:
  - Blocked by existing repo setup issue before test execution: `NameError: name '__path__' is not defined` in top-level `__init__.py`.
- Verified behavior directly with runtime check:
  - For `"Within 30 days after review, prohibition on denial of access applies."`, compiler now emits temporal→deontic adaptive ambiguity with:
    - `target_share = 0.0`
    - `has_deontic_scope = True`
    - explicit ambiguity type present (`adaptive_temporal_deontic_outvoted_margin_low`).