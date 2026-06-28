# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hour-20260518T031511Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hour-20260518T031511Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-b490bf6f2295ceed`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.135409488708`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-1396p.-fe21139649ebeec7, us-code-47-303.-26a967862251ad66, us-code-42-2274.-2795cc75e1c0bf45`
  evidence: `{"family_margin": -0.999999999986, "hint_id": "modal-synthesis-242a7d3ce94611db", "predicted_family": "temporal", "priority": 1.149999999986, "sample_id": "us-code-42-1396p.-fe21139649ebeec7", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.999999994397, "hint_id": "modal-synthesis-8b19b0d772921798", "predicted_family": "deontic", "priority": 1.149999994397, "sample_id": "us-code-47-303.-26a967862251ad66", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.95622847174, "hint_id": "modal-synthesis-be1ebe86ed88d40b", "predicted_family": "temporal", "priority": 1.10622847174, "sample_id": "us-code-42-2274.-2795cc75e1c0bf45", "target_family": "deontic"}`
