# packet-000020

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000020/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000020/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000020-20260516_155516

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-358b715d28185e14` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.065398206681, "hint_id": "modal-synthesis-79702fc90fe1606a", "priority": 0.431941892127, "reconstruction_loss": 0.431941892127, "sample_id": "us-code-2-5326-79178d297c7d0e2e"}`
  evidence: `{"cosine_similarity": 0.403357492019, "hint_id": "modal-synthesis-cc8532fe259ef72c", "priority": 0.322176009597, "reconstruction_loss": 0.322176009597, "sample_id": "us-code-16-4221-afd641e9d25b51d8"}`
- `program-ba9e01f75b592a75` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-1d3481b25a54a05f", "priority": 0.322176009597, "sample_id": "us-code-16-4221-afd641e9d25b51d8"}`
  evidence: `{"hint_id": "modal-synthesis-c35e69bda4af89a5", "priority": 0.431941892127, "sample_id": "us-code-2-5326-79178d297c7d0e2e"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```
