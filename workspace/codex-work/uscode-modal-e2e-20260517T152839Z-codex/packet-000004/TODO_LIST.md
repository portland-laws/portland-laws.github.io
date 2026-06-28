# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-0bcb007c3227c893`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.147049080409`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-26-2514-6a8917b89275a113, us-code-22-3794-739d2739f3a58466`
  evidence: `{"family_margin": -0.999043633465, "hint_id": "modal-synthesis-0a7b08b99442b089", "predicted_family": "temporal", "priority": 1.149043633465, "sample_id": "us-code-26-2514-6a8917b89275a113", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.995054527352, "hint_id": "modal-synthesis-0e98f7afe7d2afee", "predicted_family": "deontic", "priority": 1.145054527352, "sample_id": "us-code-22-3794-739d2739f3a58466", "target_family": "temporal"}`
