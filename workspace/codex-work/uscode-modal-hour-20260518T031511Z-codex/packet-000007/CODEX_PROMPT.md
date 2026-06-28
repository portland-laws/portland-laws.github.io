# packet-000007

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000007/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000007/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000007-20260518_034150

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-2c9280ade42a5417` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.964027574767, "hint_id": "modal-synthesis-5269806514837e7b", "predicted_family": "temporal", "priority": 1.114027574767, "sample_id": "us-code-33-1282-51371e0b7972bf47", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.99990920416, "hint_id": "modal-synthesis-a23e4a300ec936d5", "predicted_family": "deontic", "priority": 1.14990920416, "sample_id": "us-code-20-6312-47111943ab2d106e", "target_family": "temporal"}`

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

- Queue run: `uscode-modal-hour-20260518T031511Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hour-20260518T031511Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-2c9280ade42a5417`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.131968389464`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-20-6312-47111943ab2d106e, us-code-33-1282-51371e0b7972bf47`
  evidence: `{"family_margin": -0.964027574767, "hint_id": "modal-synthesis-5269806514837e7b", "predicted_family": "temporal", "priority": 1.114027574767, "sample_id": "us-code-33-1282-51371e0b7972bf47", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.99990920416, "hint_id": "modal-synthesis-a23e4a300ec936d5", "predicted_family": "deontic", "priority": 1.14990920416, "sample_id": "us-code-20-6312-47111943ab2d106e", "target_family": "temporal"}`
