# packet-000003

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000003/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000003/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000003-20260517_150843

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-fb14f189c2470b66` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.999664643947, "hint_id": "modal-synthesis-47afc7224efd0d22", "predicted_family": "deontic", "priority": 1.149664643947, "sample_id": "us-code-42-5196b.-bd53c8007edb2bd1", "target_family": "frame"}`
  evidence: `{"family_margin": -0.982013789768, "hint_id": "modal-synthesis-c6f4ec68d87e318e", "predicted_family": "deontic", "priority": 1.132013789768, "sample_id": "us-code-15-9009c-953c49b93d0b574c", "target_family": "frame"}`

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
- `program-fb14f189c2470b66`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.140839216858`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-5196b.-bd53c8007edb2bd1, us-code-15-9009c-953c49b93d0b574c`
  evidence: `{"family_margin": -0.999664643947, "hint_id": "modal-synthesis-47afc7224efd0d22", "predicted_family": "deontic", "priority": 1.149664643947, "sample_id": "us-code-42-5196b.-bd53c8007edb2bd1", "target_family": "frame"}`
  evidence: `{"family_margin": -0.982013789768, "hint_id": "modal-synthesis-c6f4ec68d87e318e", "predicted_family": "deontic", "priority": 1.132013789768, "sample_id": "us-code-15-9009c-953c49b93d0b574c", "target_family": "frame"}`
