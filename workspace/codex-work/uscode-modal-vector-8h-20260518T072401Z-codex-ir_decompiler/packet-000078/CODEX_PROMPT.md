# packet-000078

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000078/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000078/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000078-20260518_152400

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-9ebb066b8b3ff238` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9ebb066b8b3ff238` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.140079077145, "hint_id": "modal-synthesis-006f08982f74168a", "priority": 0.430151983404, "reconstruction_loss": 0.430151983404, "sample_id": "us-code-46-12140.-eb8fb458aa786fc0"}`
  evidence: `{"cosine_similarity": 0.034298016781, "hint_id": "modal-synthesis-3411cf1590c4fce6", "priority": 0.415836629248, "reconstruction_loss": 0.415836629248, "sample_id": "us-code-21-466-c1f1d5c503e2ccb3"}`
  evidence: `{"cosine_similarity": 0.567937684744, "hint_id": "modal-synthesis-bf25f2a0a67e2a2b", "priority": 0.340068487906, "reconstruction_loss": 0.340068487906, "sample_id": "us-code-19-1620-ed9bf5fa540afefb"}`
  evidence: `{"cosine_similarity": -0.639708498685, "hint_id": "modal-synthesis-df56331bcaf55a37", "priority": 0.679055520231, "reconstruction_loss": 0.679055520231, "sample_id": "us-code-42-12782.-01f3026e32e90a63"}`
- `program-1638cb5c5e93eebc` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9ebb066b8b3ff238` score `0.991612`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.159168950247, "hint_id": "modal-synthesis-0365fc09d3defd0f", "priority": 0.489302894062, "reconstruction_loss": 0.489302894062, "sample_id": "us-code-10-136a-498d8d89076e3d31"}`
  evidence: `{"cosine_similarity": -0.102539412398, "hint_id": "modal-synthesis-1ad71539dae39df9", "priority": 0.541111466075, "reconstruction_loss": 0.541111466075, "sample_id": "us-code-31-776-b3c3f6b94f08ad3f"}`
  evidence: `{"cosine_similarity": -0.21473217586, "hint_id": "modal-synthesis-56986a2c5d55888a", "priority": 0.474690805484, "reconstruction_loss": 0.474690805484, "sample_id": "us-code-48-1642.-f7d17eb875857fae"}`
  evidence: `{"cosine_similarity": 0.170119487474, "hint_id": "modal-synthesis-c1d104028dd77d9c", "priority": 0.347071767685, "reconstruction_loss": 0.347071767685, "sample_id": "us-code-36-152503-bfe1907e963f1c6c"}`
- `program-7d0d1e5c4c5c55bd` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9ebb066b8b3ff238` score `0.991033`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.377965429924, "hint_id": "modal-synthesis-6d9df178bb0e621d", "priority": 0.444532215549, "reconstruction_loss": 0.444532215549, "sample_id": "us-code-42-12313.-c1053dbe1a049f60"}`
  evidence: `{"cosine_similarity": -0.213090531967, "hint_id": "modal-synthesis-a081838770c11bd9", "priority": 0.484172329703, "reconstruction_loss": 0.484172329703, "sample_id": "us-code-8-606-f7dcbbfb006072f7"}`
  evidence: `{"cosine_similarity": 0.184721895531, "hint_id": "modal-synthesis-e80edafae5d4d06b", "priority": 0.32883346293, "reconstruction_loss": 0.32883346293, "sample_id": "us-code-42-18431.-b72b735d11b81b90"}`
  evidence: `{"cosine_similarity": -0.054520392314, "hint_id": "modal-synthesis-eb2d1b8f2afe16ac", "priority": 0.377513864366, "reconstruction_loss": 0.377513864366, "sample_id": "us-code-25-5396-17291bf2fa3ae3f6"}`

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
- `program-9ebb066b8b3ff238`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9ebb066b8b3ff238` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.466278155197`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-12782.-01f3026e32e90a63, us-code-46-12140.-eb8fb458aa786fc0, us-code-21-466-c1f1d5c503e2ccb3, us-code-19-1620-ed9bf5fa540afefb`
  evidence: `{"cosine_similarity": -0.140079077145, "hint_id": "modal-synthesis-006f08982f74168a", "priority": 0.430151983404, "reconstruction_loss": 0.430151983404, "sample_id": "us-code-46-12140.-eb8fb458aa786fc0"}`
  evidence: `{"cosine_similarity": 0.034298016781, "hint_id": "modal-synthesis-3411cf1590c4fce6", "priority": 0.415836629248, "reconstruction_loss": 0.415836629248, "sample_id": "us-code-21-466-c1f1d5c503e2ccb3"}`
  evidence: `{"cosine_similarity": 0.567937684744, "hint_id": "modal-synthesis-bf25f2a0a67e2a2b", "priority": 0.340068487906, "reconstruction_loss": 0.340068487906, "sample_id": "us-code-19-1620-ed9bf5fa540afefb"}`
  evidence: `{"cosine_similarity": -0.639708498685, "hint_id": "modal-synthesis-df56331bcaf55a37", "priority": 0.679055520231, "reconstruction_loss": 0.679055520231, "sample_id": "us-code-42-12782.-01f3026e32e90a63"}`
