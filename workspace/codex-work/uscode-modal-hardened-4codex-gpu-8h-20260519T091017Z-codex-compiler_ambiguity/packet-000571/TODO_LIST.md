# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-f5576f3893a4f6b4`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["conditional_normative->temporal","frame->conditional_normative","frame->temporal","temporal->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-f5576f3893a4f6b4` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.705687178834`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-12-5707-a20569681a642369, us-code-10-687-62134f1eaa130df9, us-code-42-10225.-8bd3296ec2ba451b, us-code-6-924-46b4e91da16607f0`
  evidence: `{"family_margin": -0.930605805155, "hint_id": "modal-synthesis-04f76ba6709fe14f", "predicted_family": "frame", "priority": 1.080605805155, "sample_id": "us-code-12-5707-a20569681a642369", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.823053456348, "hint_id": "modal-synthesis-349478c77be6c03a", "predicted_family": "frame", "priority": 0.973053456348, "sample_id": "us-code-10-687-62134f1eaa130df9", "target_family": "temporal"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-585bc3b85d8e591c", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-6-924-46b4e91da16607f0", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.469089453834, "hint_id": "modal-synthesis-b53879e7c4469648", "predicted_family": "conditional_normative", "priority": 0.619089453834, "sample_id": "us-code-42-10225.-8bd3296ec2ba451b", "target_family": "temporal"}`
