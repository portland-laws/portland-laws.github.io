# packet-000010

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000010/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000010/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000010-20260517_162852

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-829dd2db8b8707bf` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.919024575338, "hint_id": "modal-synthesis-20c92ee29513f085", "predicted_family": "temporal", "priority": 1.069024575338, "sample_id": "us-code-26-6233-db6218600c54d0a1", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.918595775388, "hint_id": "modal-synthesis-6f62e647f3c64fa9", "predicted_family": "deontic", "priority": 1.068595775388, "sample_id": "us-code-20-6334-4beaa7274f2f07cb", "target_family": "temporal"}`

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

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-829dd2db8b8707bf`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.068810175363`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-26-6233-db6218600c54d0a1, us-code-20-6334-4beaa7274f2f07cb`
  evidence: `{"family_margin": -0.919024575338, "hint_id": "modal-synthesis-20c92ee29513f085", "predicted_family": "temporal", "priority": 1.069024575338, "sample_id": "us-code-26-6233-db6218600c54d0a1", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.918595775388, "hint_id": "modal-synthesis-6f62e647f3c64fa9", "predicted_family": "deontic", "priority": 1.068595775388, "sample_id": "us-code-20-6334-4beaa7274f2f07cb", "target_family": "temporal"}`
