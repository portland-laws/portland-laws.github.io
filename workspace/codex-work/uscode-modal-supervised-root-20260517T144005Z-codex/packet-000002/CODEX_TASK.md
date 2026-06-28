# packet-000002

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-root-20260517T144005Z-codex/packet-000002/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-root-20260517T144005Z-codex/packet-000002/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-root-20260517T144005Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-supervised-root-20260517T144005Z-codex-packet-000002-20260517_144205

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-455a3e9b0b099013` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.99999996954, "hint_id": "modal-synthesis-3d4554f1fc1f865b", "predicted_family": "temporal", "priority": 1.14999996954, "sample_id": "us-code-26-1471-d223878b6ad984f9", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.999999845848, "hint_id": "modal-synthesis-e40e45adb1a278d0", "predicted_family": "deontic", "priority": 1.149999845848, "sample_id": "us-code-38-7329-0eb198b8ac218525", "target_family": "frame"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```
