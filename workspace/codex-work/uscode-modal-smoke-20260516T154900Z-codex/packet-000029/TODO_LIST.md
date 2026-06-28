# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-20260516T154900Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-20260516T154900Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-23f6aa41d991657a`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.277973506393`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-28-1346-a5ff9966847c2904, us-code-6-316-d630144826388409`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:conditional_normative", "flogic:modal_family:deontic", "flogic:modal_family:temporal"], "hint_id": "modal-synthesis-a5c60eeaececcf4c", "priority": 0.15759370823, "sample_id": "us-code-6-316-d630144826388409"}`
  evidence: `{"hint_id": "modal-synthesis-b93760d6b3730136", "priority": 0.398353304555, "sample_id": "us-code-28-1346-a5ff9966847c2904"}`
- `program-2f7c17e6b9fb2166`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.277973506393`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-28-1346-a5ff9966847c2904, us-code-6-316-d630144826388409`
  evidence: `{"cosine_similarity": 0.049288125528, "hint_id": "modal-synthesis-2dd92cfe76add99d", "priority": 0.398353304555, "reconstruction_loss": 0.398353304555, "sample_id": "us-code-28-1346-a5ff9966847c2904", "top_embedding_features": ["lemma:law", "lemma:prior", "lemma:contained", "lemma:department", "lemma:entered", "lemma:granting", "lemma:party", "lemma:person"]}`
  evidence: `{"cosine_similarity": 0.465167923409, "hint_id": "modal-synthesis-a3a765611889fbdb", "priority": 0.15759370823, "reconstruction_loss": 0.15759370823, "sample_id": "us-code-6-316-d630144826388409", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:conditional_normative", "flogic:modal_family:deontic", "flogic:modal_family:temporal"]}`
