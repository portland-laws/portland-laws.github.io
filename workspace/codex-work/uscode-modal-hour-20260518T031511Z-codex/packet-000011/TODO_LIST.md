# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hour-20260518T031511Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hour-20260518T031511Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-0fec3a6e6ea13f2a`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.103797308873`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-10-8211-9abd1237a57c55a2, us-code-42-4055.-ac5fac74d6265dbd, us-code-49-44111.-671331807915e2e2`
  evidence: `{"family_margin": -0.879977921479, "hint_id": "modal-synthesis-1bf4f073ab25c7d9", "predicted_family": "temporal", "priority": 1.029977921479, "sample_id": "us-code-49-44111.-671331807915e2e2", "target_family": "frame"}`
  evidence: `{"family_margin": -0.986458105609, "hint_id": "modal-synthesis-4efd0645860560ea", "predicted_family": "temporal", "priority": 1.136458105609, "sample_id": "us-code-42-4055.-ac5fac74d6265dbd", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.994955899531, "hint_id": "modal-synthesis-98c2024679b88f9d", "predicted_family": "temporal", "priority": 1.144955899531, "sample_id": "us-code-10-8211-9abd1237a57c55a2", "target_family": "deontic"}`
