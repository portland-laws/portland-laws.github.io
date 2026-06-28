# packet-000001

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-root-20260517T144005Z-codex/packet-000001/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-root-20260517T144005Z-codex/packet-000001/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-root-20260517T144005Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-supervised-root-20260517T144005Z-codex-packet-000001-20260517_144011

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-a248055f52c78b79` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": -0.131380026985, "hint_id": "modal-synthesis-153f211b0158d692", "priority": 0.789148125417, "reconstruction_loss": 0.789148125417, "sample_id": "us-code-16-430f-3-b0acd7628a2028d3"}`
  evidence: `{"cosine_similarity": -0.597268066061, "hint_id": "modal-synthesis-d98dd6ac6a4466ed", "priority": 0.734425393821, "reconstruction_loss": 0.734425393821, "sample_id": "us-code-42-2139a.-20316784ad0aace2"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```
