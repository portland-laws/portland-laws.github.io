# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-a368a64901e923d5`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.149999370625`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-29-206-845c3642b2f98030, us-code-42-1322.-b26abf2ba9d75d37, us-code-34-40901-d9783f392f578d32`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-90f1a97d3cd15181", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-29-206-845c3642b2f98030", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.99999977493, "hint_id": "modal-synthesis-d5ed52f0c5c5e53f", "predicted_family": "deontic", "priority": 1.14999977493, "sample_id": "us-code-42-1322.-b26abf2ba9d75d37", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.999998336944, "hint_id": "modal-synthesis-decb5da36ff8a149", "predicted_family": "deontic", "priority": 1.149998336944, "sample_id": "us-code-34-40901-d9783f392f578d32", "target_family": "temporal"}`
