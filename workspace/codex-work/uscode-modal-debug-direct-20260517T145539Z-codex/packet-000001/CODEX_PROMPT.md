# packet-000001

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-debug-direct-20260517T145539Z-codex/packet-000001/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-debug-direct-20260517T145539Z-codex/packet-000001/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-debug-direct-20260517T145539Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-debug-direct-20260517T145539Z-codex-packet-000001-20260517_145550

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-018db7d72ee06e33` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.99999991514, "hint_id": "modal-synthesis-323085d66447ea2a", "predicted_family": "temporal", "priority": 1.14999991514, "sample_id": "us-code-2-4507-9dd476b9e08030a0", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.982013790038, "hint_id": "modal-synthesis-c59a7e5d6a06a3b5", "predicted_family": "temporal", "priority": 1.132013790038, "sample_id": "us-code-42-15907.-10605764e72d0684", "target_family": "frame"}`

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

- Queue run: `uscode-modal-debug-direct-20260517T145539Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-debug-direct-20260517T145539Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-018db7d72ee06e33`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.141006852589`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-2-4507-9dd476b9e08030a0, us-code-42-15907.-10605764e72d0684`
  evidence: `{"family_margin": -0.99999991514, "hint_id": "modal-synthesis-323085d66447ea2a", "predicted_family": "temporal", "priority": 1.14999991514, "sample_id": "us-code-2-4507-9dd476b9e08030a0", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.982013790038, "hint_id": "modal-synthesis-c59a7e5d6a06a3b5", "predicted_family": "temporal", "priority": 1.132013790038, "sample_id": "us-code-42-15907.-10605764e72d0684", "target_family": "frame"}`
