# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-0171995e3313be82`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.0942413185`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-28-1409-9ea1a3d3a9afc1e0, us-code-20-1161r-9af5e02512a2252b, us-code-31-3327-bafefcf1f81b20c3`
  evidence: `{"family_margin": -0.981633771742, "hint_id": "modal-synthesis-237900d841544f90", "predicted_family": "temporal", "priority": 1.131633771742, "sample_id": "us-code-28-1409-9ea1a3d3a9afc1e0", "target_family": "frame"}`
  evidence: `{"family_margin": -0.970339235422, "hint_id": "modal-synthesis-42a20cb9ef367bae", "predicted_family": "deontic", "priority": 1.120339235422, "sample_id": "us-code-20-1161r-9af5e02512a2252b", "target_family": "frame"}`
  evidence: `{"family_margin": -0.880750948337, "hint_id": "modal-synthesis-85c65a7d89a6e913", "predicted_family": "deontic", "priority": 1.030750948337, "sample_id": "us-code-31-3327-bafefcf1f81b20c3", "target_family": "frame"}`
