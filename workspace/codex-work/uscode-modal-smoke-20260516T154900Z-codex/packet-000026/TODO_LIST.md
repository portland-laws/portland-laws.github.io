# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-20260516T154900Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-20260516T154900Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-2b218e0f33fc0753`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.474298599203`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-15-1803-e03f1071c51991cb, us-code-30-934-7dc5c92d73d218b3`
  evidence: `{"cosine_similarity": -0.365412902866, "hint_id": "modal-synthesis-302cb42064cf22e0", "priority": 0.885734924866, "reconstruction_loss": 0.885734924866, "sample_id": "us-code-15-1803-e03f1071c51991cb", "top_embedding_features": ["cue:conditional_normative:O|:except", "cue:deontic:O:shall", "cue:frame:Frame:is a", "cue:temporal:F:by", "family:frame:1", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits"]}`
  evidence: `{"cosine_similarity": 0.748425376801, "hint_id": "modal-synthesis-d0e22c88b6b0796d", "priority": 0.06286227354, "reconstruction_loss": 0.06286227354, "sample_id": "us-code-30-934-7dc5c92d73d218b3", "top_embedding_features": ["cue:conditional_normative:O|:except", "cue:deontic:O:shall", "cue:temporal:F:by", "family:frame:1", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing"]}`
- `program-4a3e9ee43434fc30`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.474298599203`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-15-1803-e03f1071c51991cb, us-code-30-934-7dc5c92d73d218b3`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits"], "hint_id": "modal-synthesis-5daec858e3d9a936", "priority": 0.885734924866, "sample_id": "us-code-15-1803-e03f1071c51991cb"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-829dd7387cd64e64", "priority": 0.06286227354, "sample_id": "us-code-30-934-7dc5c92d73d218b3"}`
