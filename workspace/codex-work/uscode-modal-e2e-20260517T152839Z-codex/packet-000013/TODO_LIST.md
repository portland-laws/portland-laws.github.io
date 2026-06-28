# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-6a1f221e39704295`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.045014521712`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-25-2454-8a9220338dcd54a5, us-code-41-6102-e4413b0b94be77ce`
  evidence: `{"family_margin": -0.900882165574, "hint_id": "modal-synthesis-da2cec612ce8fbf9", "predicted_family": "deontic", "priority": 1.050882165574, "sample_id": "us-code-25-2454-8a9220338dcd54a5", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.88914687785, "hint_id": "modal-synthesis-ea7b71a6ee94836f", "predicted_family": "temporal", "priority": 1.03914687785, "sample_id": "us-code-41-6102-e4413b0b94be77ce", "target_family": "alethic"}`
