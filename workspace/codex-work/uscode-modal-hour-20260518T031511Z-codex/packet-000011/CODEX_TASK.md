# packet-000011

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000011/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/packet-000011/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T031511Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T031511Z-codex-packet-000011-20260518_040821

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-0fec3a6e6ea13f2a` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.879977921479, "hint_id": "modal-synthesis-1bf4f073ab25c7d9", "predicted_family": "temporal", "priority": 1.029977921479, "sample_id": "us-code-49-44111.-671331807915e2e2", "target_family": "frame"}`
  evidence: `{"family_margin": -0.986458105609, "hint_id": "modal-synthesis-4efd0645860560ea", "predicted_family": "temporal", "priority": 1.136458105609, "sample_id": "us-code-42-4055.-ac5fac74d6265dbd", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.994955899531, "hint_id": "modal-synthesis-98c2024679b88f9d", "predicted_family": "temporal", "priority": 1.144955899531, "sample_id": "us-code-10-8211-9abd1237a57c55a2", "target_family": "deontic"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
