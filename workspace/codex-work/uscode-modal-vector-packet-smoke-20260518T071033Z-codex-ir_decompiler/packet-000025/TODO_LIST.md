# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-7f665c1cc6a49260`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7f665c1cc6a49260` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.474760173983`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-15-278s-775f3e0c4c0d1e93, us-code-15-1693k-ed185e148b73082c, us-code-15-767-e74000ac94b57e67, us-code-8-1454-45ff849cda8d2cb7`
  evidence: `{"cosine_similarity": -0.144849546185, "hint_id": "modal-synthesis-08326d8486ac981c", "priority": 0.57363258655, "reconstruction_loss": 0.57363258655, "sample_id": "us-code-15-278s-775f3e0c4c0d1e93"}`
  evidence: `{"cosine_similarity": 0.219685328542, "hint_id": "modal-synthesis-233672a2554ae1b1", "priority": 0.398714871338, "reconstruction_loss": 0.398714871338, "sample_id": "us-code-8-1454-45ff849cda8d2cb7"}`
  evidence: `{"cosine_similarity": -0.020881154729, "hint_id": "modal-synthesis-89b0a9b184a8f2ef", "priority": 0.438581418447, "reconstruction_loss": 0.438581418447, "sample_id": "us-code-15-767-e74000ac94b57e67"}`
  evidence: `{"cosine_similarity": 0.333986217437, "hint_id": "modal-synthesis-f4520f6d8e9729a5", "priority": 0.488111819598, "reconstruction_loss": 0.488111819598, "sample_id": "us-code-15-1693k-ed185e148b73082c"}`
