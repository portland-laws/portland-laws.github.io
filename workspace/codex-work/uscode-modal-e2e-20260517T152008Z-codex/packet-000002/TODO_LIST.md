# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152008Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152008Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-9f73b946ee07dfbe`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.149999560092`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-18-6001-1d3fcd8c228d1a08, us-code-7-9071-d69d5c5ff2fce558`
  evidence: `{"family_margin": -0.999999166354, "hint_id": "modal-synthesis-97a37b9a9f534210", "predicted_family": "deontic", "priority": 1.149999166354, "sample_id": "us-code-7-9071-d69d5c5ff2fce558", "target_family": "frame"}`
  evidence: `{"family_margin": -0.999999953831, "hint_id": "modal-synthesis-9a417a8d5d329206", "predicted_family": "temporal", "priority": 1.149999953831, "sample_id": "us-code-18-6001-1d3fcd8c228d1a08", "target_family": "deontic"}`
