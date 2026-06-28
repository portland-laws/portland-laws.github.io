# packet-000028

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/packet-000028/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/packet-000028/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-drain-20260516T155232Z-codex-packet-000028-20260516_155300

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-10729dc60cbbf851` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.028037591261, "hint_id": "modal-synthesis-2f0a2fa90b98848f", "priority": 0.270672581433, "reconstruction_loss": 0.270672581433, "sample_id": "us-code-42-300j-6b7f0e2ba54bb3d6"}`
  evidence: `{"cosine_similarity": -0.022409598628, "hint_id": "modal-synthesis-37057e1dd3728df2", "priority": 0.298514950771, "reconstruction_loss": 0.298514950771, "sample_id": "us-code-42-3041 to 3041f.-f7a25e2c39f54090"}`
- `program-df59e89c25109f65` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-2949459e506ca2f9", "priority": 0.270672581433, "sample_id": "us-code-42-300j-6b7f0e2ba54bb3d6"}`
  evidence: `{"hint_id": "modal-synthesis-765293ad18f6f8b3", "priority": 0.298514950771, "sample_id": "us-code-42-3041 to 3041f.-f7a25e2c39f54090"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```
