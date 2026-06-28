# packet-000006

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000006/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000006/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000006-20260518_054305

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-95689abdb450103b` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.997444485413, "hint_id": "modal-synthesis-10810329403e2313", "predicted_family": "temporal", "priority": 1.147444485413, "sample_id": "us-code-16-3502-d7f71abda6773ac6", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-687df3969b960c57", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-7-1981-05bfcfb28921524d", "target_family": "frame"}`

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
- `program-95689abdb450103b`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.148722242707`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-7-1981-05bfcfb28921524d, us-code-16-3502-d7f71abda6773ac6`
  evidence: `{"family_margin": -0.997444485413, "hint_id": "modal-synthesis-10810329403e2313", "predicted_family": "temporal", "priority": 1.147444485413, "sample_id": "us-code-16-3502-d7f71abda6773ac6", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -1.0, "hint_id": "modal-synthesis-687df3969b960c57", "predicted_family": "temporal", "priority": 1.15, "sample_id": "us-code-7-1981-05bfcfb28921524d", "target_family": "frame"}`
