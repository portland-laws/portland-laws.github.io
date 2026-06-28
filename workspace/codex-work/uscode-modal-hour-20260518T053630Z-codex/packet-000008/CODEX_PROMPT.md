# packet-000008

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000008/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000008/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000008-20260518_055554

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-5698a1aec2585a50` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.9969117081, "hint_id": "modal-synthesis-152fd15e8447f275", "predicted_family": "temporal", "priority": 1.1469117081, "sample_id": "us-code-15-1679d-20927c4a41fe2b9d", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.997719301446, "hint_id": "modal-synthesis-a73108109e7efe67", "predicted_family": "temporal", "priority": 1.147719301446, "sample_id": "us-code-49-80104.-58011132fc5a52a8", "target_family": "deontic"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Treat the packet's program_synthesis_scope metadata as the AST/write-scope boundary; keep edits inside that lane unless a test requires a small adjacent change.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hour-20260518T053630Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hour-20260518T053630Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-5698a1aec2585a50`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.147315504773`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-49-80104.-58011132fc5a52a8, us-code-15-1679d-20927c4a41fe2b9d`
  evidence: `{"family_margin": -0.9969117081, "hint_id": "modal-synthesis-152fd15e8447f275", "predicted_family": "temporal", "priority": 1.1469117081, "sample_id": "us-code-15-1679d-20927c4a41fe2b9d", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.997719301446, "hint_id": "modal-synthesis-a73108109e7efe67", "predicted_family": "temporal", "priority": 1.147719301446, "sample_id": "us-code-49-80104.-58011132fc5a52a8", "target_family": "deontic"}`
