# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-drain-20260516T155232Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-drain-20260516T155232Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-10729dc60cbbf851`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.284593766102`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-3041 to 3041f.-f7a25e2c39f54090, us-code-42-300j-6b7f0e2ba54bb3d6`
  evidence: `{"cosine_similarity": 0.028037591261, "hint_id": "modal-synthesis-2f0a2fa90b98848f", "priority": 0.270672581433, "reconstruction_loss": 0.270672581433, "sample_id": "us-code-42-300j-6b7f0e2ba54bb3d6"}`
  evidence: `{"cosine_similarity": -0.022409598628, "hint_id": "modal-synthesis-37057e1dd3728df2", "priority": 0.298514950771, "reconstruction_loss": 0.298514950771, "sample_id": "us-code-42-3041 to 3041f.-f7a25e2c39f54090"}`
- `program-df59e89c25109f65`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.284593766102`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-3041 to 3041f.-f7a25e2c39f54090, us-code-42-300j-6b7f0e2ba54bb3d6`
  evidence: `{"hint_id": "modal-synthesis-2949459e506ca2f9", "priority": 0.270672581433, "sample_id": "us-code-42-300j-6b7f0e2ba54bb3d6"}`
  evidence: `{"hint_id": "modal-synthesis-765293ad18f6f8b3", "priority": 0.298514950771, "sample_id": "us-code-42-3041 to 3041f.-f7a25e2c39f54090"}`
