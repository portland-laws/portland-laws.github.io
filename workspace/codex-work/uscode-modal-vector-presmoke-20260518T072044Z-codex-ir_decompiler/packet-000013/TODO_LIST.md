# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-presmoke-20260518T072044Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-presmoke-20260518T072044Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-2e9079bda751bdc9`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2e9079bda751bdc9` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.471144909826`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-2-1869-7375b527576801fb, us-code-7-2242b-7df2adee0c5f0d2e, us-code-10-246-dbcc3c995876961f, us-code-42-2000a-0766e54fdbc8e842`
  evidence: `{"cosine_similarity": 0.142248294992, "hint_id": "modal-synthesis-3d3e5aefad034216", "priority": 0.553286513998, "reconstruction_loss": 0.553286513998, "sample_id": "us-code-7-2242b-7df2adee0c5f0d2e"}`
  evidence: `{"cosine_similarity": -0.061252915048, "hint_id": "modal-synthesis-415a954c633a3b43", "priority": 0.233254695712, "reconstruction_loss": 0.233254695712, "sample_id": "us-code-42-2000a-0766e54fdbc8e842"}`
  evidence: `{"cosine_similarity": -0.490850747382, "hint_id": "modal-synthesis-8e2baa9ee502fc30", "priority": 0.654155660621, "reconstruction_loss": 0.654155660621, "sample_id": "us-code-2-1869-7375b527576801fb"}`
  evidence: `{"cosine_similarity": 0.096527780289, "hint_id": "modal-synthesis-d05a0e35008f4d26", "priority": 0.443882768974, "reconstruction_loss": 0.443882768974, "sample_id": "us-code-10-246-dbcc3c995876961f"}`
