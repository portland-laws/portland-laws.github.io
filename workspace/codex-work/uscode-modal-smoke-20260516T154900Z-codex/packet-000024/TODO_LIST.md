# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-20260516T154900Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-20260516T154900Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-43a63cf868b34e95`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.705472566863`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-300t-165b62726b1ad549, us-code-16-709-b9a8bf838e927a34`
  evidence: `{"hint_id": "modal-synthesis-577e0e1931503ee9", "priority": 0.483159116907, "sample_id": "us-code-16-709-b9a8bf838e927a34"}`
  evidence: `{"hint_id": "modal-synthesis-7be9fbeb1fd30dab", "priority": 0.927786016819, "sample_id": "us-code-42-300t-165b62726b1ad549"}`
- `program-ce6fe332f1dcf4de`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.705472566863`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-300t-165b62726b1ad549, us-code-16-709-b9a8bf838e927a34`
  evidence: `{"cosine_similarity": -0.389889207147, "hint_id": "modal-synthesis-847681b442bec597", "priority": 0.927786016819, "reconstruction_loss": 0.927786016819, "sample_id": "us-code-42-300t-165b62726b1ad549"}`
  evidence: `{"cosine_similarity": -0.199575532914, "hint_id": "modal-synthesis-f410fe2a97702908", "priority": 0.483159116907, "reconstruction_loss": 0.483159116907, "sample_id": "us-code-16-709-b9a8bf838e927a34"}`
- `program-ab5ec8c5b2ef5b0b`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  loss: `autoencoder_residual_cluster` = `0.62918610347`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-16-709-b9a8bf838e927a34, us-code-42-300t-165b62726b1ad549`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-6d16b50d4cfc3323", "predicted_family": "temporal", "priority": 0.509017538256, "sample_id": "us-code-42-300t-165b62726b1ad549", "target_family": "deontic", "target_probability": 0.490982461744}`
  evidence: `{"family_margin": -0.430679318188, "hint_id": "modal-synthesis-c2136d807a7d433b", "predicted_family": "temporal", "priority": 0.749354668684, "sample_id": "us-code-16-709-b9a8bf838e927a34", "target_family": "deontic", "target_probability": 0.250645331316}`
- `program-235d549eaa201a32`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `0.365339659094`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-16-709-b9a8bf838e927a34, us-code-42-300t-165b62726b1ad549`
  evidence: `{"family_margin": -0.430679318188, "hint_id": "modal-synthesis-c52d2f086d19df72", "predicted_family": "temporal", "priority": 0.580679318188, "sample_id": "us-code-16-709-b9a8bf838e927a34", "target_family": "deontic"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-eb1b2d584344dda7", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-42-300t-165b62726b1ad549", "target_family": "deontic"}`
