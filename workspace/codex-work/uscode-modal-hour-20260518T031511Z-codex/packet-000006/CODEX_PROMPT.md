# packet-000006

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000006/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000006/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000006-20260518_033558

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-b490bf6f2295ceed` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.999999999986, "hint_id": "modal-synthesis-242a7d3ce94611db", "predicted_family": "temporal", "priority": 1.149999999986, "sample_id": "us-code-42-1396p.-fe21139649ebeec7", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.999999994397, "hint_id": "modal-synthesis-8b19b0d772921798", "predicted_family": "deontic", "priority": 1.149999994397, "sample_id": "us-code-47-303.-26a967862251ad66", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.95622847174, "hint_id": "modal-synthesis-be1ebe86ed88d40b", "predicted_family": "temporal", "priority": 1.10622847174, "sample_id": "us-code-42-2274.-2795cc75e1c0bf45", "target_family": "deontic"}`

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
- `program-b490bf6f2295ceed`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.135409488708`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-1396p.-fe21139649ebeec7, us-code-47-303.-26a967862251ad66, us-code-42-2274.-2795cc75e1c0bf45`
  evidence: `{"family_margin": -0.999999999986, "hint_id": "modal-synthesis-242a7d3ce94611db", "predicted_family": "temporal", "priority": 1.149999999986, "sample_id": "us-code-42-1396p.-fe21139649ebeec7", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.999999994397, "hint_id": "modal-synthesis-8b19b0d772921798", "predicted_family": "deontic", "priority": 1.149999994397, "sample_id": "us-code-47-303.-26a967862251ad66", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.95622847174, "hint_id": "modal-synthesis-be1ebe86ed88d40b", "predicted_family": "temporal", "priority": 1.10622847174, "sample_id": "us-code-42-2274.-2795cc75e1c0bf45", "target_family": "deontic"}`
