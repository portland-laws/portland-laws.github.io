# packet-000011

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000011/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000011/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000011-20260518_072107

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-73af83db57778d92` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-73af83db57778d92` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.057519312701, "hint_id": "modal-synthesis-0f7cdce7c2290936", "priority": 0.664814243684, "reconstruction_loss": 0.664814243684, "sample_id": "us-code-42-3032a.-5cf2d7da70e73c39"}`
  evidence: `{"cosine_similarity": 0.651605649325, "hint_id": "modal-synthesis-5925539560855f1e", "priority": 0.306522000749, "reconstruction_loss": 0.306522000749, "sample_id": "us-code-16-666-44f7afdbf1e6b0bf"}`
  evidence: `{"cosine_similarity": 0.089613988735, "hint_id": "modal-synthesis-a872024b3e68a3c8", "priority": 0.612660810539, "reconstruction_loss": 0.612660810539, "sample_id": "us-code-29-557-bf030a72c81917fb"}`
  evidence: `{"cosine_similarity": 0.009812741834, "hint_id": "modal-synthesis-be1c66166013a0f0", "priority": 0.549941024976, "reconstruction_loss": 0.549941024976, "sample_id": "us-code-33-3705-03ff1c0656654ca1"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
