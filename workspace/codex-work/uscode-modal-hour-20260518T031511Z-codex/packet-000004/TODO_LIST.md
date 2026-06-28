# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hour-20260518T031511Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hour-20260518T031511Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-5cbbf8ad0fb6c07e`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.145218682924`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-10-8298-ba9d03886532100a, us-code-19-1447-d7bfa8c520c9f354, us-code-46-53412.-3b9e2e972bfc8076`
  evidence: `{"family_margin": -0.988334928701, "hint_id": "modal-synthesis-6239fe79ea7fecd6", "predicted_family": "deontic", "priority": 1.138334928701, "sample_id": "us-code-46-53412.-3b9e2e972bfc8076", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.998163039206, "hint_id": "modal-synthesis-e0ccdc8314984f6e", "predicted_family": "temporal", "priority": 1.148163039206, "sample_id": "us-code-19-1447-d7bfa8c520c9f354", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.999158080866, "hint_id": "modal-synthesis-f9dfb73a9741565c", "predicted_family": "temporal", "priority": 1.149158080866, "sample_id": "us-code-10-8298-ba9d03886532100a", "target_family": "conditional_normative"}`
