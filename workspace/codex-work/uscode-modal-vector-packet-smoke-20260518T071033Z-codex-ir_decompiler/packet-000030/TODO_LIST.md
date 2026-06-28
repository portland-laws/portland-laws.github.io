# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-db7043a6ee35b0f5`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db7043a6ee35b0f5` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.535344388437`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-16042.-619283573cf7c708, us-code-18-3106-74e02e164a46174f, us-code-32-323-a596bbb0bff87650, us-code-34-20928-7d6dcae460c25e72`
  evidence: `{"cosine_similarity": 0.275974774094, "hint_id": "modal-synthesis-1970e3f5f2f75e57", "priority": 0.373357393144, "reconstruction_loss": 0.373357393144, "sample_id": "us-code-34-20928-7d6dcae460c25e72"}`
  evidence: `{"cosine_similarity": -0.258184336438, "hint_id": "modal-synthesis-3b9ff34a34bab521", "priority": 0.685806141366, "reconstruction_loss": 0.685806141366, "sample_id": "us-code-42-16042.-619283573cf7c708"}`
  evidence: `{"cosine_similarity": 0.008844691589, "hint_id": "modal-synthesis-5ac6dcfff16fb79e", "priority": 0.612277833011, "reconstruction_loss": 0.612277833011, "sample_id": "us-code-18-3106-74e02e164a46174f"}`
  evidence: `{"cosine_similarity": -0.056337568366, "hint_id": "modal-synthesis-a94eaa38b67f2e6f", "priority": 0.469936186227, "reconstruction_loss": 0.469936186227, "sample_id": "us-code-32-323-a596bbb0bff87650"}`
