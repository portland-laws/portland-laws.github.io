# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-358b715d28185e14`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.377058950862`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-2-5326-79178d297c7d0e2e, us-code-16-4221-afd641e9d25b51d8`
  evidence: `{"cosine_similarity": 0.065398206681, "hint_id": "modal-synthesis-79702fc90fe1606a", "priority": 0.431941892127, "reconstruction_loss": 0.431941892127, "sample_id": "us-code-2-5326-79178d297c7d0e2e"}`
  evidence: `{"cosine_similarity": 0.403357492019, "hint_id": "modal-synthesis-cc8532fe259ef72c", "priority": 0.322176009597, "reconstruction_loss": 0.322176009597, "sample_id": "us-code-16-4221-afd641e9d25b51d8"}`
- `program-ba9e01f75b592a75`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.377058950862`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-2-5326-79178d297c7d0e2e, us-code-16-4221-afd641e9d25b51d8`
  evidence: `{"hint_id": "modal-synthesis-1d3481b25a54a05f", "priority": 0.322176009597, "sample_id": "us-code-16-4221-afd641e9d25b51d8"}`
  evidence: `{"hint_id": "modal-synthesis-c35e69bda4af89a5", "priority": 0.431941892127, "sample_id": "us-code-2-5326-79178d297c7d0e2e"}`
