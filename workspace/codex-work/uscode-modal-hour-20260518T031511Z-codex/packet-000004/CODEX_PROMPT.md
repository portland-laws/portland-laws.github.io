# packet-000004

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000004/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000004/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000004-20260518_032227

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-5cbbf8ad0fb6c07e` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.988334928701, "hint_id": "modal-synthesis-6239fe79ea7fecd6", "predicted_family": "deontic", "priority": 1.138334928701, "sample_id": "us-code-46-53412.-3b9e2e972bfc8076", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.998163039206, "hint_id": "modal-synthesis-e0ccdc8314984f6e", "predicted_family": "temporal", "priority": 1.148163039206, "sample_id": "us-code-19-1447-d7bfa8c520c9f354", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.999158080866, "hint_id": "modal-synthesis-f9dfb73a9741565c", "predicted_family": "temporal", "priority": 1.149158080866, "sample_id": "us-code-10-8298-ba9d03886532100a", "target_family": "conditional_normative"}`

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
- `program-5cbbf8ad0fb6c07e`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.145218682924`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-10-8298-ba9d03886532100a, us-code-19-1447-d7bfa8c520c9f354, us-code-46-53412.-3b9e2e972bfc8076`
  evidence: `{"family_margin": -0.988334928701, "hint_id": "modal-synthesis-6239fe79ea7fecd6", "predicted_family": "deontic", "priority": 1.138334928701, "sample_id": "us-code-46-53412.-3b9e2e972bfc8076", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.998163039206, "hint_id": "modal-synthesis-e0ccdc8314984f6e", "predicted_family": "temporal", "priority": 1.148163039206, "sample_id": "us-code-19-1447-d7bfa8c520c9f354", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.999158080866, "hint_id": "modal-synthesis-f9dfb73a9741565c", "predicted_family": "temporal", "priority": 1.149158080866, "sample_id": "us-code-10-8298-ba9d03886532100a", "target_family": "conditional_normative"}`
