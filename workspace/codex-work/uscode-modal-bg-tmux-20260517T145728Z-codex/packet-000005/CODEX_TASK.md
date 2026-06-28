# packet-000005

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000005/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/packet-000005/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000005-20260517_151849

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-3acb605425fb9105` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.995054712419, "hint_id": "modal-synthesis-4e2d4699b3aa55c9", "predicted_family": "temporal", "priority": 1.145054712419, "sample_id": "us-code-50-2131.-eaf4441b5af75a96", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.976817703863, "hint_id": "modal-synthesis-e8a3ac6efceef213", "predicted_family": "temporal", "priority": 1.126817703863, "sample_id": "us-code-12-1707-a9b005a482816c26", "target_family": "conditional_normative"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```
