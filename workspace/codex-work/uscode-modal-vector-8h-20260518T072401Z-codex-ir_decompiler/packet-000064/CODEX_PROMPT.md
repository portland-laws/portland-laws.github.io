# packet-000064

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000064/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000064/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000064-20260518_133955

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-9927abd05a20393b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.393838688215, "hint_id": "modal-synthesis-01d46f9a4b581df3", "priority": 0.580689797434, "reconstruction_loss": 0.580689797434, "sample_id": "us-code-28-363-5f6bfa732952e00b"}`
  evidence: `{"cosine_similarity": 0.427614758839, "hint_id": "modal-synthesis-68aeabe5f6af6a2b", "priority": 0.244477998097, "reconstruction_loss": 0.244477998097, "sample_id": "us-code-25-4163-2eae7188dc5c764c"}`
  evidence: `{"cosine_similarity": -0.373051907987, "hint_id": "modal-synthesis-7c941214f6b488fe", "priority": 0.552639272259, "reconstruction_loss": 0.552639272259, "sample_id": "us-code-46-31109.-99db4340d1749cd8"}`
  evidence: `{"cosine_similarity": -0.753182057899, "hint_id": "modal-synthesis-c9cfd5a01bb38aa5", "priority": 0.653603794375, "reconstruction_loss": 0.653603794375, "sample_id": "us-code-25-1300d-2-13848766d43c7ed4"}`
- `program-0259022affa2db77` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `0.992853`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.621179143149, "hint_id": "modal-synthesis-39210b832bf8fd11", "priority": 0.178369647054, "reconstruction_loss": 0.178369647054, "sample_id": "us-code-7-2143-cbad35cf9d290cf0"}`
  evidence: `{"cosine_similarity": 0.128179243378, "hint_id": "modal-synthesis-5c779d3cdde46c39", "priority": 0.445644549679, "reconstruction_loss": 0.445644549679, "sample_id": "us-code-28-2245-d1ea16b1ac50014b"}`
  evidence: `{"cosine_similarity": -0.186394924636, "hint_id": "modal-synthesis-93424fb108379634", "priority": 0.683242663074, "reconstruction_loss": 0.683242663074, "sample_id": "us-code-20-6082-6a0e64a86e194aa8"}`
  evidence: `{"cosine_similarity": -0.452277523087, "hint_id": "modal-synthesis-be5ef7f07eaafb6e", "priority": 0.611143621452, "reconstruction_loss": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
- `program-7b683915216908c3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `0.992527`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.315949751766, "hint_id": "modal-synthesis-2710b7b4c8bde0fc", "priority": 0.516439971177, "reconstruction_loss": 0.516439971177, "sample_id": "us-code-42-2981 to 2981c.-4bed92f2f879fa8f"}`
  evidence: `{"cosine_similarity": -0.33229760373, "hint_id": "modal-synthesis-837aa6806f891a54", "priority": 0.539929254334, "reconstruction_loss": 0.539929254334, "sample_id": "us-code-7-6416-7ac2926c94b239ae"}`
  evidence: `{"cosine_similarity": 0.018374851804, "hint_id": "modal-synthesis-895a91d028b40bbb", "priority": 0.392714684205, "reconstruction_loss": 0.392714684205, "sample_id": "us-code-50-3076.-f7b429a4acb2df69"}`
  evidence: `{"cosine_similarity": 0.221937538484, "hint_id": "modal-synthesis-e17e7a98b5e59525", "priority": 0.504428467593, "reconstruction_loss": 0.504428467593, "sample_id": "us-code-10-8821-c6406d88586fd9c4"}`

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
- `program-9927abd05a20393b`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.507852715541`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-1300d-2-13848766d43c7ed4, us-code-28-363-5f6bfa732952e00b, us-code-46-31109.-99db4340d1749cd8, us-code-25-4163-2eae7188dc5c764c`
  evidence: `{"cosine_similarity": 0.393838688215, "hint_id": "modal-synthesis-01d46f9a4b581df3", "priority": 0.580689797434, "reconstruction_loss": 0.580689797434, "sample_id": "us-code-28-363-5f6bfa732952e00b"}`
  evidence: `{"cosine_similarity": 0.427614758839, "hint_id": "modal-synthesis-68aeabe5f6af6a2b", "priority": 0.244477998097, "reconstruction_loss": 0.244477998097, "sample_id": "us-code-25-4163-2eae7188dc5c764c"}`
  evidence: `{"cosine_similarity": -0.373051907987, "hint_id": "modal-synthesis-7c941214f6b488fe", "priority": 0.552639272259, "reconstruction_loss": 0.552639272259, "sample_id": "us-code-46-31109.-99db4340d1749cd8"}`
  evidence: `{"cosine_similarity": -0.753182057899, "hint_id": "modal-synthesis-c9cfd5a01bb38aa5", "priority": 0.653603794375, "reconstruction_loss": 0.653603794375, "sample_id": "us-code-25-1300d-2-13848766d43c7ed4"}`
- `program-0259022affa2db77`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `0.992853`
  loss: `autoencoder_residual_cluster` = `0.479600120315`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-20-6082-6a0e64a86e194aa8, us-code-15-1717a-f876cffa460ff996, us-code-28-2245-d1ea16b1ac50014b, us-code-7-2143-cbad35cf9d290cf0`
  evidence: `{"cosine_similarity": 0.621179143149, "hint_id": "modal-synthesis-39210b832bf8fd11", "priority": 0.178369647054, "reconstruction_loss": 0.178369647054, "sample_id": "us-code-7-2143-cbad35cf9d290cf0"}`
  evidence: `{"cosine_similarity": 0.128179243378, "hint_id": "modal-synthesis-5c779d3cdde46c39", "priority": 0.445644549679, "reconstruction_loss": 0.445644549679, "sample_id": "us-code-28-2245-d1ea16b1ac50014b"}`
  evidence: `{"cosine_similarity": -0.186394924636, "hint_id": "modal-synthesis-93424fb108379634", "priority": 0.683242663074, "reconstruction_loss": 0.683242663074, "sample_id": "us-code-20-6082-6a0e64a86e194aa8"}`
  evidence: `{"cosine_similarity": -0.452277523087, "hint_id": "modal-synthesis-be5ef7f07eaafb6e", "priority": 0.611143621452, "reconstruction_loss": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
- `program-7b683915216908c3`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `0.992527`
  loss: `autoencoder_residual_cluster` = `0.488378094327`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-6416-7ac2926c94b239ae, us-code-42-2981 to 2981c.-4bed92f2f879fa8f, us-code-10-8821-c6406d88586fd9c4, us-code-50-3076.-f7b429a4acb2df69`
  evidence: `{"cosine_similarity": -0.315949751766, "hint_id": "modal-synthesis-2710b7b4c8bde0fc", "priority": 0.516439971177, "reconstruction_loss": 0.516439971177, "sample_id": "us-code-42-2981 to 2981c.-4bed92f2f879fa8f"}`
  evidence: `{"cosine_similarity": -0.33229760373, "hint_id": "modal-synthesis-837aa6806f891a54", "priority": 0.539929254334, "reconstruction_loss": 0.539929254334, "sample_id": "us-code-7-6416-7ac2926c94b239ae"}`
  evidence: `{"cosine_similarity": 0.018374851804, "hint_id": "modal-synthesis-895a91d028b40bbb", "priority": 0.392714684205, "reconstruction_loss": 0.392714684205, "sample_id": "us-code-50-3076.-f7b429a4acb2df69"}`
  evidence: `{"cosine_similarity": 0.221937538484, "hint_id": "modal-synthesis-e17e7a98b5e59525", "priority": 0.504428467593, "reconstruction_loss": 0.504428467593, "sample_id": "us-code-10-8821-c6406d88586fd9c4"}`
