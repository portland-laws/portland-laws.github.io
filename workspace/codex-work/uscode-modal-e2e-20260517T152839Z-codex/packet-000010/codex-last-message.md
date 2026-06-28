Implemented a narrow deterministic ambiguity-policy improvement by expanding lexical scope detection for modal family disambiguation.

Changed:
- [spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000010-20260517_162852/ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py#L32)
  - Added conditional-scope phrase signals (`in the case of`, `except to the extent`, etc.).
  - Expanded temporal-scope phrase signals (`for any fiscal year`, `period beginning on`, etc.).
  - Added calendar-date detection regex.
  - Updated `has_condition_or_exception_scope`/`has_temporal_scope` to incorporate these deterministic signals.
- [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000010-20260517_162852/tests/unit_tests/logic/modal/test_modal_codec.py#L291)
  - Added regression test for temporal-vs-conditional ambiguity triggered by `in the case of`.
  - Added regression test for deontic-vs-temporal ambiguity triggered by `period beginning ... January 1, 2030 ...`.

Validation run:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "..."`
  - Blocked by existing repo issue: `__init__.py:11 NameError: __path__ is not defined`.
- Ran targeted Python assertion scripts instead; both passed (`ok`) for:
  - New conditional-scope ambiguity case.
  - New temporal-scope/calendar-date ambiguity case.
  - Existing baseline ambiguity signals (not-later-than, before-scope).