- `program-1638cb5c5e93eebc`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9ebb066b8b3ff238` score `0.991612`
  loss: `autoencoder_residual_cluster` = `0.463044233327`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-31-776-b3c3f6b94f08ad3f, us-code-10-136a-498d8d89076e3d31, us-code-48-1642.-f7d17eb875857fae, us-code-36-152503-bfe1907e963f1c6c`
  evidence: `{"cosine_similarity": -0.159168950247, "hint_id": "modal-synthesis-0365fc09d3defd0f", "priority": 0.489302894062, "reconstruction_loss": 0.489302894062, "sample_id": "us-code-10-136a-498d8d89076e3d31"}`
  evidence: `{"cosine_similarity": -0.102539412398, "hint_id": "modal-synthesis-1ad71539dae39df9", "priority": 0.541111466075, "reconstruction_loss": 0.541111466075, "sample_id": "us-code-31-776-b3c3f6b94f08ad3f"}`
  evidence: `{"cosine_similarity": -0.21473217586, "hint_id": "modal-synthesis-56986a2c5d55888a", "priority": 0.474690805484, "reconstruction_loss": 0.474690805484, "sample_id": "us-code-48-1642.-f7d17eb875857fae"}`
  evidence: `{"cosine_similarity": 0.170119487474, "hint_id": "modal-synthesis-c1d104028dd77d9c", "priority": 0.347071767685, "reconstruction_loss": 0.347071767685, "sample_id": "us-code-36-152503-bfe1907e963f1c6c"}`
- `program-7d0d1e5c4c5c55bd`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9ebb066b8b3ff238` score `0.991033`
  loss: `autoencoder_residual_cluster` = `0.408762968137`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-8-606-f7dcbbfb006072f7, us-code-42-12313.-c1053dbe1a049f60, us-code-25-5396-17291bf2fa3ae3f6, us-code-42-18431.-b72b735d11b81b90`
  evidence: `{"cosine_similarity": -0.377965429924, "hint_id": "modal-synthesis-6d9df178bb0e621d", "priority": 0.444532215549, "reconstruction_loss": 0.444532215549, "sample_id": "us-code-42-12313.-c1053dbe1a049f60"}`
  evidence: `{"cosine_similarity": -0.213090531967, "hint_id": "modal-synthesis-a081838770c11bd9", "priority": 0.484172329703, "reconstruction_loss": 0.484172329703, "sample_id": "us-code-8-606-f7dcbbfb006072f7"}`
  evidence: `{"cosine_similarity": 0.184721895531, "hint_id": "modal-synthesis-e80edafae5d4d06b", "priority": 0.32883346293, "reconstruction_loss": 0.32883346293, "sample_id": "us-code-42-18431.-b72b735d11b81b90"}`
  evidence: `{"cosine_similarity": -0.054520392314, "hint_id": "modal-synthesis-eb2d1b8f2afe16ac", "priority": 0.377513864366, "reconstruction_loss": 0.377513864366, "sample_id": "us-code-25-5396-17291bf2fa3ae3f6"}`
