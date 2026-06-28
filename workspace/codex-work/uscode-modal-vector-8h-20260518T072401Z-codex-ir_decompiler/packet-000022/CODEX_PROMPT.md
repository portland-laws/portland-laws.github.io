# packet-000022

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000022/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000022/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000022-20260518_092457

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-e7f4b10e8ddc6e84` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e7f4b10e8ddc6e84` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.250037084142, "hint_id": "modal-synthesis-3912a69ca2ec0e46", "priority": 0.531677263652, "reconstruction_loss": 0.531677263652, "sample_id": "us-code-15-78u-3-ee2050477d2aec44"}`
  evidence: `{"cosine_similarity": -0.442160236663, "hint_id": "modal-synthesis-8270aad0f218941f", "priority": 0.928075936982, "reconstruction_loss": 0.928075936982, "sample_id": "us-code-43-1473c.-2d2a046860434dea"}`
  evidence: `{"cosine_similarity": 0.130307021069, "hint_id": "modal-synthesis-a6e0671b88a3a6c3", "priority": 0.426759351089, "reconstruction_loss": 0.426759351089, "sample_id": "us-code-52-30144.-e258143d2f58a48d"}`
  evidence: `{"cosine_similarity": 0.090529926624, "hint_id": "modal-synthesis-e34cf236be0d75e5", "priority": 0.439830323816, "reconstruction_loss": 0.439830323816, "sample_id": "us-code-25-728-b4eb2832937265d5"}`
- `program-ae39cec12642553d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e7f4b10e8ddc6e84` score `0.994565`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.037128161474, "hint_id": "modal-synthesis-10512b3e8ca33285", "priority": 0.367165160382, "reconstruction_loss": 0.367165160382, "sample_id": "us-code-33-1367-a9c539ff72272b44"}`
  evidence: `{"cosine_similarity": 0.046488334455, "hint_id": "modal-synthesis-7e3e5e38c88957a7", "priority": 0.516707037143, "reconstruction_loss": 0.516707037143, "sample_id": "us-code-42-4629.-4ee296debf8f5c10"}`
  evidence: `{"cosine_similarity": 0.245153112645, "hint_id": "modal-synthesis-b6277c95a812febc", "priority": 0.442575286602, "reconstruction_loss": 0.442575286602, "sample_id": "us-code-16-361e-ab77b152bad77be1"}`
  evidence: `{"cosine_similarity": -0.72245848653, "hint_id": "modal-synthesis-cd2ff546b3a39b8a", "priority": 0.675538907949, "reconstruction_loss": 0.675538907949, "sample_id": "us-code-43-375e.-b9c9ddd539a1f4bf"}`
