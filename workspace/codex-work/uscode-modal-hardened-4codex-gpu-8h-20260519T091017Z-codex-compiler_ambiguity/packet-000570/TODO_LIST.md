# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-bfe8ae94d3856e3a`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["dynamic->dynamic","frame->conditional_normative","frame->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-bfe8ae94d3856e3a` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.713210807867`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-12-2091-76d98884a22e0c41, us-code-36-220522-c5d706908c8f3683, us-code-42-7385s-359864d4338b98ff`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-3f59cdf6d660c8a7", "predicted_family": "dynamic", "priority": 0.15, "sample_id": "us-code-42-7385s-359864d4338b98ff", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.837741879819, "hint_id": "modal-synthesis-49d645daa86b432e", "predicted_family": "frame", "priority": 0.987741879819, "sample_id": "us-code-36-220522-c5d706908c8f3683", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.851890543783, "hint_id": "modal-synthesis-515f32ba228c133c", "predicted_family": "frame", "priority": 1.001890543783, "sample_id": "us-code-12-2091-76d98884a22e0c41", "target_family": "deontic"}`
