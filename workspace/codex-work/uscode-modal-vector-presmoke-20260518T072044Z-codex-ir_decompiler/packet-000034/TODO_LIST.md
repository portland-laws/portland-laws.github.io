# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-presmoke-20260518T072044Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-presmoke-20260518T072044Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-427ac509c32fac66`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-427ac509c32fac66` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.471382199465`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-50-213.-b38307b371a573c8, us-code-25-712d-21dfbbe4ca8c836d, us-code-22-286ee-6742eff5bf2ba235, us-code-20-18-cd9a248f07f46dcf`
  evidence: `{"cosine_similarity": -0.248449075303, "hint_id": "modal-synthesis-5a8132142edcb13a", "priority": 0.412087752021, "reconstruction_loss": 0.412087752021, "sample_id": "us-code-22-286ee-6742eff5bf2ba235"}`
  evidence: `{"cosine_similarity": -0.014383590963, "hint_id": "modal-synthesis-826b3aee54a23aad", "priority": 0.53893448036, "reconstruction_loss": 0.53893448036, "sample_id": "us-code-25-712d-21dfbbe4ca8c836d"}`
  evidence: `{"cosine_similarity": -0.013895991369, "hint_id": "modal-synthesis-83500861d5652129", "priority": 0.550212006359, "reconstruction_loss": 0.550212006359, "sample_id": "us-code-50-213.-b38307b371a573c8"}`
  evidence: `{"cosine_similarity": 0.469064169429, "hint_id": "modal-synthesis-948129f30b25bf0e", "priority": 0.384294559119, "reconstruction_loss": 0.384294559119, "sample_id": "us-code-20-18-cd9a248f07f46dcf"}`
