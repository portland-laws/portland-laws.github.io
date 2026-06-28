# packet-000081

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000081/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000081/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000081-20260518_154643

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-10cc7cdebe3173bf` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-10cc7cdebe3173bf` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.34618529704, "hint_id": "modal-synthesis-0ef4c8723bc9db3f", "priority": 0.552763056249, "reconstruction_loss": 0.552763056249, "sample_id": "us-code-49-44114.-ae03827f4ac4af72"}`
  evidence: `{"cosine_similarity": -0.427041578293, "hint_id": "modal-synthesis-3258618d814497e6", "priority": 0.329952485159, "reconstruction_loss": 0.329952485159, "sample_id": "us-code-25-1521-9c8e3d4bc1c6f2c4"}`
  evidence: `{"cosine_similarity": -0.118153874082, "hint_id": "modal-synthesis-726a8f8e62c7ea91", "priority": 0.611517595697, "reconstruction_loss": 0.611517595697, "sample_id": "us-code-43-1.-f897d28cfa30563e"}`
  evidence: `{"cosine_similarity": 0.633621418989, "hint_id": "modal-synthesis-a6abfc58e15b6daf", "priority": 0.239149401855, "reconstruction_loss": 0.239149401855, "sample_id": "us-code-50-403-3b247020d38be31f"}`
- `program-a326ffeafeecfb7a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-10cc7cdebe3173bf` score `0.993384`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.112945510864, "hint_id": "modal-synthesis-2bdd72857d432084", "priority": 0.37609795055, "reconstruction_loss": 0.37609795055, "sample_id": "us-code-26-985-711ffcc6aa671afc"}`
  evidence: `{"cosine_similarity": 0.230591328137, "hint_id": "modal-synthesis-3e1042eea1ca67ab", "priority": 0.176464762742, "reconstruction_loss": 0.176464762742, "sample_id": "us-code-25-118-d6d7ef1f5d1f9c66"}`
  evidence: `{"cosine_similarity": -0.673280190913, "hint_id": "modal-synthesis-946bbc1f67c149f7", "priority": 0.591658068816, "reconstruction_loss": 0.591658068816, "sample_id": "us-code-40-3111-e3a7ddbab17ebaea"}`
  evidence: `{"cosine_similarity": 0.17529637054, "hint_id": "modal-synthesis-f854ce5058b9d68b", "priority": 0.287703315468, "reconstruction_loss": 0.287703315468, "sample_id": "us-code-41-1703-9db1a964c184e964"}`
- `program-642d74ebd979ab4a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-10cc7cdebe3173bf` score `0.993204`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.307973311693, "hint_id": "modal-synthesis-57162886110c7b47", "priority": 0.420762902052, "reconstruction_loss": 0.420762902052, "sample_id": "us-code-42-300gg-8f8607d568e0a328"}`
  evidence: `{"cosine_similarity": 0.470852546927, "hint_id": "modal-synthesis-ae482e1b7de731fe", "priority": 0.125402509064, "reconstruction_loss": 0.125402509064, "sample_id": "us-code-2-132a-464703c77bb723dd"}`
  evidence: `{"cosine_similarity": -0.202464071192, "hint_id": "modal-synthesis-b906cfdad5d5e314", "priority": 0.494902752277, "reconstruction_loss": 0.494902752277, "sample_id": "us-code-10-8245-44462289f99ceb81"}`
  evidence: `{"cosine_similarity": -0.460318435636, "hint_id": "modal-synthesis-e00290e10f6a936a", "priority": 0.685525024964, "reconstruction_loss": 0.685525024964, "sample_id": "us-code-7-1651-e60bc4810b20c5b7"}`

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
- `program-10cc7cdebe3173bf`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-10cc7cdebe3173bf` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.43334563474`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-43-1.-f897d28cfa30563e, us-code-49-44114.-ae03827f4ac4af72, us-code-25-1521-9c8e3d4bc1c6f2c4, us-code-50-403-3b247020d38be31f`
  evidence: `{"cosine_similarity": -0.34618529704, "hint_id": "modal-synthesis-0ef4c8723bc9db3f", "priority": 0.552763056249, "reconstruction_loss": 0.552763056249, "sample_id": "us-code-49-44114.-ae03827f4ac4af72"}`
  evidence: `{"cosine_similarity": -0.427041578293, "hint_id": "modal-synthesis-3258618d814497e6", "priority": 0.329952485159, "reconstruction_loss": 0.329952485159, "sample_id": "us-code-25-1521-9c8e3d4bc1c6f2c4"}`
  evidence: `{"cosine_similarity": -0.118153874082, "hint_id": "modal-synthesis-726a8f8e62c7ea91", "priority": 0.611517595697, "reconstruction_loss": 0.611517595697, "sample_id": "us-code-43-1.-f897d28cfa30563e"}`
  evidence: `{"cosine_similarity": 0.633621418989, "hint_id": "modal-synthesis-a6abfc58e15b6daf", "priority": 0.239149401855, "reconstruction_loss": 0.239149401855, "sample_id": "us-code-50-403-3b247020d38be31f"}`
