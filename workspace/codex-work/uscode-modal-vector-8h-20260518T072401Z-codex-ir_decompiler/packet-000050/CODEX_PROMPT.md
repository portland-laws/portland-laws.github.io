# packet-000050

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000050/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000050/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000050-20260518_121158

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-00c7f90f09e9d0c5` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-00c7f90f09e9d0c5` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.719051393215, "hint_id": "modal-synthesis-368b6109a8a888dd", "priority": 0.987764099961, "reconstruction_loss": 0.987764099961, "sample_id": "us-code-42-12752.-22fb1fe07b4c5173"}`
  evidence: `{"cosine_similarity": 0.265417325033, "hint_id": "modal-synthesis-9c88a94d2d9270e0", "priority": 0.401046772684, "reconstruction_loss": 0.401046772684, "sample_id": "us-code-15-1693o-2-2408eae6e5a9204e"}`
  evidence: `{"cosine_similarity": -0.015627314051, "hint_id": "modal-synthesis-e7e33bb84b0ae376", "priority": 0.391563894264, "reconstruction_loss": 0.391563894264, "sample_id": "us-code-20-6021-80e97e93a8c629aa"}`
  evidence: `{"cosine_similarity": 0.275238733796, "hint_id": "modal-synthesis-ee74b683adb01091", "priority": 0.305083520212, "reconstruction_loss": 0.305083520212, "sample_id": "us-code-42-247d-fabf88284c55cda8"}`
- `program-b3c9367ca93feda3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-00c7f90f09e9d0c5` score `0.994362`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.085140326776, "hint_id": "modal-synthesis-4f196d91bb00725a", "priority": 0.381503036839, "reconstruction_loss": 0.381503036839, "sample_id": "us-code-42-7671j.-7e1a3a5a982b94d0"}`
  evidence: `{"cosine_similarity": -0.555691068289, "hint_id": "modal-synthesis-54416084b81710ec", "priority": 0.762072141402, "reconstruction_loss": 0.762072141402, "sample_id": "us-code-31-3525-e90154f9559f626c"}`
  evidence: `{"cosine_similarity": 0.174793459075, "hint_id": "modal-synthesis-886792417c39fab0", "priority": 0.375683111864, "reconstruction_loss": 0.375683111864, "sample_id": "us-code-42-280h-b7073f12b34f8c3e"}`
  evidence: `{"cosine_similarity": 0.635703687104, "hint_id": "modal-synthesis-e772b0e9e40d5578", "priority": 0.194328194542, "reconstruction_loss": 0.194328194542, "sample_id": "us-code-25-117-8a7b8d693320173d"}`
