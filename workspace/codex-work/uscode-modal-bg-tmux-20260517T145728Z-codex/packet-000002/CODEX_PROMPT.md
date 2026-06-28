# packet-000002

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000002/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000002/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000002-20260517_150409

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-46a228b728c12e35` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.986595557522, "hint_id": "modal-synthesis-0e312951636da861", "predicted_family": "temporal", "priority": 1.136595557522, "sample_id": "us-code-20-1135c-d3b61be83f24785c", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.997527376843, "hint_id": "modal-synthesis-e88c663fecf8fd20", "predicted_family": "deontic", "priority": 1.147527376843, "sample_id": "us-code-42-247d-7032d3f07d177525", "target_family": "epistemic"}`

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
- `program-46a228b728c12e35`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.142061467183`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-247d-7032d3f07d177525, us-code-20-1135c-d3b61be83f24785c`
  evidence: `{"family_margin": -0.986595557522, "hint_id": "modal-synthesis-0e312951636da861", "predicted_family": "temporal", "priority": 1.136595557522, "sample_id": "us-code-20-1135c-d3b61be83f24785c", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.997527376843, "hint_id": "modal-synthesis-e88c663fecf8fd20", "predicted_family": "deontic", "priority": 1.147527376843, "sample_id": "us-code-42-247d-7032d3f07d177525", "target_family": "epistemic"}`
