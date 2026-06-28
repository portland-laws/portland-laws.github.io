# packet-000011

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000011/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000011/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000011-20260518_061317

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-ad8cc2244d7e1cae` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.981772759874, "hint_id": "modal-synthesis-22db05d1e95de001", "predicted_family": "deontic", "priority": 1.131772759874, "sample_id": "us-code-18-930-d9181e80fc52ba40", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.986559457815, "hint_id": "modal-synthesis-52d1b5269fc02340", "predicted_family": "temporal", "priority": 1.136559457815, "sample_id": "us-code-18-607-b05a65ff022ab3a4", "target_family": "deontic"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