- `program-9260b11444a266d7` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-00c7f90f09e9d0c5` score `0.994064`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.559001866694, "hint_id": "modal-synthesis-0973e3acf0a499c4", "priority": 0.291233453081, "reconstruction_loss": 0.291233453081, "sample_id": "us-code-10-949h-7cc1d19c8671b6c7"}`
  evidence: `{"cosine_similarity": 0.306121444938, "hint_id": "modal-synthesis-1ab0e6fdc5d4b82a", "priority": 0.283636229629, "reconstruction_loss": 0.283636229629, "sample_id": "us-code-26-4963-7e2728b28cb8837f"}`
  evidence: `{"cosine_similarity": 0.393516477406, "hint_id": "modal-synthesis-85a0347ccfabe9c9", "priority": 0.294523722769, "reconstruction_loss": 0.294523722769, "sample_id": "us-code-15-1666i-2-a76d89c3d53690b1"}`
  evidence: `{"cosine_similarity": -0.230232973917, "hint_id": "modal-synthesis-d2ad6214d2c213e2", "priority": 0.806243988228, "reconstruction_loss": 0.806243988228, "sample_id": "us-code-42-430.-bc74777c34a97ef8"}`

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
- `program-00c7f90f09e9d0c5`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-00c7f90f09e9d0c5` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.52136457178`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-12752.-22fb1fe07b4c5173, us-code-15-1693o-2-2408eae6e5a9204e, us-code-20-6021-80e97e93a8c629aa, us-code-42-247d-fabf88284c55cda8`
  evidence: `{"cosine_similarity": -0.719051393215, "hint_id": "modal-synthesis-368b6109a8a888dd", "priority": 0.987764099961, "reconstruction_loss": 0.987764099961, "sample_id": "us-code-42-12752.-22fb1fe07b4c5173"}`
  evidence: `{"cosine_similarity": 0.265417325033, "hint_id": "modal-synthesis-9c88a94d2d9270e0", "priority": 0.401046772684, "reconstruction_loss": 0.401046772684, "sample_id": "us-code-15-1693o-2-2408eae6e5a9204e"}`
  evidence: `{"cosine_similarity": -0.015627314051, "hint_id": "modal-synthesis-e7e33bb84b0ae376", "priority": 0.391563894264, "reconstruction_loss": 0.391563894264, "sample_id": "us-code-20-6021-80e97e93a8c629aa"}`
  evidence: `{"cosine_similarity": 0.275238733796, "hint_id": "modal-synthesis-ee74b683adb01091", "priority": 0.305083520212, "reconstruction_loss": 0.305083520212, "sample_id": "us-code-42-247d-fabf88284c55cda8"}`
- `program-b3c9367ca93feda3`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-00c7f90f09e9d0c5` score `0.994362`
  loss: `autoencoder_residual_cluster` = `0.428396621162`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-31-3525-e90154f9559f626c, us-code-42-7671j.-7e1a3a5a982b94d0, us-code-42-280h-b7073f12b34f8c3e, us-code-25-117-8a7b8d693320173d`
  evidence: `{"cosine_similarity": 0.085140326776, "hint_id": "modal-synthesis-4f196d91bb00725a", "priority": 0.381503036839, "reconstruction_loss": 0.381503036839, "sample_id": "us-code-42-7671j.-7e1a3a5a982b94d0"}`
  evidence: `{"cosine_similarity": -0.555691068289, "hint_id": "modal-synthesis-54416084b81710ec", "priority": 0.762072141402, "reconstruction_loss": 0.762072141402, "sample_id": "us-code-31-3525-e90154f9559f626c"}`
  evidence: `{"cosine_similarity": 0.174793459075, "hint_id": "modal-synthesis-886792417c39fab0", "priority": 0.375683111864, "reconstruction_loss": 0.375683111864, "sample_id": "us-code-42-280h-b7073f12b34f8c3e"}`
  evidence: `{"cosine_similarity": 0.635703687104, "hint_id": "modal-synthesis-e772b0e9e40d5578", "priority": 0.194328194542, "reconstruction_loss": 0.194328194542, "sample_id": "us-code-25-117-8a7b8d693320173d"}`
- `program-9260b11444a266d7`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-00c7f90f09e9d0c5` score `0.994064`
  loss: `autoencoder_residual_cluster` = `0.418909348427`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-430.-bc74777c34a97ef8, us-code-15-1666i-2-a76d89c3d53690b1, us-code-10-949h-7cc1d19c8671b6c7, us-code-26-4963-7e2728b28cb8837f`
  evidence: `{"cosine_similarity": 0.559001866694, "hint_id": "modal-synthesis-0973e3acf0a499c4", "priority": 0.291233453081, "reconstruction_loss": 0.291233453081, "sample_id": "us-code-10-949h-7cc1d19c8671b6c7"}`
  evidence: `{"cosine_similarity": 0.306121444938, "hint_id": "modal-synthesis-1ab0e6fdc5d4b82a", "priority": 0.283636229629, "reconstruction_loss": 0.283636229629, "sample_id": "us-code-26-4963-7e2728b28cb8837f"}`
  evidence: `{"cosine_similarity": 0.393516477406, "hint_id": "modal-synthesis-85a0347ccfabe9c9", "priority": 0.294523722769, "reconstruction_loss": 0.294523722769, "sample_id": "us-code-15-1666i-2-a76d89c3d53690b1"}`
  evidence: `{"cosine_similarity": -0.230232973917, "hint_id": "modal-synthesis-d2ad6214d2c213e2", "priority": 0.806243988228, "reconstruction_loss": 0.806243988228, "sample_id": "us-code-42-430.-bc74777c34a97ef8"}`
