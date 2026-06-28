# packet-000011

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000011/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000011/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000011-20260518_081116

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-619419d5c26b4d65` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-619419d5c26b4d65` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.120645783701, "hint_id": "modal-synthesis-75d71781003c27fc", "priority": 0.491150515948, "reconstruction_loss": 0.491150515948, "sample_id": "us-code-16-3604-4d85bd59734f753e"}`
  evidence: `{"cosine_similarity": -0.586183867379, "hint_id": "modal-synthesis-b25a3f6f245357f1", "priority": 0.708546951254, "reconstruction_loss": 0.708546951254, "sample_id": "us-code-5-8133-e9163264dc0fc8b4"}`
  evidence: `{"cosine_similarity": 0.246772445476, "hint_id": "modal-synthesis-b54f12c649939b2a", "priority": 0.490137190505, "reconstruction_loss": 0.490137190505, "sample_id": "us-code-49-30503.-e89d7a8e6f1b350f"}`
  evidence: `{"cosine_similarity": -0.210753165567, "hint_id": "modal-synthesis-d02541d4fef66151", "priority": 0.749948105531, "reconstruction_loss": 0.749948105531, "sample_id": "us-code-42-3797q.-5f8a67b0c6b18ce1"}`
- `program-2ec7ad5ddbc85db1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-619419d5c26b4d65` score `0.99471`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.750288765848, "hint_id": "modal-synthesis-369f0cf870d3ef52", "priority": 0.174856052655, "reconstruction_loss": 0.174856052655, "sample_id": "us-code-6-124m-1-9cf7c28c05e73fda"}`
  evidence: `{"cosine_similarity": 0.316940066664, "hint_id": "modal-synthesis-4f58835a086acdcc", "priority": 0.354134068165, "reconstruction_loss": 0.354134068165, "sample_id": "us-code-49-42308.-b300fc5613beb023"}`
  evidence: `{"cosine_similarity": 0.835226787794, "hint_id": "modal-synthesis-9a5a87bb4876b7b8", "priority": 0.112591357235, "reconstruction_loss": 0.112591357235, "sample_id": "us-code-2-2232-d2b7eed159c634a0"}`
  evidence: `{"cosine_similarity": -0.091728341848, "hint_id": "modal-synthesis-b89d5ffb9570f185", "priority": 0.420996524568, "reconstruction_loss": 0.420996524568, "sample_id": "us-code-36-200303-0d4486b2d890b2a6"}`
