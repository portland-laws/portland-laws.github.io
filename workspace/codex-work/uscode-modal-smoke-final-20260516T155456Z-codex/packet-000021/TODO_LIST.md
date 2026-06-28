# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-76d3142c9d1000f3`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.051055697121`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-18-2386-91b9795f9b9a4e53, us-code-10-2723-3711a965e1107f6a`
  evidence: `{"family_margin": -0.905148235645, "hint_id": "modal-synthesis-380b61b8340f4861", "predicted_family": "temporal", "priority": 1.055148235645, "sample_id": "us-code-18-2386-91b9795f9b9a4e53", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.896963158598, "hint_id": "modal-synthesis-fe6bc931a113eb26", "predicted_family": "deontic", "priority": 1.046963158598, "sample_id": "us-code-10-2723-3711a965e1107f6a", "target_family": "temporal"}`
- `program-53780f2241b4ac99`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  loss: `autoencoder_residual_cluster` = `0.952788559172`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-10-2723-3711a965e1107f6a, us-code-18-2386-91b9795f9b9a4e53`
  evidence: `{"family_margin": -0.905148235645, "hint_id": "modal-synthesis-4024a8c3c76d9b16", "predicted_family": "temporal", "priority": 0.952574127766, "sample_id": "us-code-18-2386-91b9795f9b9a4e53", "target_family": "deontic", "target_probability": 0.047425872234}`
  evidence: `{"family_margin": -0.896963158598, "hint_id": "modal-synthesis-adb9239bf957df9e", "predicted_family": "deontic", "priority": 0.953002990578, "sample_id": "us-code-10-2723-3711a965e1107f6a", "target_family": "temporal", "target_probability": 0.046997009422}`
- `program-316fc5445084dbbc`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.349545567016`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-10-2723-3711a965e1107f6a, us-code-18-2386-91b9795f9b9a4e53`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D"], "hint_id": "modal-synthesis-0b25aa7f8eac9b84", "priority": 0.378615178487, "sample_id": "us-code-10-2723-3711a965e1107f6a"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"], "hint_id": "modal-synthesis-f82b93597b008e48", "priority": 0.320475955545, "sample_id": "us-code-18-2386-91b9795f9b9a4e53"}`
- `program-3975dd6339bc7124`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.349545567016`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-10-2723-3711a965e1107f6a, us-code-18-2386-91b9795f9b9a4e53`
  evidence: `{"cosine_similarity": 0.143039398796, "hint_id": "modal-synthesis-766acd94cee6680a", "priority": 0.320475955545, "reconstruction_loss": 0.320475955545, "sample_id": "us-code-18-2386-91b9795f9b9a4e53", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"]}`
  evidence: `{"cosine_similarity": -0.201774883902, "hint_id": "modal-synthesis-9d0b30401a2a5de3", "priority": 0.378615178487, "reconstruction_loss": 0.378615178487, "sample_id": "us-code-10-2723-3711a965e1107f6a", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D"]}`
