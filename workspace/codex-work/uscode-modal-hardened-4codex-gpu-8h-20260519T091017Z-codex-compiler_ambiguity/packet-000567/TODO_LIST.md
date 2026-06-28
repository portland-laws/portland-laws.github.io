# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-55640050f06dfc39`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["conditional_normative->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-55640050f06dfc39` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.602068541432`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-47-555.-f3c0d28d2e6b674d, us-code-7-182-b18cb75569dc2d85`
  evidence: `{"family_margin": -0.98641901285, "hint_id": "modal-synthesis-e865551423ea7cd6", "predicted_family": "frame", "priority": 1.13641901285, "sample_id": "us-code-47-555.-f3c0d28d2e6b674d", "target_family": "temporal"}`
  evidence: `{"family_margin": 0.082281929987, "hint_id": "modal-synthesis-eb1dcda5ac41ee2b", "predicted_family": "conditional_normative", "priority": 0.067718070013, "sample_id": "us-code-7-182-b18cb75569dc2d85", "target_family": "conditional_normative"}`
- `program-3bbcca197991e012`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->frame","frame->deontic","temporal->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-55640050f06dfc39` score `0.952677`
  loss: `autoencoder_residual_cluster` = `0.563316753548`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-14-2735-857345e2c5c2a359, us-code-42-5083.-77b302f9cbe4a1a5, us-code-43-390h.-20a339501c1a8236`
  evidence: `{"family_margin": -0.592973972988, "hint_id": "modal-synthesis-0c3258dc13ab613b", "predicted_family": "frame", "priority": 0.742973972988, "sample_id": "us-code-14-2735-857345e2c5c2a359", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.314912979406, "hint_id": "modal-synthesis-7516117f97306f70", "predicted_family": "alethic", "priority": 0.464912979406, "sample_id": "us-code-43-390h.-20a339501c1a8236", "target_family": "frame"}`
  evidence: `{"family_margin": -0.332063308249, "hint_id": "modal-synthesis-c34f852822fee068", "predicted_family": "temporal", "priority": 0.482063308249, "sample_id": "us-code-42-5083.-77b302f9cbe4a1a5", "target_family": "deontic"}`
