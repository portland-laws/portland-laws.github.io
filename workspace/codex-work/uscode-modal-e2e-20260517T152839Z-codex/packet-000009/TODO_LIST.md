# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-00eea260a1b250d5`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.070511937069`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-22-4106-2bec276bc903c601, us-code-26-3134-7d41d03274935de1, us-code-15-78dd-1-18ce21e2386aaaab`
  evidence: `{"family_margin": -0.999954602131, "hint_id": "modal-synthesis-2ee17c503c09e716", "predicted_family": "deontic", "priority": 1.149954602131, "sample_id": "us-code-26-3134-7d41d03274935de1", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.99998705312, "hint_id": "modal-synthesis-6e6699c14ac816f3", "predicted_family": "deontic", "priority": 1.14998705312, "sample_id": "us-code-22-4106-2bec276bc903c601", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.761594155956, "hint_id": "modal-synthesis-e36d48730f9c00be", "predicted_family": "temporal", "priority": 0.911594155956, "sample_id": "us-code-15-78dd-1-18ce21e2386aaaab", "target_family": "deontic"}`
