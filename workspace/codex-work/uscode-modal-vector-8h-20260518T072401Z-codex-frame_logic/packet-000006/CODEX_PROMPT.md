# packet-000006

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000006/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000006/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000006-20260518_072441

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-0568fbd8d7aefa98` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0568fbd8d7aefa98` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-2c2e46a5ce157413", "priority": 0.332670299865, "sample_id": "us-code-28-715-17e4d69b8bcf8ca0"}`
  evidence: `{"hint_id": "modal-synthesis-8967bb0352ecca58", "priority": 0.481679767704, "sample_id": "us-code-16-4262-d3b48644065ce57a"}`
  evidence: `{"hint_id": "modal-synthesis-960cf39b61588b6c", "priority": 0.927671002099, "sample_id": "us-code-41-1908-0e08f1fa2d71abfc"}`
  evidence: `{"hint_id": "modal-synthesis-d06f2f1e5f043bb6", "priority": 0.274639597408, "sample_id": "us-code-32-314-6744cb7ec9549d48"}`
- `program-0a0d9c29289c1be1` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0568fbd8d7aefa98` score `0.989723`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-3ccc9fe893560d75", "priority": 0.314326984364, "sample_id": "us-code-10-8588-eb039524912bce7b"}`
  evidence: `{"hint_id": "modal-synthesis-50e9f475ef5d5d24", "priority": 0.311751356897, "sample_id": "us-code-15-649-2196edd5586b40df"}`
  evidence: `{"hint_id": "modal-synthesis-917322bd944b67d6", "priority": 0.619429136569, "sample_id": "us-code-29-1863-caa9fbb898b49ba9"}`
  evidence: `{"hint_id": "modal-synthesis-c4726797aa08e6da", "priority": 0.317243178444, "sample_id": "us-code-42-300mm.-80233d6bb1a7d5e4"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Treat the packet's program_synthesis_scope metadata as the AST/write-scope boundary; keep edits inside that lane unless a test requires a small adjacent change.
When multiple TODOs are present, treat their semantic_bundle_key or vector_bundle metadata as evidence for one generalized compiler/decompiler/frame improvement over one-off sample fixes.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-0568fbd8d7aefa98`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0568fbd8d7aefa98` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.504165166769`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-41-1908-0e08f1fa2d71abfc, us-code-16-4262-d3b48644065ce57a, us-code-28-715-17e4d69b8bcf8ca0, us-code-32-314-6744cb7ec9549d48`
  evidence: `{"hint_id": "modal-synthesis-2c2e46a5ce157413", "priority": 0.332670299865, "sample_id": "us-code-28-715-17e4d69b8bcf8ca0"}`
  evidence: `{"hint_id": "modal-synthesis-8967bb0352ecca58", "priority": 0.481679767704, "sample_id": "us-code-16-4262-d3b48644065ce57a"}`
  evidence: `{"hint_id": "modal-synthesis-960cf39b61588b6c", "priority": 0.927671002099, "sample_id": "us-code-41-1908-0e08f1fa2d71abfc"}`
  evidence: `{"hint_id": "modal-synthesis-d06f2f1e5f043bb6", "priority": 0.274639597408, "sample_id": "us-code-32-314-6744cb7ec9549d48"}`
- `program-0a0d9c29289c1be1`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0568fbd8d7aefa98` score `0.989723`
  loss: `autoencoder_residual_cluster` = `0.390687664068`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-29-1863-caa9fbb898b49ba9, us-code-42-300mm.-80233d6bb1a7d5e4, us-code-10-8588-eb039524912bce7b, us-code-15-649-2196edd5586b40df`
  evidence: `{"hint_id": "modal-synthesis-3ccc9fe893560d75", "priority": 0.314326984364, "sample_id": "us-code-10-8588-eb039524912bce7b"}`
  evidence: `{"hint_id": "modal-synthesis-50e9f475ef5d5d24", "priority": 0.311751356897, "sample_id": "us-code-15-649-2196edd5586b40df"}`
  evidence: `{"hint_id": "modal-synthesis-917322bd944b67d6", "priority": 0.619429136569, "sample_id": "us-code-29-1863-caa9fbb898b49ba9"}`
  evidence: `{"hint_id": "modal-synthesis-c4726797aa08e6da", "priority": 0.317243178444, "sample_id": "us-code-42-300mm.-80233d6bb1a7d5e4"}`
