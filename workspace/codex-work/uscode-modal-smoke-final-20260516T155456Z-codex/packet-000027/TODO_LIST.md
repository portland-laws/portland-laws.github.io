# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-3d6533e87a953fe9`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.523927426798`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-300t.-aaed07240d8c050d, us-code-16-1882-7162f921f0a7085c`
  evidence: `{"cosine_similarity": 0.116707523278, "hint_id": "modal-synthesis-7708e523060d0a60", "priority": 0.425972123547, "reconstruction_loss": 0.425972123547, "sample_id": "us-code-16-1882-7162f921f0a7085c", "top_embedding_features": ["family:alethic:2", "lemma:later", "lemma:state", "lemma:iv", "lemma:known", "lemma:existing", "lemma:june", "lemma:added"]}`
  evidence: `{"cosine_similarity": -0.228023584524, "hint_id": "modal-synthesis-7bee6236f345e5b5", "priority": 0.621882730049, "reconstruction_loss": 0.621882730049, "sample_id": "us-code-42-300t.-aaed07240d8c050d", "top_embedding_features": ["lemma:application", "lemma:appropriations", "lemma:eligible", "lemma:establish", "lemma:iii", "lemma:secretary", "lemma:june", "lemma:determination"]}`
- `program-ef6db7f780ba4b90`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.523927426798`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-300t.-aaed07240d8c050d, us-code-16-1882-7162f921f0a7085c`
  evidence: `{"hint_id": "modal-synthesis-a16fec0fa73bfedd", "priority": 0.425972123547, "sample_id": "us-code-16-1882-7162f921f0a7085c"}`
  evidence: `{"hint_id": "modal-synthesis-bf1b170a3037e565", "priority": 0.621882730049, "sample_id": "us-code-42-300t.-aaed07240d8c050d"}`
- `program-3c8c635e7b37eed0`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.311222147126`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-12-3205-dfa0e74737439e95, us-code-9-307-174540ee55e7b56f`
  evidence: `{"hint_id": "modal-synthesis-419359f2759e28e8", "priority": 0.396669988652, "sample_id": "us-code-12-3205-dfa0e74737439e95"}`
  evidence: `{"frame_features": ["flogic:predicate:pub"], "hint_id": "modal-synthesis-578461b17b5f05fb", "priority": 0.2257743056, "sample_id": "us-code-9-307-174540ee55e7b56f"}`
- `program-d468a646026b5726`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.311222147126`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-12-3205-dfa0e74737439e95, us-code-9-307-174540ee55e7b56f`
  evidence: `{"cosine_similarity": 0.38554548742, "hint_id": "modal-synthesis-9728d4b9778b28fe", "priority": 0.2257743056, "reconstruction_loss": 0.2257743056, "sample_id": "us-code-9-307-174540ee55e7b56f", "top_embedding_features": ["lemma:substituted", "lemma:conflict", "cue:temporal:F:by", "lemma:amendments", "lemma:inserted", "lemma:application", "flogic:predicate:pub", "lemma:amended"]}`
  evidence: `{"cosine_similarity": 0.105902970905, "hint_id": "modal-synthesis-d80982983fa22ec6", "priority": 0.396669988652, "reconstruction_loss": 0.396669988652, "sample_id": "us-code-12-3205-dfa0e74737439e95", "top_embedding_features": ["lemma:assets", "lemma:expiration", "lemma:makes", "lemma:establishment", "lemma:days", "lemma:preceding", "lemma:changes", "cue:deontic:F:prohibited"]}`
