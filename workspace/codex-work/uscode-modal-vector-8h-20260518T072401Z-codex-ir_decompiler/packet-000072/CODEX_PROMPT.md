# packet-000072

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000072/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000072/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000072-20260518_143011

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-becc7f64c45b9066` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-becc7f64c45b9066` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.130489447398, "hint_id": "modal-synthesis-5bb9c23ee4dd9cdc", "priority": 0.41480128469, "reconstruction_loss": 0.41480128469, "sample_id": "us-code-31-1106-bfadc9da78a1cccc"}`
  evidence: `{"cosine_similarity": -0.545166806628, "hint_id": "modal-synthesis-76d2f7134fd9df57", "priority": 0.81164360047, "reconstruction_loss": 0.81164360047, "sample_id": "us-code-22-10006-9bc8c2091200efcc"}`
  evidence: `{"cosine_similarity": -0.442942501629, "hint_id": "modal-synthesis-bd9b1d15d401a860", "priority": 0.747721683335, "reconstruction_loss": 0.747721683335, "sample_id": "us-code-12-5517-315b38c715df0675"}`
  evidence: `{"cosine_similarity": 0.128817343902, "hint_id": "modal-synthesis-c49b230c419c1761", "priority": 0.3834290849, "reconstruction_loss": 0.3834290849, "sample_id": "us-code-42-1789.-05a5c63e410f98ab"}`
- `program-e87c4cc900b89ac0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-becc7f64c45b9066` score `0.994752`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.35265428627, "hint_id": "modal-synthesis-076345e1888567a9", "priority": 0.431640532516, "reconstruction_loss": 0.431640532516, "sample_id": "us-code-16-47a-26c452e74b52db99"}`
  evidence: `{"cosine_similarity": 0.294378194805, "hint_id": "modal-synthesis-573d05649564bc1d", "priority": 0.345424598846, "reconstruction_loss": 0.345424598846, "sample_id": "us-code-8-1365b-a825991ce12b9ec4"}`
  evidence: `{"cosine_similarity": 0.402503493297, "hint_id": "modal-synthesis-a014361c3019f1eb", "priority": 0.34880263313, "reconstruction_loss": 0.34880263313, "sample_id": "us-code-7-450-759794f8a1f6176f"}`
  evidence: `{"cosine_similarity": -0.044104511491, "hint_id": "modal-synthesis-fcfc8ca4fabea001", "priority": 0.47110089938, "reconstruction_loss": 0.47110089938, "sample_id": "us-code-31-1121-71177e9ae735ce0b"}`
