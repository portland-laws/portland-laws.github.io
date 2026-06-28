Implemented a generalized statutory-scope slot refinement for the IR decompiler path.

- Expanded statutory reference parsing in [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000009-20260518_075235/ipfs_datasets_py/logic/modal/decompiler.py#L51) and [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000009-20260518_075235/ipfs_datasets_py/logic/modal/codec.py#L105):
  - Added connectors `within` and `in`
  - Added broader unit coverage (`part`, `subchapter`, `clause`, `subclause`, etc., with plural handling)
  - Added determiner support (`this`, `such`)
  - Preserved Roman numeral targets for determiner references
  - Canonicalized plural unit slot values to singular (`sections` -> `section`) while keeping surface text in `statutory_scope_reference`
- Added a focused regression test in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000009-20260518_075235/tests/unit_tests/logic/modal/test_modal_codec.py#L1765) for expanded connectors/units/targets and triple emission.

Validation run:
- `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py -k "statutory_scope"` fails due pre-existing repo setup issue in [__init__.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000009-20260518_075235/__init__.py#L11): `NameError: __path__ is not defined`.
- Fallback direct assertion script against the same modal APIs passed (`ok`).
- `python3 -m py_compile` passed for changed files.