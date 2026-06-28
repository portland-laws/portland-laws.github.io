# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-423e226c6324afbb`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.61852230974`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-14-1905-6a693ba4de600b23, us-code-20-5965-8b42ad15e9524286`
  evidence: `{"frame_features": ["flogic:modal_family:temporal", "flogic:modal_operator:F", "flogic:modal_operator:P", "flogic:modal_system:LTL", "flogic:predicate_role:temporal_scope"], "hint_id": "modal-synthesis-620a4ef5ae958e42", "priority": 0.910855735373, "sample_id": "us-code-14-1905-6a693ba4de600b23"}`
  evidence: `{"frame_features": ["flogic:modal_family:conditional_normative", "flogic:modal_family:temporal", "flogic:modal_operator:F"], "hint_id": "modal-synthesis-a49e2ecf9753b7c4", "priority": 0.326188884107, "sample_id": "us-code-20-5965-8b42ad15e9524286"}`
- `program-b48c8c4608daa38c`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.61852230974`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-14-1905-6a693ba4de600b23, us-code-20-5965-8b42ad15e9524286`
  evidence: `{"cosine_similarity": 0.081698321021, "hint_id": "modal-synthesis-c92cf4418dc5a9d6", "priority": 0.326188884107, "reconstruction_loss": 0.326188884107, "sample_id": "us-code-20-5965-8b42ad15e9524286", "top_embedding_features": ["lemma:paragraph", "lemma:year", "cue:conditional_normative:O|:if", "cue:deontic:P:may", "cue:temporal:X:after", "flogic:modal_family:conditional_normative", "flogic:modal_family:temporal", "flogic:modal_operator:F"]}`
  evidence: `{"cosine_similarity": -0.365815776637, "hint_id": "modal-synthesis-c96d85b212e0c4f0", "priority": 0.910855735373, "reconstruction_loss": 0.910855735373, "sample_id": "us-code-14-1905-6a693ba4de600b23", "top_embedding_features": ["cue:deontic:P:may", "cue:temporal:F:by", "cue:temporal:F:within", "flogic:modal_family:temporal", "flogic:modal_operator:F", "flogic:modal_operator:P", "flogic:modal_system:LTL", "flogic:predicate_role:temporal_scope"]}`
- `program-9a70e2620a3b37fc`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.609709967043`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-15923.-0db47438360bf7c8, us-code-16-721-60610bafb76ac1a0`
  evidence: `{"cosine_similarity": -0.154725143157, "hint_id": "modal-synthesis-0e420dcb4f576002", "priority": 0.575041833528, "reconstruction_loss": 0.575041833528, "sample_id": "us-code-16-721-60610bafb76ac1a0", "top_embedding_features": ["cue:deontic:P:may", "flogic:modal_operator:P", "lemma:pub", "family:frame:1", "flogic:interpreted_in_frame:criminal_penalty_enforcement", "flogic:selected_ontology_frame:criminal_penalty_enforcement", "frame:criminal_penalty_enforcement", "lemma:association"]}`
  evidence: `{"cosine_similarity": -0.357580174614, "hint_id": "modal-synthesis-796823c775e8be3e", "priority": 0.644378100558, "reconstruction_loss": 0.644378100558, "sample_id": "us-code-42-15923.-0db47438360bf7c8", "top_embedding_features": ["lemma:pub", "lemma:assessment", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing", "cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement"]}`
- `program-f12acfacde027ee7`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.609709967043`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-15923.-0db47438360bf7c8, us-code-16-721-60610bafb76ac1a0`
  evidence: `{"frame_features": ["flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement"], "hint_id": "modal-synthesis-419ab7a040f32ac6", "priority": 0.644378100558, "sample_id": "us-code-42-15923.-0db47438360bf7c8"}`
  evidence: `{"frame_features": ["flogic:modal_operator:P", "flogic:interpreted_in_frame:criminal_penalty_enforcement", "flogic:selected_ontology_frame:criminal_penalty_enforcement", "frame:criminal_penalty_enforcement"], "hint_id": "modal-synthesis-5de5dbf7b1d11db3", "priority": 0.575041833528, "sample_id": "us-code-16-721-60610bafb76ac1a0"}`
