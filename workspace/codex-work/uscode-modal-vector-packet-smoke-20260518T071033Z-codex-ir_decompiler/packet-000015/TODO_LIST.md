# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-8ab2b52e08bc9842`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8ab2b52e08bc9842` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.387022676392`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-16-4011-c7a2df8c840edce3, us-code-7-5213-0181b6209c09dd47, us-code-25-458aaa-13-9841567e37933284, us-code-15-144-1321a679e8cdef85`
  evidence: `{"cosine_similarity": 0.011258540027, "hint_id": "modal-synthesis-58a7b994e28f2f84", "priority": 0.391158171391, "reconstruction_loss": 0.391158171391, "sample_id": "us-code-7-5213-0181b6209c09dd47"}`
  evidence: `{"cosine_similarity": -0.131884575213, "hint_id": "modal-synthesis-8cfba8c218b26e40", "priority": 0.418624633672, "reconstruction_loss": 0.418624633672, "sample_id": "us-code-16-4011-c7a2df8c840edce3"}`
  evidence: `{"cosine_similarity": 0.292579019568, "hint_id": "modal-synthesis-a8be05cbc6223423", "priority": 0.357559037967, "reconstruction_loss": 0.357559037967, "sample_id": "us-code-15-144-1321a679e8cdef85"}`
  evidence: `{"cosine_similarity": 0.210800962468, "hint_id": "modal-synthesis-d440710d2b7e60eb", "priority": 0.380748862536, "reconstruction_loss": 0.380748862536, "sample_id": "us-code-25-458aaa-13-9841567e37933284"}`
