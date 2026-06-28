# packet-000061

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000061/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000061/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000061-20260518_131943

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-32b4ef3ca56d5fdb` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-32b4ef3ca56d5fdb` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.574123838466, "hint_id": "modal-synthesis-31d7f97a34b5e2c7", "priority": 0.895437831863, "reconstruction_loss": 0.895437831863, "sample_id": "us-code-48-2146.-435be10c1c6c2688"}`
  evidence: `{"cosine_similarity": -0.23794382235, "hint_id": "modal-synthesis-3389fc1c7bf0ae42", "priority": 0.560198207568, "reconstruction_loss": 0.560198207568, "sample_id": "us-code-42-15113.-be490a63be6c7d3a"}`
  evidence: `{"cosine_similarity": 0.285587278591, "hint_id": "modal-synthesis-3e5723497093b697", "priority": 0.306115226181, "reconstruction_loss": 0.306115226181, "sample_id": "us-code-25-3742-07c82320791611f1"}`
  evidence: `{"cosine_similarity": 0.622782268498, "hint_id": "modal-synthesis-547e658e2b5b2728", "priority": 0.19324862098, "reconstruction_loss": 0.19324862098, "sample_id": "us-code-46-30908.-a29b051f6f1dce13"}`
- `program-8b1af39a8c504130` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-32b4ef3ca56d5fdb` score `0.993946`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.595806938329, "hint_id": "modal-synthesis-04e5d0417617bd93", "priority": 0.514229958758, "reconstruction_loss": 0.514229958758, "sample_id": "us-code-12-1831cc-c7b61dd8e184ad94"}`
  evidence: `{"cosine_similarity": 0.60151602333, "hint_id": "modal-synthesis-1482e359400036d6", "priority": 0.246644100162, "reconstruction_loss": 0.246644100162, "sample_id": "us-code-33-3203-3c7405d1f67d28da"}`
  evidence: `{"cosine_similarity": -0.098195615474, "hint_id": "modal-synthesis-63c37d8c235163be", "priority": 0.516991968156, "reconstruction_loss": 0.516991968156, "sample_id": "us-code-42-3796ii-c190061c9a76e369"}`
  evidence: `{"cosine_similarity": 0.797195916489, "hint_id": "modal-synthesis-be287f1fcb847e53", "priority": 0.210315802767, "reconstruction_loss": 0.210315802767, "sample_id": "us-code-34-20991-b57c0f9ca0db93ed"}`
- `program-7856b77b6705fc71` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-32b4ef3ca56d5fdb` score `0.992954`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.187277191974, "hint_id": "modal-synthesis-25ef12463bf87859", "priority": 0.327803807666, "reconstruction_loss": 0.327803807666, "sample_id": "us-code-42-15251.-c8bc40200627c975"}`
  evidence: `{"cosine_similarity": -0.533575815414, "hint_id": "modal-synthesis-5edce2cf064132c0", "priority": 0.439342314221, "reconstruction_loss": 0.439342314221, "sample_id": "us-code-14-1155-e938dff6f2f5890b"}`
  evidence: `{"cosine_similarity": 0.112112884981, "hint_id": "modal-synthesis-e724e0a36538ba79", "priority": 0.442974447012, "reconstruction_loss": 0.442974447012, "sample_id": "us-code-46-55318.-a7002ab697067d67"}`
  evidence: `{"cosine_similarity": -0.074661260543, "hint_id": "modal-synthesis-fa52713c4e146360", "priority": 0.456822515049, "reconstruction_loss": 0.456822515049, "sample_id": "us-code-42-665.-09a84f3d930035b6"}`

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
- `program-32b4ef3ca56d5fdb`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-32b4ef3ca56d5fdb` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.488749971648`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-48-2146.-435be10c1c6c2688, us-code-42-15113.-be490a63be6c7d3a, us-code-25-3742-07c82320791611f1, us-code-46-30908.-a29b051f6f1dce13`
  evidence: `{"cosine_similarity": -0.574123838466, "hint_id": "modal-synthesis-31d7f97a34b5e2c7", "priority": 0.895437831863, "reconstruction_loss": 0.895437831863, "sample_id": "us-code-48-2146.-435be10c1c6c2688"}`
  evidence: `{"cosine_similarity": -0.23794382235, "hint_id": "modal-synthesis-3389fc1c7bf0ae42", "priority": 0.560198207568, "reconstruction_loss": 0.560198207568, "sample_id": "us-code-42-15113.-be490a63be6c7d3a"}`
  evidence: `{"cosine_similarity": 0.285587278591, "hint_id": "modal-synthesis-3e5723497093b697", "priority": 0.306115226181, "reconstruction_loss": 0.306115226181, "sample_id": "us-code-25-3742-07c82320791611f1"}`
  evidence: `{"cosine_similarity": 0.622782268498, "hint_id": "modal-synthesis-547e658e2b5b2728", "priority": 0.19324862098, "reconstruction_loss": 0.19324862098, "sample_id": "us-code-46-30908.-a29b051f6f1dce13"}`
