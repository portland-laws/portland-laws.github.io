# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-2f2916a70ea31c87`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.37902956407`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-46-12113.-237d8a683c3ef740, us-code-22-2737-53e3f10c5adf9439`
  evidence: `{"hint_id": "modal-synthesis-0bc5ba5280708b92", "priority": 0.233742460424, "sample_id": "us-code-22-2737-53e3f10c5adf9439"}`
  evidence: `{"frame_features": ["flogic:modal_family:conditional_normative", "flogic:modal_family:temporal", "flogic:modal_operator:F", "flogic:modal_operator:O|"], "hint_id": "modal-synthesis-179abcf0419d66a6", "priority": 0.524316667716, "sample_id": "us-code-46-12113.-237d8a683c3ef740"}`
- `program-942612e48015b882`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.37902956407`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-46-12113.-237d8a683c3ef740, us-code-22-2737-53e3f10c5adf9439`
  evidence: `{"cosine_similarity": 0.241702482593, "hint_id": "modal-synthesis-048cadb0d242e37d", "priority": 0.233742460424, "reconstruction_loss": 0.233742460424, "sample_id": "us-code-22-2737-53e3f10c5adf9439", "top_embedding_features": ["lemma:effective", "lemma:ii", "lemma:note", "lemma:set", "lemma:statutory", "lemma:subsidiaries", "lemma:editorial", "lemma:notes"]}`
  evidence: `{"cosine_similarity": -0.232661510782, "hint_id": "modal-synthesis-488de262a313e53d", "priority": 0.524316667716, "reconstruction_loss": 0.524316667716, "sample_id": "us-code-46-12113.-237d8a683c3ef740", "top_embedding_features": ["lemma:paragraph", "cue:conditional_normative:O|:if", "cue:deontic:P:may", "cue:temporal:X:after", "flogic:modal_family:conditional_normative", "flogic:modal_family:temporal", "flogic:modal_operator:F", "flogic:modal_operator:O|"]}`
