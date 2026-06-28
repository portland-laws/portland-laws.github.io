# packet-000006

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000006/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000006/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000006-20260517_160106

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-f7bc31cbca03871b` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.945564889475, "hint_id": "modal-synthesis-48b896b178e847eb", "predicted_family": "deontic", "priority": 1.095564889475, "sample_id": "us-code-29-436-740e3de3d603a2c2", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.999872052798, "hint_id": "modal-synthesis-97e160ef5285755d", "predicted_family": "temporal", "priority": 1.149872052798, "sample_id": "us-code-5-4303-cbbd1322f24a1882", "target_family": "conditional_normative"}`

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
- `program-f7bc31cbca03871b`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  loss: `autoencoder_residual_cluster` = `1.122718471136`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-5-4303-cbbd1322f24a1882, us-code-29-436-740e3de3d603a2c2`
  evidence: `{"family_margin": -0.945564889475, "hint_id": "modal-synthesis-48b896b178e847eb", "predicted_family": "deontic", "priority": 1.095564889475, "sample_id": "us-code-29-436-740e3de3d603a2c2", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.999872052798, "hint_id": "modal-synthesis-97e160ef5285755d", "predicted_family": "temporal", "priority": 1.149872052798, "sample_id": "us-code-5-4303-cbbd1322f24a1882", "target_family": "conditional_normative"}`
