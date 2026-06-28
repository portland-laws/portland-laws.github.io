# packet-000004

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000004/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000004/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000004-20260517_151320

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-f4d51ee3ac819028` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-a252714c867a648e", "predicted_family": "deontic", "priority": 1.15, "sample_id": "us-code-15-636-2c99c6e6d2e95f00", "target_family": "temporal"}`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-b2cd5713cfc55796", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-38-1710-f36eb1d15e1f571a", "target_family": "conditional_normative"}`

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
- `program-f4d51ee3ac819028`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.15`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-15-636-2c99c6e6d2e95f00, us-code-38-1710-f36eb1d15e1f571a`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-a252714c867a648e", "predicted_family": "deontic", "priority": 1.15, "sample_id": "us-code-15-636-2c99c6e6d2e95f00", "target_family": "temporal"}`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-b2cd5713cfc55796", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-38-1710-f36eb1d15e1f571a", "target_family": "conditional_normative"}`
