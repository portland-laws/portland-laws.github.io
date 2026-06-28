# packet-000004

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000004/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000004/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000004-20260517_154730

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-0bcb007c3227c893` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.999043633465, "hint_id": "modal-synthesis-0a7b08b99442b089", "predicted_family": "temporal", "priority": 1.149043633465, "sample_id": "us-code-26-2514-6a8917b89275a113", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.995054527352, "hint_id": "modal-synthesis-0e98f7afe7d2afee", "predicted_family": "deontic", "priority": 1.145054527352, "sample_id": "us-code-22-3794-739d2739f3a58466", "target_family": "temporal"}`

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
- `program-0bcb007c3227c893`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.147049080409`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-26-2514-6a8917b89275a113, us-code-22-3794-739d2739f3a58466`
  evidence: `{"family_margin": -0.999043633465, "hint_id": "modal-synthesis-0a7b08b99442b089", "predicted_family": "temporal", "priority": 1.149043633465, "sample_id": "us-code-26-2514-6a8917b89275a113", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.995054527352, "hint_id": "modal-synthesis-0e98f7afe7d2afee", "predicted_family": "deontic", "priority": 1.145054527352, "sample_id": "us-code-22-3794-739d2739f3a58466", "target_family": "temporal"}`