- `program-d53757061cde4039` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-becc7f64c45b9066` score `0.994529`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.537875562781, "hint_id": "modal-synthesis-00a6530477b468a9", "priority": 0.338191566023, "reconstruction_loss": 0.338191566023, "sample_id": "us-code-6-924-46b4e91da16607f0"}`
  evidence: `{"cosine_similarity": 0.75123959, "hint_id": "modal-synthesis-2db9a44451326ecc", "priority": 0.185624271959, "reconstruction_loss": 0.185624271959, "sample_id": "us-code-5-10-852d8ede8019f304"}`
  evidence: `{"cosine_similarity": 0.123435570296, "hint_id": "modal-synthesis-39c7d92d171be984", "priority": 0.545127968469, "reconstruction_loss": 0.545127968469, "sample_id": "us-code-34-10307-3d13e651f2feb776"}`
  evidence: `{"cosine_similarity": 0.42837431094, "hint_id": "modal-synthesis-d3089cbfd3578eac", "priority": 0.227856268506, "reconstruction_loss": 0.227856268506, "sample_id": "us-code-33-444-516a16b59ab41826"}`

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
- `program-becc7f64c45b9066`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-becc7f64c45b9066` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.589398913349`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-22-10006-9bc8c2091200efcc, us-code-12-5517-315b38c715df0675, us-code-31-1106-bfadc9da78a1cccc, us-code-42-1789.-05a5c63e410f98ab`
  evidence: `{"cosine_similarity": 0.130489447398, "hint_id": "modal-synthesis-5bb9c23ee4dd9cdc", "priority": 0.41480128469, "reconstruction_loss": 0.41480128469, "sample_id": "us-code-31-1106-bfadc9da78a1cccc"}`
  evidence: `{"cosine_similarity": -0.545166806628, "hint_id": "modal-synthesis-76d2f7134fd9df57", "priority": 0.81164360047, "reconstruction_loss": 0.81164360047, "sample_id": "us-code-22-10006-9bc8c2091200efcc"}`
  evidence: `{"cosine_similarity": -0.442942501629, "hint_id": "modal-synthesis-bd9b1d15d401a860", "priority": 0.747721683335, "reconstruction_loss": 0.747721683335, "sample_id": "us-code-12-5517-315b38c715df0675"}`
  evidence: `{"cosine_similarity": 0.128817343902, "hint_id": "modal-synthesis-c49b230c419c1761", "priority": 0.3834290849, "reconstruction_loss": 0.3834290849, "sample_id": "us-code-42-1789.-05a5c63e410f98ab"}`
- `program-e87c4cc900b89ac0`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-becc7f64c45b9066` score `0.994752`
  loss: `autoencoder_residual_cluster` = `0.399242165968`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-31-1121-71177e9ae735ce0b, us-code-16-47a-26c452e74b52db99, us-code-7-450-759794f8a1f6176f, us-code-8-1365b-a825991ce12b9ec4`
  evidence: `{"cosine_similarity": 0.35265428627, "hint_id": "modal-synthesis-076345e1888567a9", "priority": 0.431640532516, "reconstruction_loss": 0.431640532516, "sample_id": "us-code-16-47a-26c452e74b52db99"}`
  evidence: `{"cosine_similarity": 0.294378194805, "hint_id": "modal-synthesis-573d05649564bc1d", "priority": 0.345424598846, "reconstruction_loss": 0.345424598846, "sample_id": "us-code-8-1365b-a825991ce12b9ec4"}`
  evidence: `{"cosine_similarity": 0.402503493297, "hint_id": "modal-synthesis-a014361c3019f1eb", "priority": 0.34880263313, "reconstruction_loss": 0.34880263313, "sample_id": "us-code-7-450-759794f8a1f6176f"}`
  evidence: `{"cosine_similarity": -0.044104511491, "hint_id": "modal-synthesis-fcfc8ca4fabea001", "priority": 0.47110089938, "reconstruction_loss": 0.47110089938, "sample_id": "us-code-31-1121-71177e9ae735ce0b"}`
- `program-d53757061cde4039`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-becc7f64c45b9066` score `0.994529`
  loss: `autoencoder_residual_cluster` = `0.324200018739`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-34-10307-3d13e651f2feb776, us-code-6-924-46b4e91da16607f0, us-code-33-444-516a16b59ab41826, us-code-5-10-852d8ede8019f304`
  evidence: `{"cosine_similarity": 0.537875562781, "hint_id": "modal-synthesis-00a6530477b468a9", "priority": 0.338191566023, "reconstruction_loss": 0.338191566023, "sample_id": "us-code-6-924-46b4e91da16607f0"}`
  evidence: `{"cosine_similarity": 0.75123959, "hint_id": "modal-synthesis-2db9a44451326ecc", "priority": 0.185624271959, "reconstruction_loss": 0.185624271959, "sample_id": "us-code-5-10-852d8ede8019f304"}`
  evidence: `{"cosine_similarity": 0.123435570296, "hint_id": "modal-synthesis-39c7d92d171be984", "priority": 0.545127968469, "reconstruction_loss": 0.545127968469, "sample_id": "us-code-34-10307-3d13e651f2feb776"}`
  evidence: `{"cosine_similarity": 0.42837431094, "hint_id": "modal-synthesis-d3089cbfd3578eac", "priority": 0.227856268506, "reconstruction_loss": 0.227856268506, "sample_id": "us-code-33-444-516a16b59ab41826"}`
