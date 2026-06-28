# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-20260516T154900Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-20260516T154900Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-a63ee9ad4a308466`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.503480153398`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-19-3911-46b2d5dc09c76062, us-code-51-20161.-90f4bf0dfa214e7d`
  evidence: `{"cosine_similarity": 0.047868850145, "hint_id": "modal-synthesis-189b38a5edc1cbad", "priority": 0.592912505891, "reconstruction_loss": 0.592912505891, "sample_id": "us-code-19-3911-46b2d5dc09c76062", "top_embedding_features": ["cue:conditional_normative:O|:if", "lemma:chapter", "lemma:code", "lemma:edition", "lemma:effect", "lemma:government", "lemma:publishing", "lemma:purpose"]}`
  evidence: `{"cosine_similarity": -0.127701115921, "hint_id": "modal-synthesis-dc74e238d7110de5", "priority": 0.414047800905, "reconstruction_loss": 0.414047800905, "sample_id": "us-code-51-20161.-90f4bf0dfa214e7d", "top_embedding_features": ["lemma:iv", "lemma:revised", "lemma:statutes", "lemma:code", "lemma:purpose", "lemma:states", "lemma:united", "flogic:candidate_ontology_frame:administrative_notice_hearing"]}`
