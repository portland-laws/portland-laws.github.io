# packet-000036

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000036/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000036/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_071159

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-a026ae9976076080` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a026ae9976076080` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.087863559283, "hint_id": "modal-synthesis-9e6240d4e64383bf", "priority": 0.428801459759, "reconstruction_loss": 0.428801459759, "sample_id": "us-code-26-1286-48f398ab3ebddca4"}`
  evidence: `{"cosine_similarity": -0.204631417015, "hint_id": "modal-synthesis-a16d6db1fd7eef1b", "priority": 0.584160617304, "reconstruction_loss": 0.584160617304, "sample_id": "us-code-33-33-4bccb35c29027106"}`
  evidence: `{"cosine_similarity": 0.328779036858, "hint_id": "modal-synthesis-a46757a2d7b523c5", "priority": 0.247817126049, "reconstruction_loss": 0.247817126049, "sample_id": "us-code-16-544p-cb1fddf2f6ece7ed"}`
  evidence: `{"cosine_similarity": 0.299124017363, "hint_id": "modal-synthesis-f1d204a1b223549a", "priority": 0.262634422081, "reconstruction_loss": 0.262634422081, "sample_id": "us-code-12-1148a-4-638b1a5c78baa5c9"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
