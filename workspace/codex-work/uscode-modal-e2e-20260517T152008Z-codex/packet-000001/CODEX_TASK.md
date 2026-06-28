# packet-000001

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152008Z-codex/packet-000001/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152008Z-codex/packet-000001/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152008Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152008Z-codex-packet-000001-20260517_152019

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-76a56d03d4719f65` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.755144230447, "hint_id": "modal-synthesis-344a15c9b335a43c", "predicted_family": "temporal", "priority": 0.905144230447, "sample_id": "us-code-16-690b-0fe42bf8360601ae", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.979497600371, "hint_id": "modal-synthesis-3450fd3ed31436a5", "predicted_family": "temporal", "priority": 1.129497600371, "sample_id": "us-code-5-3333-ce51d21cfaae7f20", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.904791860193, "hint_id": "modal-synthesis-c00b1b1f52842fce", "predicted_family": "temporal", "priority": 1.054791860193, "sample_id": "us-code-20-9904-1ede866558967af3", "target_family": "deontic"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```
