Implemented a deterministic parser robustness fix plus regression fixtures for the three packet citations.

- Updated [legal_modal_parser.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000023-20260518_094715/ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py):
  - U.S.C. citation detection now accepts dotted and undotted forms (`U.S.C.` and `USC`) and optional section symbol (`§`).
  - All U.S.C. fallback gates now use the normalized citation detector instead of a strict `"u.s.c."` substring check.
  - This prevents zero-formula outcomes for heading-style legal text when citation formatting varies.

- Added spaCy-compiler regression fixture coverage in [test_spacy_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000023-20260518_094715/tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py):
  - New test covers `7 U.S.C. 473a`, `20 U.S.C. 1067j`, and `15 U.S.C. 2501` with citation variants like `USC` and `§`.

- Added compiler-level regression fixture coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000023-20260518_094715/tests/unit_tests/logic/modal/test_modal_codec.py):
  - Verifies both `regex` and `spacy` backends avoid `missing_modal_formula` on those sec-prefixed heading samples with citation variants.

Tests run:

- `pytest -q tests/unit/optimizers/logic_theorem_optimizer/test_spacy_modal_codec.py -k 'citation_variants_for_sec_headings or sec_prefixed_heading_zero_formula_sample_for_15_1693l or heading_zero_formula_cases_for_25_422_48_1572_and_42_6323'`  
  - Passed.
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k 'usc_citation_variants'`  
  - Passed.