# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-20260516T154900Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-20260516T154900Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `program-957c34463225bbb8`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `0.97230403357`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-299b-eda60092171769d9, us-code-18-3013-7473c2b440770471`
  evidence: `{"family_margin": -0.654174848239, "hint_id": "modal-synthesis-b0d926c3e310b5ad", "predicted_family": "conditional_normative", "priority": 0.804174848239, "sample_id": "us-code-18-3013-7473c2b440770471", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.990433218902, "hint_id": "modal-synthesis-bbdcb9bb8552f433", "predicted_family": "temporal", "priority": 1.140433218902, "sample_id": "us-code-42-299b-eda60092171769d9", "target_family": "frame"}`
- `program-a109045024d63b07`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  loss: `autoencoder_residual_cluster` = `0.948353056146`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-42-299b-eda60092171769d9, us-code-18-3013-7473c2b440770471`
  evidence: `{"family_margin": -0.654174848239, "hint_id": "modal-synthesis-586b2a1f928fd38b", "predicted_family": "conditional_normative", "priority": 0.897610094808, "sample_id": "us-code-18-3013-7473c2b440770471", "target_family": "deontic", "target_probability": 0.102389905192}`
  evidence: `{"family_margin": -0.990433218902, "hint_id": "modal-synthesis-97818b52e4c94d64", "predicted_family": "temporal", "priority": 0.999096017484, "sample_id": "us-code-42-299b-eda60092171769d9", "target_family": "frame", "target_probability": 0.000903982516}`
- `program-3b1317be205b7a2c`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.362079756278`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-18-3013-7473c2b440770471, us-code-42-299b-eda60092171769d9`
  evidence: `{"hint_id": "modal-synthesis-b4f0684f235beec6", "priority": 0.5203984572, "sample_id": "us-code-18-3013-7473c2b440770471"}`
  evidence: `{"hint_id": "modal-synthesis-d4ebf802975a4d94", "priority": 0.203761055357, "sample_id": "us-code-42-299b-eda60092171769d9"}`
- `program-751d235d993c73cc`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.362079756278`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-18-3013-7473c2b440770471, us-code-42-299b-eda60092171769d9`
  evidence: `{"cosine_similarity": 0.303698358893, "hint_id": "modal-synthesis-92ac8b5b47c4f1c4", "priority": 0.203761055357, "reconstruction_loss": 0.203761055357, "sample_id": "us-code-42-299b-eda60092171769d9"}`
  evidence: `{"cosine_similarity": -0.318405199588, "hint_id": "modal-synthesis-b4b9432aee9f6aae", "priority": 0.5203984572, "reconstruction_loss": 0.5203984572, "sample_id": "us-code-18-3013-7473c2b440770471"}`
