# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hour-20260518T031511Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hour-20260518T031511Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-4bf9bc980068d1a5`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.056571471315`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-5-8412a-fb7dc99c481d5fab, us-code-34-11186-0ca85651195dfd90, us-code-42-2313.-8f41b1cac65a9419`
  evidence: `{"family_margin": -0.961440464124, "hint_id": "modal-synthesis-1648479fc1ef85a1", "predicted_family": "deontic", "priority": 1.111440464124, "sample_id": "us-code-34-11186-0ca85651195dfd90", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.999999999999, "hint_id": "modal-synthesis-a7863c9454ab9f02", "predicted_family": "deontic", "priority": 1.149999999999, "sample_id": "us-code-5-8412a-fb7dc99c481d5fab", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.758273949821, "hint_id": "modal-synthesis-eb5cecba86e806f8", "predicted_family": "temporal", "priority": 0.908273949821, "sample_id": "us-code-42-2313.-8f41b1cac65a9419", "target_family": "deontic"}`
