# packet-000007

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000007/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000007/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000007-20260517_160912

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-0171995e3313be82` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.981633771742, "hint_id": "modal-synthesis-237900d841544f90", "predicted_family": "temporal", "priority": 1.131633771742, "sample_id": "us-code-28-1409-9ea1a3d3a9afc1e0", "target_family": "frame"}`
  evidence: `{"family_margin": -0.970339235422, "hint_id": "modal-synthesis-42a20cb9ef367bae", "predicted_family": "deontic", "priority": 1.120339235422, "sample_id": "us-code-20-1161r-9af5e02512a2252b", "target_family": "frame"}`
  evidence: `{"family_margin": -0.880750948337, "hint_id": "modal-synthesis-85c65a7d89a6e913", "predicted_family": "deontic", "priority": 1.030750948337, "sample_id": "us-code-31-3327-bafefcf1f81b20c3", "target_family": "frame"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-0171995e3313be82`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.0942413185`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-28-1409-9ea1a3d3a9afc1e0, us-code-20-1161r-9af5e02512a2252b, us-code-31-3327-bafefcf1f81b20c3`
  evidence: `{"family_margin": -0.981633771742, "hint_id": "modal-synthesis-237900d841544f90", "predicted_family": "temporal", "priority": 1.131633771742, "sample_id": "us-code-28-1409-9ea1a3d3a9afc1e0", "target_family": "frame"}`
  evidence: `{"family_margin": -0.970339235422, "hint_id": "modal-synthesis-42a20cb9ef367bae", "predicted_family": "deontic", "priority": 1.120339235422, "sample_id": "us-code-20-1161r-9af5e02512a2252b", "target_family": "frame"}`
  evidence: `{"family_margin": -0.880750948337, "hint_id": "modal-synthesis-85c65a7d89a6e913", "predicted_family": "deontic", "priority": 1.030750948337, "sample_id": "us-code-31-3327-bafefcf1f81b20c3", "target_family": "frame"}`
