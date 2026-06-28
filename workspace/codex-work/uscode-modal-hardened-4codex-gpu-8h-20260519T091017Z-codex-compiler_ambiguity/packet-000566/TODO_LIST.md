# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-ba549f587ea2d0de`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->deontic","frame->conditional_normative","frame->dynamic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-ba549f587ea2d0de` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.547534919636`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-36-230504-78cb5c6be6527fc3, us-code-15-1693i-c5b32e9682c65bf6, us-code-25-2105-2805749f4deed141`
  evidence: `{"family_margin": -0.494646959627, "hint_id": "modal-synthesis-4d608290aa5a7c45", "predicted_family": "frame", "priority": 0.644646959627, "sample_id": "us-code-15-1693i-c5b32e9682c65bf6", "target_family": "dynamic"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-a08f820398e26d0f", "predicted_family": "deontic", "priority": 0.15, "sample_id": "us-code-25-2105-2805749f4deed141", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.697957799282, "hint_id": "modal-synthesis-d828f2c604e0ef47", "predicted_family": "frame", "priority": 0.847957799282, "sample_id": "us-code-36-230504-78cb5c6be6527fc3", "target_family": "conditional_normative"}`
