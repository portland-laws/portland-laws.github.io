# packet-000021

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000021/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000021/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000021-20260518_093102

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-89542492e7f10083` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-89542492e7f10083` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-1804de105b905d35", "priority": 0.637180749754, "sample_id": "us-code-15-8563-3b998304c368f8a4"}`
  evidence: `{"hint_id": "modal-synthesis-5fd86fae59bd63dc", "priority": 0.584563515822, "sample_id": "us-code-15-1693l-62b207bc138a3216"}`
  evidence: `{"hint_id": "modal-synthesis-b3e5877e0ce817a0", "priority": 0.572915792228, "sample_id": "us-code-29-1169-02398831eb6558ee"}`
  evidence: `{"hint_id": "modal-synthesis-d12ee51318bcda7c", "priority": 0.553519723823, "sample_id": "us-code-16-6410-7cc9d1ff88340f35"}`
- `program-85d8a69588d98e82` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-89542492e7f10083` score `0.993824`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-3c9a9d0690c81b0a", "priority": 0.388228935042, "sample_id": "us-code-22-286b-1-c03d45d89ce69337"}`
  evidence: `{"hint_id": "modal-synthesis-7ae700a5716e282d", "priority": 0.513439327901, "sample_id": "us-code-42-7138.-c336418057a65c1d"}`
  evidence: `{"hint_id": "modal-synthesis-a5f59d60effe2bc0", "priority": 0.2567555523, "sample_id": "us-code-49-329.-930183d98235e137"}`
  evidence: `{"hint_id": "modal-synthesis-ed3d01be749309fe", "priority": 0.326941559086, "sample_id": "us-code-22-183-9272d613cfbb0f5f"}`
- `program-53038e08d87ce1cb` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-89542492e7f10083` score `0.993753`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-3163e80ebbbdddd7", "priority": 0.607915110566, "sample_id": "us-code-46-56101.-388a7506dd3d0a7e"}`
  evidence: `{"hint_id": "modal-synthesis-893ea8d3def5c4a4", "priority": 0.550273026999, "sample_id": "us-code-22-1465cc-9465fda281180311"}`
  evidence: `{"hint_id": "modal-synthesis-92b664831e5e24cc", "priority": 0.274537405818, "sample_id": "us-code-15-9413-f5a8f52590d9aeca"}`
  evidence: `{"hint_id": "modal-synthesis-fa9103b203fc2704", "priority": 0.499713182211, "sample_id": "us-code-16-80a-2b97b2cf01190662"}`

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
- TODO count: `3`

## TODOs
- `program-89542492e7f10083`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-89542492e7f10083` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.587044945407`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-15-8563-3b998304c368f8a4, us-code-15-1693l-62b207bc138a3216, us-code-29-1169-02398831eb6558ee, us-code-16-6410-7cc9d1ff88340f35`
  evidence: `{"hint_id": "modal-synthesis-1804de105b905d35", "priority": 0.637180749754, "sample_id": "us-code-15-8563-3b998304c368f8a4"}`
  evidence: `{"hint_id": "modal-synthesis-5fd86fae59bd63dc", "priority": 0.584563515822, "sample_id": "us-code-15-1693l-62b207bc138a3216"}`
  evidence: `{"hint_id": "modal-synthesis-b3e5877e0ce817a0", "priority": 0.572915792228, "sample_id": "us-code-29-1169-02398831eb6558ee"}`
  evidence: `{"hint_id": "modal-synthesis-d12ee51318bcda7c", "priority": 0.553519723823, "sample_id": "us-code-16-6410-7cc9d1ff88340f35"}`
- `program-85d8a69588d98e82`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-89542492e7f10083` score `0.993824`
  loss: `autoencoder_residual_cluster` = `0.371341343582`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-7138.-c336418057a65c1d, us-code-22-286b-1-c03d45d89ce69337, us-code-22-183-9272d613cfbb0f5f, us-code-49-329.-930183d98235e137`
  evidence: `{"hint_id": "modal-synthesis-3c9a9d0690c81b0a", "priority": 0.388228935042, "sample_id": "us-code-22-286b-1-c03d45d89ce69337"}`
  evidence: `{"hint_id": "modal-synthesis-7ae700a5716e282d", "priority": 0.513439327901, "sample_id": "us-code-42-7138.-c336418057a65c1d"}`
  evidence: `{"hint_id": "modal-synthesis-a5f59d60effe2bc0", "priority": 0.2567555523, "sample_id": "us-code-49-329.-930183d98235e137"}`
  evidence: `{"hint_id": "modal-synthesis-ed3d01be749309fe", "priority": 0.326941559086, "sample_id": "us-code-22-183-9272d613cfbb0f5f"}`
- `program-53038e08d87ce1cb`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-89542492e7f10083` score `0.993753`
  loss: `autoencoder_residual_cluster` = `0.483109681399`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-46-56101.-388a7506dd3d0a7e, us-code-22-1465cc-9465fda281180311, us-code-16-80a-2b97b2cf01190662, us-code-15-9413-f5a8f52590d9aeca`
  evidence: `{"hint_id": "modal-synthesis-3163e80ebbbdddd7", "priority": 0.607915110566, "sample_id": "us-code-46-56101.-388a7506dd3d0a7e"}`
  evidence: `{"hint_id": "modal-synthesis-893ea8d3def5c4a4", "priority": 0.550273026999, "sample_id": "us-code-22-1465cc-9465fda281180311"}`
  evidence: `{"hint_id": "modal-synthesis-92b664831e5e24cc", "priority": 0.274537405818, "sample_id": "us-code-15-9413-f5a8f52590d9aeca"}`
  evidence: `{"hint_id": "modal-synthesis-fa9103b203fc2704", "priority": 0.499713182211, "sample_id": "us-code-16-80a-2b97b2cf01190662"}`