- `program-02550ec329d4164e` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e7f4b10e8ddc6e84` score `0.993686`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.251958351406, "hint_id": "modal-synthesis-9934d9cc87819bbe", "priority": 0.438073794127, "reconstruction_loss": 0.438073794127, "sample_id": "us-code-51-20139.-7a842787eecc66aa"}`
  evidence: `{"cosine_similarity": -0.273506600809, "hint_id": "modal-synthesis-9fe6bd484c424b0d", "priority": 0.337458627001, "reconstruction_loss": 0.337458627001, "sample_id": "us-code-22-8771-3e41f3d8cf08a4c5"}`
  evidence: `{"cosine_similarity": 0.058143059473, "hint_id": "modal-synthesis-abd44f6b7842d21e", "priority": 0.51493375475, "reconstruction_loss": 0.51493375475, "sample_id": "us-code-26-956A-260a522b66789c53"}`
  evidence: `{"cosine_similarity": 0.521686907823, "hint_id": "modal-synthesis-cf80f3ce028175b2", "priority": 0.386515303019, "reconstruction_loss": 0.386515303019, "sample_id": "us-code-26-4946-3d47497d3e73bcae"}`

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
- `program-e7f4b10e8ddc6e84`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e7f4b10e8ddc6e84` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.581585718885`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-43-1473c.-2d2a046860434dea, us-code-15-78u-3-ee2050477d2aec44, us-code-25-728-b4eb2832937265d5, us-code-52-30144.-e258143d2f58a48d`
  evidence: `{"cosine_similarity": 0.250037084142, "hint_id": "modal-synthesis-3912a69ca2ec0e46", "priority": 0.531677263652, "reconstruction_loss": 0.531677263652, "sample_id": "us-code-15-78u-3-ee2050477d2aec44"}`
  evidence: `{"cosine_similarity": -0.442160236663, "hint_id": "modal-synthesis-8270aad0f218941f", "priority": 0.928075936982, "reconstruction_loss": 0.928075936982, "sample_id": "us-code-43-1473c.-2d2a046860434dea"}`
  evidence: `{"cosine_similarity": 0.130307021069, "hint_id": "modal-synthesis-a6e0671b88a3a6c3", "priority": 0.426759351089, "reconstruction_loss": 0.426759351089, "sample_id": "us-code-52-30144.-e258143d2f58a48d"}`
  evidence: `{"cosine_similarity": 0.090529926624, "hint_id": "modal-synthesis-e34cf236be0d75e5", "priority": 0.439830323816, "reconstruction_loss": 0.439830323816, "sample_id": "us-code-25-728-b4eb2832937265d5"}`
- `program-ae39cec12642553d`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e7f4b10e8ddc6e84` score `0.994565`
  loss: `autoencoder_residual_cluster` = `0.500496598019`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-43-375e.-b9c9ddd539a1f4bf, us-code-42-4629.-4ee296debf8f5c10, us-code-16-361e-ab77b152bad77be1, us-code-33-1367-a9c539ff72272b44`
  evidence: `{"cosine_similarity": -0.037128161474, "hint_id": "modal-synthesis-10512b3e8ca33285", "priority": 0.367165160382, "reconstruction_loss": 0.367165160382, "sample_id": "us-code-33-1367-a9c539ff72272b44"}`
  evidence: `{"cosine_similarity": 0.046488334455, "hint_id": "modal-synthesis-7e3e5e38c88957a7", "priority": 0.516707037143, "reconstruction_loss": 0.516707037143, "sample_id": "us-code-42-4629.-4ee296debf8f5c10"}`
  evidence: `{"cosine_similarity": 0.245153112645, "hint_id": "modal-synthesis-b6277c95a812febc", "priority": 0.442575286602, "reconstruction_loss": 0.442575286602, "sample_id": "us-code-16-361e-ab77b152bad77be1"}`
  evidence: `{"cosine_similarity": -0.72245848653, "hint_id": "modal-synthesis-cd2ff546b3a39b8a", "priority": 0.675538907949, "reconstruction_loss": 0.675538907949, "sample_id": "us-code-43-375e.-b9c9ddd539a1f4bf"}`
- `program-02550ec329d4164e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e7f4b10e8ddc6e84` score `0.993686`
  loss: `autoencoder_residual_cluster` = `0.419245369724`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-956A-260a522b66789c53, us-code-51-20139.-7a842787eecc66aa, us-code-26-4946-3d47497d3e73bcae, us-code-22-8771-3e41f3d8cf08a4c5`
  evidence: `{"cosine_similarity": 0.251958351406, "hint_id": "modal-synthesis-9934d9cc87819bbe", "priority": 0.438073794127, "reconstruction_loss": 0.438073794127, "sample_id": "us-code-51-20139.-7a842787eecc66aa"}`
  evidence: `{"cosine_similarity": -0.273506600809, "hint_id": "modal-synthesis-9fe6bd484c424b0d", "priority": 0.337458627001, "reconstruction_loss": 0.337458627001, "sample_id": "us-code-22-8771-3e41f3d8cf08a4c5"}`
  evidence: `{"cosine_similarity": 0.058143059473, "hint_id": "modal-synthesis-abd44f6b7842d21e", "priority": 0.51493375475, "reconstruction_loss": 0.51493375475, "sample_id": "us-code-26-956A-260a522b66789c53"}`
  evidence: `{"cosine_similarity": 0.521686907823, "hint_id": "modal-synthesis-cf80f3ce028175b2", "priority": 0.386515303019, "reconstruction_loss": 0.386515303019, "sample_id": "us-code-26-4946-3d47497d3e73bcae"}`
