# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-e00878e40532c3ac`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e00878e40532c3ac` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.434763335266`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-51-70710.-12fcc705389b92d3, us-code-22-6065-b5294523fa516c12, us-code-49-31145.-cb5988a31468ff54, us-code-49-49103.-4d730eb4e74ab8c0`
  evidence: `{"cosine_similarity": -0.615278274427, "hint_id": "modal-synthesis-1dbcb3aefcce9444", "priority": 0.739540963442, "reconstruction_loss": 0.739540963442, "sample_id": "us-code-51-70710.-12fcc705389b92d3"}`
  evidence: `{"cosine_similarity": 0.460730759924, "hint_id": "modal-synthesis-b834d3bc39f83127", "priority": 0.199887713775, "reconstruction_loss": 0.199887713775, "sample_id": "us-code-49-49103.-4d730eb4e74ab8c0"}`
  evidence: `{"cosine_similarity": -0.618679093647, "hint_id": "modal-synthesis-bae62a28f9619314", "priority": 0.534201106079, "reconstruction_loss": 0.534201106079, "sample_id": "us-code-22-6065-b5294523fa516c12"}`
  evidence: `{"cosine_similarity": -0.058278976891, "hint_id": "modal-synthesis-d4a744fd5f55ab40", "priority": 0.265423557767, "reconstruction_loss": 0.265423557767, "sample_id": "us-code-49-31145.-cb5988a31468ff54"}`
