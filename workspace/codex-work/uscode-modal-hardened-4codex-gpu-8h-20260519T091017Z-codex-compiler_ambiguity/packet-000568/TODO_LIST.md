# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-c51b39bfc0c5043f`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->epistemic","deontic->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-c51b39bfc0c5043f` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.749015810821`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-10-2650-fc88eeb2517632d4, us-code-12-5018-ece54fe9a514c43c, us-code-7-8203-eef8592beaf3bf27`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-72e40a69c4fdd99c", "predicted_family": "deontic", "priority": 0.15, "sample_id": "us-code-7-8203-eef8592beaf3bf27", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.82092512363, "hint_id": "modal-synthesis-a8046d699cc84564", "predicted_family": "alethic", "priority": 0.97092512363, "sample_id": "us-code-12-5018-ece54fe9a514c43c", "target_family": "epistemic"}`
  evidence: `{"family_margin": -0.976122308832, "hint_id": "modal-synthesis-b849570ced4558e1", "predicted_family": "frame", "priority": 1.126122308832, "sample_id": "us-code-10-2650-fc88eeb2517632d4", "target_family": "temporal"}`
- `program-6c7d2601af80f322`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->temporal","temporal->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-c51b39bfc0c5043f` score `0.97274`
  loss: `autoencoder_residual_cluster` = `0.460735210617`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-299b-67436521eac14325, us-code-16-115a-d0babad0261804a7`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-40f818082492500f", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-16-115a-d0babad0261804a7", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.621470421233, "hint_id": "modal-synthesis-f27a521adb7f4c69", "predicted_family": "deontic", "priority": 0.771470421233, "sample_id": "us-code-42-299b-67436521eac14325", "target_family": "temporal"}`
