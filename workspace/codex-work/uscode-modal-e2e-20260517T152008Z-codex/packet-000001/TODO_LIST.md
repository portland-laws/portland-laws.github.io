# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152008Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152008Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-76a56d03d4719f65`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.029811230337`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-5-3333-ce51d21cfaae7f20, us-code-20-9904-1ede866558967af3, us-code-16-690b-0fe42bf8360601ae`
  evidence: `{"family_margin": -0.755144230447, "hint_id": "modal-synthesis-344a15c9b335a43c", "predicted_family": "temporal", "priority": 0.905144230447, "sample_id": "us-code-16-690b-0fe42bf8360601ae", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.979497600371, "hint_id": "modal-synthesis-3450fd3ed31436a5", "predicted_family": "temporal", "priority": 1.129497600371, "sample_id": "us-code-5-3333-ce51d21cfaae7f20", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.904791860193, "hint_id": "modal-synthesis-c00b1b1f52842fce", "predicted_family": "temporal", "priority": 1.054791860193, "sample_id": "us-code-20-9904-1ede866558967af3", "target_family": "deontic"}`
