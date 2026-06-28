# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-33bb12221a2e4bc6`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.374383914706`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-47-208.-bbe14e3800c522d1, us-code-26-45E-bd16b29c97210cf4`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"], "hint_id": "modal-synthesis-4a8d2a1bf508a889", "priority": 0.432772191864, "sample_id": "us-code-47-208.-bbe14e3800c522d1"}`
  evidence: `{"hint_id": "modal-synthesis-557a9803eee8dc64", "priority": 0.315995637547, "sample_id": "us-code-26-45E-bd16b29c97210cf4"}`
- `program-503e2be2fe62a3ee`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.374383914706`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-47-208.-bbe14e3800c522d1, us-code-26-45E-bd16b29c97210cf4`
  evidence: `{"cosine_similarity": 0.167001735891, "hint_id": "modal-synthesis-232eeaf18866bb88", "priority": 0.315995637547, "reconstruction_loss": 0.315995637547, "sample_id": "us-code-26-45E-bd16b29c97210cf4", "top_embedding_features": ["lemma:act", "lemma:date", "lemma:defined", "lemma:effective", "lemma:employees", "lemma:ii", "lemma:member", "lemma:note"]}`
  evidence: `{"cosine_similarity": 0.508660753224, "hint_id": "modal-synthesis-543cb69c8636ef75", "priority": 0.432772191864, "reconstruction_loss": 0.432772191864, "sample_id": "us-code-47-208.-bbe14e3800c522d1", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"]}`
