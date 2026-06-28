# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-f7bc31cbca03871b`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.122718471136`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-5-4303-cbbd1322f24a1882, us-code-29-436-740e3de3d603a2c2`
  evidence: `{"family_margin": -0.945564889475, "hint_id": "modal-synthesis-48b896b178e847eb", "predicted_family": "deontic", "priority": 1.095564889475, "sample_id": "us-code-29-436-740e3de3d603a2c2", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.999872052798, "hint_id": "modal-synthesis-97e160ef5285755d", "predicted_family": "temporal", "priority": 1.149872052798, "sample_id": "us-code-5-4303-cbbd1322f24a1882", "target_family": "conditional_normative"}`
