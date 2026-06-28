# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-3dbf12986307eaf5`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-3dbf12986307eaf5` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.363174639483`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-16-192b-3-812122fc15751c20, us-code-49-22105.-99b5f570b42829b7, us-code-22-262m-ef4ebe45d982a030, us-code-20-80r-3-d88633103946052c`
  evidence: `{"cosine_similarity": -0.6242029832, "hint_id": "modal-synthesis-0a1b6f8ceb8c01fe", "priority": 0.576078774157, "reconstruction_loss": 0.576078774157, "sample_id": "us-code-49-22105.-99b5f570b42829b7"}`
  evidence: `{"cosine_similarity": 0.471851268635, "hint_id": "modal-synthesis-2563fad87ab362b7", "priority": 0.140435256976, "reconstruction_loss": 0.140435256976, "sample_id": "us-code-20-80r-3-d88633103946052c"}`
  evidence: `{"cosine_similarity": 0.644485401012, "hint_id": "modal-synthesis-9c9213a19b275ac6", "priority": 0.148174550588, "reconstruction_loss": 0.148174550588, "sample_id": "us-code-22-262m-ef4ebe45d982a030"}`
  evidence: `{"cosine_similarity": 0.101617649234, "hint_id": "modal-synthesis-d9ed819d65116a6c", "priority": 0.58800997621, "reconstruction_loss": 0.58800997621, "sample_id": "us-code-16-192b-3-812122fc15751c20"}`
