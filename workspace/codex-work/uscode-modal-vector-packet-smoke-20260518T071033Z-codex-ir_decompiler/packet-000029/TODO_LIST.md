# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-d5857c29aac6fa3c`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d5857c29aac6fa3c` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.413968904391`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-22-1475g-20df64b94508657f, us-code-10-2410p-5916881502e308ce, us-code-15-77g-c4e632c18f2972f9, us-code-16-1826h-3724c890f5738a7c`
  evidence: `{"cosine_similarity": -0.247621732361, "hint_id": "modal-synthesis-584c557ee0ef13e8", "priority": 0.537430590272, "reconstruction_loss": 0.537430590272, "sample_id": "us-code-10-2410p-5916881502e308ce"}`
  evidence: `{"cosine_similarity": -0.388964454925, "hint_id": "modal-synthesis-99b03e1f3918b659", "priority": 0.577816666617, "reconstruction_loss": 0.577816666617, "sample_id": "us-code-22-1475g-20df64b94508657f"}`
  evidence: `{"cosine_similarity": 0.554263323594, "hint_id": "modal-synthesis-bb7c93212bacd402", "priority": 0.220034375646, "reconstruction_loss": 0.220034375646, "sample_id": "us-code-16-1826h-3724c890f5738a7c"}`
  evidence: `{"cosine_similarity": 0.021117124708, "hint_id": "modal-synthesis-f7687bcf6331f0f6", "priority": 0.320593985028, "reconstruction_loss": 0.320593985028, "sample_id": "us-code-15-77g-c4e632c18f2972f9"}`
