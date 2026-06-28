# packet-000002

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000002/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000002/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000002-20260517_153732

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-a368a64901e923d5` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-90f1a97d3cd15181", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-29-206-845c3642b2f98030", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.99999977493, "hint_id": "modal-synthesis-d5ed52f0c5c5e53f", "predicted_family": "deontic", "priority": 1.14999977493, "sample_id": "us-code-42-1322.-b26abf2ba9d75d37", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.999998336944, "hint_id": "modal-synthesis-decb5da36ff8a149", "predicted_family": "deontic", "priority": 1.149998336944, "sample_id": "us-code-34-40901-d9783f392f578d32", "target_family": "temporal"}`

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
- `program-a368a64901e923d5`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.149999370625`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-29-206-845c3642b2f98030, us-code-42-1322.-b26abf2ba9d75d37, us-code-34-40901-d9783f392f578d32`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-90f1a97d3cd15181", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-29-206-845c3642b2f98030", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.99999977493, "hint_id": "modal-synthesis-d5ed52f0c5c5e53f", "predicted_family": "deontic", "priority": 1.14999977493, "sample_id": "us-code-42-1322.-b26abf2ba9d75d37", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.999998336944, "hint_id": "modal-synthesis-decb5da36ff8a149", "predicted_family": "deontic", "priority": 1.149998336944, "sample_id": "us-code-34-40901-d9783f392f578d32", "target_family": "temporal"}`