- `program-7edf9b76a78e1976` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-619419d5c26b4d65` score `0.994454`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.039442956623, "hint_id": "modal-synthesis-2550820cd34fdf9a", "priority": 0.451140873489, "reconstruction_loss": 0.451140873489, "sample_id": "us-code-42-3797e.-40aa49fef08689a6"}`
  evidence: `{"cosine_similarity": 0.29981088683, "hint_id": "modal-synthesis-289023f9e1911c6c", "priority": 0.40402867776, "reconstruction_loss": 0.40402867776, "sample_id": "us-code-54-101913.-045b8b30e25d1f3b"}`
  evidence: `{"cosine_similarity": 0.043158683, "hint_id": "modal-synthesis-5c561289a27e3c7f", "priority": 0.364090923365, "reconstruction_loss": 0.364090923365, "sample_id": "us-code-20-7703-ecd421e19a6cb135"}`
  evidence: `{"cosine_similarity": 0.164975903288, "hint_id": "modal-synthesis-6c7103d4b6b03c01", "priority": 0.277066388472, "reconstruction_loss": 0.277066388472, "sample_id": "us-code-36-40702-2897adc821c7f68d"}`

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
- `program-619419d5c26b4d65`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-619419d5c26b4d65` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.60994569081`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-3797q.-5f8a67b0c6b18ce1, us-code-5-8133-e9163264dc0fc8b4, us-code-16-3604-4d85bd59734f753e, us-code-49-30503.-e89d7a8e6f1b350f`
  evidence: `{"cosine_similarity": 0.120645783701, "hint_id": "modal-synthesis-75d71781003c27fc", "priority": 0.491150515948, "reconstruction_loss": 0.491150515948, "sample_id": "us-code-16-3604-4d85bd59734f753e"}`
  evidence: `{"cosine_similarity": -0.586183867379, "hint_id": "modal-synthesis-b25a3f6f245357f1", "priority": 0.708546951254, "reconstruction_loss": 0.708546951254, "sample_id": "us-code-5-8133-e9163264dc0fc8b4"}`
  evidence: `{"cosine_similarity": 0.246772445476, "hint_id": "modal-synthesis-b54f12c649939b2a", "priority": 0.490137190505, "reconstruction_loss": 0.490137190505, "sample_id": "us-code-49-30503.-e89d7a8e6f1b350f"}`
  evidence: `{"cosine_similarity": -0.210753165567, "hint_id": "modal-synthesis-d02541d4fef66151", "priority": 0.749948105531, "reconstruction_loss": 0.749948105531, "sample_id": "us-code-42-3797q.-5f8a67b0c6b18ce1"}`
- `program-2ec7ad5ddbc85db1`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-619419d5c26b4d65` score `0.99471`
  loss: `autoencoder_residual_cluster` = `0.265644500656`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-36-200303-0d4486b2d890b2a6, us-code-49-42308.-b300fc5613beb023, us-code-6-124m-1-9cf7c28c05e73fda, us-code-2-2232-d2b7eed159c634a0`
  evidence: `{"cosine_similarity": 0.750288765848, "hint_id": "modal-synthesis-369f0cf870d3ef52", "priority": 0.174856052655, "reconstruction_loss": 0.174856052655, "sample_id": "us-code-6-124m-1-9cf7c28c05e73fda"}`
  evidence: `{"cosine_similarity": 0.316940066664, "hint_id": "modal-synthesis-4f58835a086acdcc", "priority": 0.354134068165, "reconstruction_loss": 0.354134068165, "sample_id": "us-code-49-42308.-b300fc5613beb023"}`
  evidence: `{"cosine_similarity": 0.835226787794, "hint_id": "modal-synthesis-9a5a87bb4876b7b8", "priority": 0.112591357235, "reconstruction_loss": 0.112591357235, "sample_id": "us-code-2-2232-d2b7eed159c634a0"}`
  evidence: `{"cosine_similarity": -0.091728341848, "hint_id": "modal-synthesis-b89d5ffb9570f185", "priority": 0.420996524568, "reconstruction_loss": 0.420996524568, "sample_id": "us-code-36-200303-0d4486b2d890b2a6"}`
- `program-7edf9b76a78e1976`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-619419d5c26b4d65` score `0.994454`
  loss: `autoencoder_residual_cluster` = `0.374081715772`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-3797e.-40aa49fef08689a6, us-code-54-101913.-045b8b30e25d1f3b, us-code-20-7703-ecd421e19a6cb135, us-code-36-40702-2897adc821c7f68d`
  evidence: `{"cosine_similarity": 0.039442956623, "hint_id": "modal-synthesis-2550820cd34fdf9a", "priority": 0.451140873489, "reconstruction_loss": 0.451140873489, "sample_id": "us-code-42-3797e.-40aa49fef08689a6"}`
  evidence: `{"cosine_similarity": 0.29981088683, "hint_id": "modal-synthesis-289023f9e1911c6c", "priority": 0.40402867776, "reconstruction_loss": 0.40402867776, "sample_id": "us-code-54-101913.-045b8b30e25d1f3b"}`
  evidence: `{"cosine_similarity": 0.043158683, "hint_id": "modal-synthesis-5c561289a27e3c7f", "priority": 0.364090923365, "reconstruction_loss": 0.364090923365, "sample_id": "us-code-20-7703-ecd421e19a6cb135"}`
  evidence: `{"cosine_similarity": 0.164975903288, "hint_id": "modal-synthesis-6c7103d4b6b03c01", "priority": 0.277066388472, "reconstruction_loss": 0.277066388472, "sample_id": "us-code-36-40702-2897adc821c7f68d"}`
