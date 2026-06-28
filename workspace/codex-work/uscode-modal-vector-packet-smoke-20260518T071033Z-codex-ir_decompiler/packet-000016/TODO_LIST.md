# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-da38d1742788a5d7`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-da38d1742788a5d7` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.410356537759`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-1777e-0b43a2e61a68e08c, us-code-43-1761a.-b46ffaeaa2ca048b, us-code-16-470x-6-8425545a27313911, us-code-22-9634-99cf2ae08643766a`
  evidence: `{"cosine_similarity": 0.149262554943, "hint_id": "modal-synthesis-1c02fb543727861f", "priority": 0.34593319452, "reconstruction_loss": 0.34593319452, "sample_id": "us-code-16-470x-6-8425545a27313911"}`
  evidence: `{"cosine_similarity": -0.11522396174, "hint_id": "modal-synthesis-8a3f35778ac159ef", "priority": 0.465811900833, "reconstruction_loss": 0.465811900833, "sample_id": "us-code-43-1761a.-b46ffaeaa2ca048b"}`
  evidence: `{"cosine_similarity": 0.041403044642, "hint_id": "modal-synthesis-bcbda30bfc616adc", "priority": 0.549095692157, "reconstruction_loss": 0.549095692157, "sample_id": "us-code-25-1777e-0b43a2e61a68e08c"}`
  evidence: `{"cosine_similarity": 0.578457803099, "hint_id": "modal-synthesis-de6d39daa2852bad", "priority": 0.280585363528, "reconstruction_loss": 0.280585363528, "sample_id": "us-code-22-9634-99cf2ae08643766a"}`
