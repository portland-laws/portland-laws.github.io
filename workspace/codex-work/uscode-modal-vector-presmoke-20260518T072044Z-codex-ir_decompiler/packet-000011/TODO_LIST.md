# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-presmoke-20260518T072044Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-presmoke-20260518T072044Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-73af83db57778d92`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-73af83db57778d92` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.533484519987`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-3032a.-5cf2d7da70e73c39, us-code-29-557-bf030a72c81917fb, us-code-33-3705-03ff1c0656654ca1, us-code-16-666-44f7afdbf1e6b0bf`
  evidence: `{"cosine_similarity": -0.057519312701, "hint_id": "modal-synthesis-0f7cdce7c2290936", "priority": 0.664814243684, "reconstruction_loss": 0.664814243684, "sample_id": "us-code-42-3032a.-5cf2d7da70e73c39"}`
  evidence: `{"cosine_similarity": 0.651605649325, "hint_id": "modal-synthesis-5925539560855f1e", "priority": 0.306522000749, "reconstruction_loss": 0.306522000749, "sample_id": "us-code-16-666-44f7afdbf1e6b0bf"}`
  evidence: `{"cosine_similarity": 0.089613988735, "hint_id": "modal-synthesis-a872024b3e68a3c8", "priority": 0.612660810539, "reconstruction_loss": 0.612660810539, "sample_id": "us-code-29-557-bf030a72c81917fb"}`
  evidence: `{"cosine_similarity": 0.009812741834, "hint_id": "modal-synthesis-be1c66166013a0f0", "priority": 0.549941024976, "reconstruction_loss": 0.549941024976, "sample_id": "us-code-33-3705-03ff1c0656654ca1"}`