- `program-a326ffeafeecfb7a`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-10cc7cdebe3173bf` score `0.993384`
  loss: `autoencoder_residual_cluster` = `0.357981024394`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-40-3111-e3a7ddbab17ebaea, us-code-26-985-711ffcc6aa671afc, us-code-41-1703-9db1a964c184e964, us-code-25-118-d6d7ef1f5d1f9c66`
  evidence: `{"cosine_similarity": 0.112945510864, "hint_id": "modal-synthesis-2bdd72857d432084", "priority": 0.37609795055, "reconstruction_loss": 0.37609795055, "sample_id": "us-code-26-985-711ffcc6aa671afc"}`
  evidence: `{"cosine_similarity": 0.230591328137, "hint_id": "modal-synthesis-3e1042eea1ca67ab", "priority": 0.176464762742, "reconstruction_loss": 0.176464762742, "sample_id": "us-code-25-118-d6d7ef1f5d1f9c66"}`
  evidence: `{"cosine_similarity": -0.673280190913, "hint_id": "modal-synthesis-946bbc1f67c149f7", "priority": 0.591658068816, "reconstruction_loss": 0.591658068816, "sample_id": "us-code-40-3111-e3a7ddbab17ebaea"}`
  evidence: `{"cosine_similarity": 0.17529637054, "hint_id": "modal-synthesis-f854ce5058b9d68b", "priority": 0.287703315468, "reconstruction_loss": 0.287703315468, "sample_id": "us-code-41-1703-9db1a964c184e964"}`
- `program-642d74ebd979ab4a`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-10cc7cdebe3173bf` score `0.993204`
  loss: `autoencoder_residual_cluster` = `0.431648297089`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-1651-e60bc4810b20c5b7, us-code-10-8245-44462289f99ceb81, us-code-42-300gg-8f8607d568e0a328, us-code-2-132a-464703c77bb723dd`
  evidence: `{"cosine_similarity": -0.307973311693, "hint_id": "modal-synthesis-57162886110c7b47", "priority": 0.420762902052, "reconstruction_loss": 0.420762902052, "sample_id": "us-code-42-300gg-8f8607d568e0a328"}`
  evidence: `{"cosine_similarity": 0.470852546927, "hint_id": "modal-synthesis-ae482e1b7de731fe", "priority": 0.125402509064, "reconstruction_loss": 0.125402509064, "sample_id": "us-code-2-132a-464703c77bb723dd"}`
  evidence: `{"cosine_similarity": -0.202464071192, "hint_id": "modal-synthesis-b906cfdad5d5e314", "priority": 0.494902752277, "reconstruction_loss": 0.494902752277, "sample_id": "us-code-10-8245-44462289f99ceb81"}`
  evidence: `{"cosine_similarity": -0.460318435636, "hint_id": "modal-synthesis-e00290e10f6a936a", "priority": 0.685525024964, "reconstruction_loss": 0.685525024964, "sample_id": "us-code-7-1651-e60bc4810b20c5b7"}`
