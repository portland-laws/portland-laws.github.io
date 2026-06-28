# packet-000022

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000022/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000022/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000022-20260518_071124

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-3dbf12986307eaf5` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-3dbf12986307eaf5` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.6242029832, "hint_id": "modal-synthesis-0a1b6f8ceb8c01fe", "priority": 0.576078774157, "reconstruction_loss": 0.576078774157, "sample_id": "us-code-49-22105.-99b5f570b42829b7"}`
  evidence: `{"cosine_similarity": 0.471851268635, "hint_id": "modal-synthesis-2563fad87ab362b7", "priority": 0.140435256976, "reconstruction_loss": 0.140435256976, "sample_id": "us-code-20-80r-3-d88633103946052c"}`
  evidence: `{"cosine_similarity": 0.644485401012, "hint_id": "modal-synthesis-9c9213a19b275ac6", "priority": 0.148174550588, "reconstruction_loss": 0.148174550588, "sample_id": "us-code-22-262m-ef4ebe45d982a030"}`
  evidence: `{"cosine_similarity": 0.101617649234, "hint_id": "modal-synthesis-d9ed819d65116a6c", "priority": 0.58800997621, "reconstruction_loss": 0.58800997621, "sample_id": "us-code-16-192b-3-812122fc15751c20"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
