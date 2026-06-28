Implemented a focused `ir_decompiler` refinement: deterministic statutory-scope slot extraction and triple projection for phrases like `under this section`, `pursuant to subsection (b)`, and `as provided in paragraph (1)`.

**Changes**
- Added statutory-scope phrase parsing and slot emission in decompiler phrase decoding, with deduped provenance-only slots:
  - `statutory_scope_reference`
  - `statutory_scope_connector`
  - `statutory_scope_unit`
  - `statutory_scope_target`
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/ipfs_datasets_py/logic/modal/decompiler.py:51)
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/ipfs_datasets_py/logic/modal/decompiler.py:205)
  - [decompiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/ipfs_datasets_py/logic/modal/decompiler.py:618)

- Added corresponding F-logic triple extraction from predicate text, typed argument values, and condition/exception clauses:
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/ipfs_datasets_py/logic/modal/codec.py:103)
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/ipfs_datasets_py/logic/modal/codec.py:577)
  - [codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/ipfs_datasets_py/logic/modal/codec.py:880)

- Added a unit test covering both decompiler slots and triples for statutory references:
  - [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213/tests/unit_tests/logic/modal/test_modal_codec.py:1642)

**Validation**
- Ran targeted tests (with `--rootdir=tests` to avoid repo-root import-mode noise):
  - `pytest -q tests/unit_tests/logic/modal/test_modal_codec.py --rootdir=tests -k "decompiler_recovers_condition_exception_and_citation_slots or triples_and_decompiler_slots_include_typed_predicate_arguments or decompiler_and_triples_include_statutory_scope_reference_slots"`
  - Result: `3 passed, 45 deselected`