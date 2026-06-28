# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-drain-20260516T155232Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-drain-20260516T155232Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-b4f19a7abd520b1f`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.400829649366`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-25-3741-a5e014ea7f4d1a76, us-code-16-460l-5a-122678c241494e33`
  evidence: `{"frame_features": ["flogic:modal_operator:X", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-158fa7e5edb19f75", "priority": 0.47693849873, "sample_id": "us-code-25-3741-a5e014ea7f4d1a76"}`
  evidence: `{"frame_features": ["flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-6ff59f762b2abbd4", "priority": 0.324720800002, "sample_id": "us-code-16-460l-5a-122678c241494e33"}`
- `program-ba3115c84fd35339`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.400829649366`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-3741-a5e014ea7f4d1a76, us-code-16-460l-5a-122678c241494e33`
  evidence: `{"cosine_similarity": 0.183050810624, "hint_id": "modal-synthesis-d2e408c862612d0f", "priority": 0.47693849873, "reconstruction_loss": 0.47693849873, "sample_id": "us-code-25-3741-a5e014ea7f4d1a76", "top_embedding_features": ["cue:temporal:X:after", "flogic:modal_operator:X", "family:conditional_normative:1", "lemma:general", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing", "lemma:chapter"]}`
  evidence: `{"cosine_similarity": -0.109436403253, "hint_id": "modal-synthesis-e83d3367f2216693", "priority": 0.324720800002, "reconstruction_loss": 0.324720800002, "sample_id": "us-code-16-460l-5a-122678c241494e33", "top_embedding_features": ["lemma:available", "lemma:use", "lemma:water", "lemma:b", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing", "lemma:chapter"]}`
- `program-2004d603274fed93`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.379946158313`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-22-279a-d93c50023668d543, us-code-47-925.-235a16e625780e2e`
  evidence: `{"frame_features": ["flogic:modal_operator:P", "flogic:predicate:pub", "flogic:predicate:section_pub"], "hint_id": "modal-synthesis-3d64aced30c49a8c", "priority": 0.615953834102, "sample_id": "us-code-22-279a-d93c50023668d543"}`
  evidence: `{"frame_features": ["flogic:modal_operator:X"], "hint_id": "modal-synthesis-fc708292d5943582", "priority": 0.143938482524, "sample_id": "us-code-47-925.-235a16e625780e2e"}`
- `program-ddb9d4f3988474d8`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.379946158313`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-22-279a-d93c50023668d543, us-code-47-925.-235a16e625780e2e`
  evidence: `{"cosine_similarity": 0.854732842727, "hint_id": "modal-synthesis-cafd5d1dbdc59fa1", "priority": 0.143938482524, "reconstruction_loss": 0.143938482524, "sample_id": "us-code-47-925.-235a16e625780e2e", "top_embedding_features": ["cue:conditional_normative:O|:provided that", "cue:deontic:O:required", "cue:temporal:X:after", "flogic:modal_operator:X", "lemma:act", "lemma:congress", "lemma:definition", "lemma:e"]}`
  evidence: `{"cosine_similarity": -0.199889005754, "hint_id": "modal-synthesis-fc530cdd7a537d00", "priority": 0.615953834102, "reconstruction_loss": 0.615953834102, "sample_id": "us-code-22-279a-d93c50023668d543", "top_embedding_features": ["cue:conditional_normative:O|:except", "cue:deontic:P:may", "flogic:modal_operator:P", "flogic:predicate:pub", "flogic:predicate:section_pub", "lemma:agriculture", "lemma:amendments", "lemma:code"]}`
