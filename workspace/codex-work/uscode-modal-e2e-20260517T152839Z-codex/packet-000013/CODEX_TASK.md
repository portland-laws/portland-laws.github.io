# packet-000013

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000013/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000013/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000013-20260517_165031

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-6a1f221e39704295` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.900882165574, "hint_id": "modal-synthesis-da2cec612ce8fbf9", "predicted_family": "deontic", "priority": 1.050882165574, "sample_id": "us-code-25-2454-8a9220338dcd54a5", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.88914687785, "hint_id": "modal-synthesis-ea7b71a6ee94836f", "predicted_family": "temporal", "priority": 1.03914687785, "sample_id": "us-code-41-6102-e4413b0b94be77ce", "target_family": "alethic"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
