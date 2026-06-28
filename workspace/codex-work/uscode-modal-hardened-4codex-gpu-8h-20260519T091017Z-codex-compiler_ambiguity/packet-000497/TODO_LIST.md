# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-4fd173fcbf69db4f`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->temporal","frame->epistemic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-4fd173fcbf69db4f` score `1.0`
  loss: `autoencoder_residual_cluster` = `1.064748839898`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-15-1644-9e552b71b349501b, us-code-25-139-d7777f253f3394b8`
  evidence: `{"family_margin": -0.957919173467, "hint_id": "modal-synthesis-14128bcd7267b5de", "predicted_family": "frame", "priority": 1.107919173467, "sample_id": "us-code-15-1644-9e552b71b349501b", "target_family": "epistemic"}`
  evidence: `{"family_margin": -0.87157850633, "hint_id": "modal-synthesis-25b55be77cf7f82f", "predicted_family": "deontic", "priority": 1.02157850633, "sample_id": "us-code-25-139-d7777f253f3394b8", "target_family": "temporal"}`
