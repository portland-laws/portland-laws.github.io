# packet-000002

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152008Z-codex/packet-000002/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152008Z-codex/packet-000002/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152008Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152008Z-codex-packet-000002-20260517_152538

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-9f73b946ee07dfbe` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.999999166354, "hint_id": "modal-synthesis-97a37b9a9f534210", "predicted_family": "deontic", "priority": 1.149999166354, "sample_id": "us-code-7-9071-d69d5c5ff2fce558", "target_family": "frame"}`
  evidence: `{"family_margin": -0.999999953831, "hint_id": "modal-synthesis-9a417a8d5d329206", "predicted_family": "temporal", "priority": 1.149999953831, "sample_id": "us-code-18-6001-1d3fcd8c228d1a08", "target_family": "deontic"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152008Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152008Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-9f73b946ee07dfbe`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.149999560092`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-18-6001-1d3fcd8c228d1a08, us-code-7-9071-d69d5c5ff2fce558`
  evidence: `{"family_margin": -0.999999166354, "hint_id": "modal-synthesis-97a37b9a9f534210", "predicted_family": "deontic", "priority": 1.149999166354, "sample_id": "us-code-7-9071-d69d5c5ff2fce558", "target_family": "frame"}`
  evidence: `{"family_margin": -0.999999953831, "hint_id": "modal-synthesis-9a417a8d5d329206", "predicted_family": "temporal", "priority": 1.149999953831, "sample_id": "us-code-18-6001-1d3fcd8c228d1a08", "target_family": "deontic"}`
