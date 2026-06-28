# packet-000010

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000010/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000010/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000010-20260518_060625

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-0ffeb126d3f5bea0` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.988411341698, "hint_id": "modal-synthesis-3a917a4f905a8f96", "predicted_family": "temporal", "priority": 1.138411341698, "sample_id": "us-code-20-7261-2b584dbbd067d4e6", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.992723401446, "hint_id": "modal-synthesis-6ccf2a8babfb96ca", "predicted_family": "deontic", "priority": 1.142723401446, "sample_id": "us-code-7-9035-732d721c86e9cde0", "target_family": "conditional_normative"}`

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
- `program-0ffeb126d3f5bea0`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.140567371572`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-7-9035-732d721c86e9cde0, us-code-20-7261-2b584dbbd067d4e6`
  evidence: `{"family_margin": -0.988411341698, "hint_id": "modal-synthesis-3a917a4f905a8f96", "predicted_family": "temporal", "priority": 1.138411341698, "sample_id": "us-code-20-7261-2b584dbbd067d4e6", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.992723401446, "hint_id": "modal-synthesis-6ccf2a8babfb96ca", "predicted_family": "deontic", "priority": 1.142723401446, "sample_id": "us-code-7-9035-732d721c86e9cde0", "target_family": "conditional_normative"}`
