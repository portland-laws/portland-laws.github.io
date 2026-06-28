# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-0a46da1b6c12a2da`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.41795944497`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-48-1807.-2b00a7c8484eaec4, us-code-34-20144-a1f38c368ce05bfe`
  evidence: `{"cosine_similarity": 0.331299038646, "hint_id": "modal-synthesis-1205591ba504df84", "priority": 0.20875790515, "reconstruction_loss": 0.20875790515, "sample_id": "us-code-34-20144-a1f38c368ce05bfe", "top_embedding_features": ["lemma:set", "lemma:chapter", "lemma:code", "lemma:editorial", "lemma:notes", "lemma:section", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement"]}`
  evidence: `{"cosine_similarity": -0.618899958769, "hint_id": "modal-synthesis-ff0277652496ce74", "priority": 0.62716098479, "reconstruction_loss": 0.62716098479, "sample_id": "us-code-48-1807.-2b00a7c8484eaec4", "top_embedding_features": ["lemma:encourage", "lemma:opportunities", "lemma:permanent", "lemma:recruiting", "cue:conditional_normative:O|:provided that", "cue:frame:Frame:part of", "lemma:identify", "lemma:program"]}`
- `program-b300eb260e7d9a18`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.41795944497`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-48-1807.-2b00a7c8484eaec4, us-code-34-20144-a1f38c368ce05bfe`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement"], "hint_id": "modal-synthesis-69d66a8a6010598b", "priority": 0.20875790515, "sample_id": "us-code-34-20144-a1f38c368ce05bfe"}`
  evidence: `{"hint_id": "modal-synthesis-d0ea623a998bb9f8", "priority": 0.62716098479, "sample_id": "us-code-48-1807.-2b00a7c8484eaec4"}`
