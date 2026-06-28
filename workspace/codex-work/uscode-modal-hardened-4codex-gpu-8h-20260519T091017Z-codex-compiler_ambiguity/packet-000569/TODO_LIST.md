# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-cc1244899492db9e`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->frame","deontic->epistemic","frame->conditional_normative"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-cc1244899492db9e` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.914101520182`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-33-2716-0a535e176856ddc9, us-code-48-1574.-f9081ded4aa34275, us-code-22-262p-4b-03ebeee53c8b50cd`
  evidence: `{"family_margin": -0.873489298146, "hint_id": "modal-synthesis-369909f52b1c28bc", "predicted_family": "alethic", "priority": 1.023489298146, "sample_id": "us-code-48-1574.-f9081ded4aa34275", "target_family": "frame"}`
  evidence: `{"family_margin": -0.996675378384, "hint_id": "modal-synthesis-7a422ed6786e3304", "predicted_family": "frame", "priority": 1.146675378384, "sample_id": "us-code-33-2716-0a535e176856ddc9", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.422139884017, "hint_id": "modal-synthesis-e74bc2f94c39864f", "predicted_family": "deontic", "priority": 0.572139884017, "sample_id": "us-code-22-262p-4b-03ebeee53c8b50cd", "target_family": "epistemic"}`
- `program-17a05a99670d1ae4`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->conditional_normative","deontic->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-cc1244899492db9e` score `0.978664`
  loss: `autoencoder_residual_cluster` = `0.360329183981`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-15-6104-8fef2f81532f25c4, us-code-7-2158-a09f86abd58a5b26, us-code-22-6592-6a5fd41e31cf2f8d`
  evidence: `{"family_margin": -0.421626693366, "hint_id": "modal-synthesis-103504ece24b2a0c", "predicted_family": "deontic", "priority": 0.571626693366, "sample_id": "us-code-15-6104-8fef2f81532f25c4", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.209360858578, "hint_id": "modal-synthesis-2beb52d6dbab6891", "predicted_family": "deontic", "priority": 0.359360858578, "sample_id": "us-code-7-2158-a09f86abd58a5b26", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-9dfdde9030854417", "predicted_family": "deontic", "priority": 0.15, "sample_id": "us-code-22-6592-6a5fd41e31cf2f8d", "target_family": "conditional_normative"}`
