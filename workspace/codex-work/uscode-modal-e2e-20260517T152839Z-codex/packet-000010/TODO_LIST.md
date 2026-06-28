# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-829dd2db8b8707bf`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.068810175363`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-26-6233-db6218600c54d0a1, us-code-20-6334-4beaa7274f2f07cb`
  evidence: `{"family_margin": -0.919024575338, "hint_id": "modal-synthesis-20c92ee29513f085", "predicted_family": "temporal", "priority": 1.069024575338, "sample_id": "us-code-26-6233-db6218600c54d0a1", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.918595775388, "hint_id": "modal-synthesis-6f62e647f3c64fa9", "predicted_family": "deontic", "priority": 1.068595775388, "sample_id": "us-code-20-6334-4beaa7274f2f07cb", "target_family": "temporal"}`
