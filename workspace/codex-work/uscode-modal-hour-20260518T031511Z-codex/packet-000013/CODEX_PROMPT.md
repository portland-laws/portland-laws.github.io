# packet-000013

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000013/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000013/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000013-20260518_041606

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-4bf9bc980068d1a5` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.961440464124, "hint_id": "modal-synthesis-1648479fc1ef85a1", "predicted_family": "deontic", "priority": 1.111440464124, "sample_id": "us-code-34-11186-0ca85651195dfd90", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.999999999999, "hint_id": "modal-synthesis-a7863c9454ab9f02", "predicted_family": "deontic", "priority": 1.149999999999, "sample_id": "us-code-5-8412a-fb7dc99c481d5fab", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.758273949821, "hint_id": "modal-synthesis-eb5cecba86e806f8", "predicted_family": "temporal", "priority": 0.908273949821, "sample_id": "us-code-42-2313.-8f41b1cac65a9419", "target_family": "deontic"}`

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
- `program-4bf9bc980068d1a5`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.056571471315`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-5-8412a-fb7dc99c481d5fab, us-code-34-11186-0ca85651195dfd90, us-code-42-2313.-8f41b1cac65a9419`
  evidence: `{"family_margin": -0.961440464124, "hint_id": "modal-synthesis-1648479fc1ef85a1", "predicted_family": "deontic", "priority": 1.111440464124, "sample_id": "us-code-34-11186-0ca85651195dfd90", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.999999999999, "hint_id": "modal-synthesis-a7863c9454ab9f02", "predicted_family": "deontic", "priority": 1.149999999999, "sample_id": "us-code-5-8412a-fb7dc99c481d5fab", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.758273949821, "hint_id": "modal-synthesis-eb5cecba86e806f8", "predicted_family": "temporal", "priority": 0.908273949821, "sample_id": "us-code-42-2313.-8f41b1cac65a9419", "target_family": "deontic"}`