- `program-8b1af39a8c504130`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-32b4ef3ca56d5fdb` score `0.993946`
  loss: `autoencoder_residual_cluster` = `0.372045457461`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-3796ii-c190061c9a76e369, us-code-12-1831cc-c7b61dd8e184ad94, us-code-33-3203-3c7405d1f67d28da, us-code-34-20991-b57c0f9ca0db93ed`
  evidence: `{"cosine_similarity": -0.595806938329, "hint_id": "modal-synthesis-04e5d0417617bd93", "priority": 0.514229958758, "reconstruction_loss": 0.514229958758, "sample_id": "us-code-12-1831cc-c7b61dd8e184ad94"}`
  evidence: `{"cosine_similarity": 0.60151602333, "hint_id": "modal-synthesis-1482e359400036d6", "priority": 0.246644100162, "reconstruction_loss": 0.246644100162, "sample_id": "us-code-33-3203-3c7405d1f67d28da"}`
  evidence: `{"cosine_similarity": -0.098195615474, "hint_id": "modal-synthesis-63c37d8c235163be", "priority": 0.516991968156, "reconstruction_loss": 0.516991968156, "sample_id": "us-code-42-3796ii-c190061c9a76e369"}`
  evidence: `{"cosine_similarity": 0.797195916489, "hint_id": "modal-synthesis-be287f1fcb847e53", "priority": 0.210315802767, "reconstruction_loss": 0.210315802767, "sample_id": "us-code-34-20991-b57c0f9ca0db93ed"}`
- `program-7856b77b6705fc71`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-32b4ef3ca56d5fdb` score `0.992954`
  loss: `autoencoder_residual_cluster` = `0.416735770987`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-665.-09a84f3d930035b6, us-code-46-55318.-a7002ab697067d67, us-code-14-1155-e938dff6f2f5890b, us-code-42-15251.-c8bc40200627c975`
  evidence: `{"cosine_similarity": 0.187277191974, "hint_id": "modal-synthesis-25ef12463bf87859", "priority": 0.327803807666, "reconstruction_loss": 0.327803807666, "sample_id": "us-code-42-15251.-c8bc40200627c975"}`
  evidence: `{"cosine_similarity": -0.533575815414, "hint_id": "modal-synthesis-5edce2cf064132c0", "priority": 0.439342314221, "reconstruction_loss": 0.439342314221, "sample_id": "us-code-14-1155-e938dff6f2f5890b"}`
  evidence: `{"cosine_similarity": 0.112112884981, "hint_id": "modal-synthesis-e724e0a36538ba79", "priority": 0.442974447012, "reconstruction_loss": 0.442974447012, "sample_id": "us-code-46-55318.-a7002ab697067d67"}`
  evidence: `{"cosine_similarity": -0.074661260543, "hint_id": "modal-synthesis-fa52713c4e146360", "priority": 0.456822515049, "reconstruction_loss": 0.456822515049, "sample_id": "us-code-42-665.-09a84f3d930035b6"}`
