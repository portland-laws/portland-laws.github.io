# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-final-20260516T155456Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-final-20260516T155456Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-429bbec8b81e1287`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  loss: `autoencoder_residual_cluster` = `0.923023302466`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-18-1864-0895435d80f993be, us-code-46-53713.-35b054d30aa10ddc`
  evidence: `{"family_margin": -0.669337638281, "hint_id": "modal-synthesis-84691e1728457dd7", "predicted_family": "conditional_normative", "priority": 0.964929588254, "sample_id": "us-code-18-1864-0895435d80f993be", "target_family": "temporal", "target_probability": 0.035070411746}`
  evidence: `{"family_margin": -0.759550049661, "hint_id": "modal-synthesis-a6e2f4c56a491425", "predicted_family": "temporal", "priority": 0.881117016677, "sample_id": "us-code-46-53713.-35b054d30aa10ddc", "target_family": "deontic", "target_probability": 0.118882983323}`
- `program-454919a69ac82aae`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `0.864443843971`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-46-53713.-35b054d30aa10ddc, us-code-18-1864-0895435d80f993be`
  evidence: `{"family_margin": -0.669337638281, "hint_id": "modal-synthesis-4dd428bfef70a93f", "predicted_family": "conditional_normative", "priority": 0.819337638281, "sample_id": "us-code-18-1864-0895435d80f993be", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.759550049661, "hint_id": "modal-synthesis-c5c108c0f9214be6", "predicted_family": "temporal", "priority": 0.909550049661, "sample_id": "us-code-46-53713.-35b054d30aa10ddc", "target_family": "deontic"}`
- `program-569df8edd804df3c`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.408907495152`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-18-1864-0895435d80f993be, us-code-46-53713.-35b054d30aa10ddc`
  evidence: `{"hint_id": "modal-synthesis-243dafec18d9e9a8", "priority": 0.51773843429, "sample_id": "us-code-18-1864-0895435d80f993be"}`
  evidence: `{"hint_id": "modal-synthesis-831df542b5b3f8d1", "priority": 0.300076556014, "sample_id": "us-code-46-53713.-35b054d30aa10ddc"}`
- `program-f631a6967555155a`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.408907495152`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-18-1864-0895435d80f993be, us-code-46-53713.-35b054d30aa10ddc`
  evidence: `{"cosine_similarity": -0.411539146776, "hint_id": "modal-synthesis-6961db96c9131a68", "priority": 0.51773843429, "reconstruction_loss": 0.51773843429, "sample_id": "us-code-18-1864-0895435d80f993be", "top_embedding_features": ["cue:conditional_normative:O|:if", "lemma:civil", "lemma:costs", "lemma:includes", "lemma:regard", "lemma:remains", "lemma:trip", "family:frame:1"]}`
  evidence: `{"cosine_similarity": 0.272661817671, "hint_id": "modal-synthesis-cb34658af9fda078", "priority": 0.300076556014, "reconstruction_loss": 0.300076556014, "sample_id": "us-code-46-53713.-35b054d30aa10ddc", "top_embedding_features": ["lemma:charge", "lemma:investigating", "lemma:administration", "lemma:administrative", "lemma:derived", "lemma:introductory", "lemma:large", "lemma:legislative"]}`
