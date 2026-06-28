# packet-000005

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000005/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/packet-000005/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hour-20260518T053630Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-hour-20260518T053630Z-codex-packet-000005-20260518_053713

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-7248fe1dba78eda8` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.99999999584, "hint_id": "modal-synthesis-0d0924add337932f", "predicted_family": "deontic", "priority": 0.999999997939, "sample_id": "us-code-26-6164-b541519d7ea4361a", "target_family": "temporal", "target_probability": 2.061e-09}`
  evidence: `{"family_margin": -0.761581214232, "hint_id": "modal-synthesis-6657570012b50aa2", "predicted_family": "temporal", "priority": 0.880799103586, "sample_id": "us-code-42-1397a.-c872e61c07a43984", "target_family": "deontic", "target_probability": 0.119200896414}`
  evidence: `{"family_margin": -0.411885467434, "hint_id": "modal-synthesis-fe50e0ff002b017f", "predicted_family": "temporal", "priority": 0.760292252056, "sample_id": "us-code-42-12144.-d02bf5ae02f1e4e5", "target_family": "conditional_normative", "target_probability": 0.239707747944}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
