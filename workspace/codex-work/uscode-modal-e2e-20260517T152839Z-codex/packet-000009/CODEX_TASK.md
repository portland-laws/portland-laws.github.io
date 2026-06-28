# packet-000009

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000009/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000009/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000009-20260517_162144

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-00eea260a1b250d5` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.999954602131, "hint_id": "modal-synthesis-2ee17c503c09e716", "predicted_family": "deontic", "priority": 1.149954602131, "sample_id": "us-code-26-3134-7d41d03274935de1", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.99998705312, "hint_id": "modal-synthesis-6e6699c14ac816f3", "predicted_family": "deontic", "priority": 1.14998705312, "sample_id": "us-code-22-4106-2bec276bc903c601", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.761594155956, "hint_id": "modal-synthesis-e36d48730f9c00be", "predicted_family": "temporal", "priority": 0.911594155956, "sample_id": "us-code-15-78dd-1-18ce21e2386aaaab", "target_family": "deontic"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
