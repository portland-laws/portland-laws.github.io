# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-a026ae9976076080`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a026ae9976076080` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.380853406298`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-33-33-4bccb35c29027106, us-code-26-1286-48f398ab3ebddca4, us-code-12-1148a-4-638b1a5c78baa5c9, us-code-16-544p-cb1fddf2f6ece7ed`
  evidence: `{"cosine_similarity": 0.087863559283, "hint_id": "modal-synthesis-9e6240d4e64383bf", "priority": 0.428801459759, "reconstruction_loss": 0.428801459759, "sample_id": "us-code-26-1286-48f398ab3ebddca4"}`
  evidence: `{"cosine_similarity": -0.204631417015, "hint_id": "modal-synthesis-a16d6db1fd7eef1b", "priority": 0.584160617304, "reconstruction_loss": 0.584160617304, "sample_id": "us-code-33-33-4bccb35c29027106"}`
  evidence: `{"cosine_similarity": 0.328779036858, "hint_id": "modal-synthesis-a46757a2d7b523c5", "priority": 0.247817126049, "reconstruction_loss": 0.247817126049, "sample_id": "us-code-16-544p-cb1fddf2f6ece7ed"}`
  evidence: `{"cosine_similarity": 0.299124017363, "hint_id": "modal-synthesis-f1d204a1b223549a", "priority": 0.262634422081, "reconstruction_loss": 0.262634422081, "sample_id": "us-code-12-1148a-4-638b1a5c78baa5c9"}`
