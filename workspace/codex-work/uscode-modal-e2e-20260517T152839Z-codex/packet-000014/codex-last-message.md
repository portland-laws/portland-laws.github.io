Added the requested golden parser regression for the zero-formula sample ID `us-code-10-7082-9e036c2a899ad874` in [test_legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000014-20260517_165741/tests/unit/optimizers/logic_theorem_optimizer/test_legal_modal_parser.py#L123).

What the new test asserts:
- Parses `§7082. Transferred.` with `citation="10 U.S.C. 7082"`.
- Confirms formulas are produced via deterministic fallback.
- Confirms fallback metadata:
  - `cue == "__uscode_codification_fallback__"`
  - `fallback_rule == "uscode_transferred_heading_v1"`
  - provenance citation preserved.

Validation run:
- `pytest ...test_legal_modal_parser.py -k '10_7082'` failed due a pre-existing repo import issue in root `__init__.py` (`NameError: __path__ is not defined` during package setup).
- Ran a direct `python3` assertion script against `LegalModalParser.parse(...)` for this case; it passed (`manual parser check passed`).