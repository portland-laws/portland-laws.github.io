# packet-000001

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000001/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000001/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000001-20260517_145739

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-069bafb09ba07ac7` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-60a7671ce50fecda", "predicted_family": "temporal", "priority": 0.643757932971, "sample_id": "us-code-16-554c-b2920b0655ea4019", "target_family": "deontic", "target_probability": 0.356242067029}`
  evidence: `{"family_margin": -0.999995479351, "hint_id": "modal-synthesis-ca53b0367eff2f9a", "predicted_family": "deontic", "priority": 0.999997739676, "sample_id": "us-code-42-9605.-e797e44e0150247e", "target_family": "temporal", "target_probability": 2.260324e-06}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```


## Execution Instructions
Work only inside the packet worktree.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-bg-tmux-20260517T145728Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-bg-tmux-20260517T145728Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-069bafb09ba07ac7`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  loss: `autoencoder_residual_cluster` = `0.821877836323`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-42-9605.-e797e44e0150247e, us-code-16-554c-b2920b0655ea4019`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-60a7671ce50fecda", "predicted_family": "temporal", "priority": 0.643757932971, "sample_id": "us-code-16-554c-b2920b0655ea4019", "target_family": "deontic", "target_probability": 0.356242067029}`
  evidence: `{"family_margin": -0.999995479351, "hint_id": "modal-synthesis-ca53b0367eff2f9a", "predicted_family": "deontic", "priority": 0.999997739676, "sample_id": "us-code-42-9605.-e797e44e0150247e", "target_family": "temporal", "target_probability": 2.260324e-06}`
