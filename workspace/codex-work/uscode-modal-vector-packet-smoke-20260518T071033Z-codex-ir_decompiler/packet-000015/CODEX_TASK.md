# packet-000015

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000015/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000015/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_071105

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-8ab2b52e08bc9842` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8ab2b52e08bc9842` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.011258540027, "hint_id": "modal-synthesis-58a7b994e28f2f84", "priority": 0.391158171391, "reconstruction_loss": 0.391158171391, "sample_id": "us-code-7-5213-0181b6209c09dd47"}`
  evidence: `{"cosine_similarity": -0.131884575213, "hint_id": "modal-synthesis-8cfba8c218b26e40", "priority": 0.418624633672, "reconstruction_loss": 0.418624633672, "sample_id": "us-code-16-4011-c7a2df8c840edce3"}`
  evidence: `{"cosine_similarity": 0.292579019568, "hint_id": "modal-synthesis-a8be05cbc6223423", "priority": 0.357559037967, "reconstruction_loss": 0.357559037967, "sample_id": "us-code-15-144-1321a679e8cdef85"}`
  evidence: `{"cosine_similarity": 0.210800962468, "hint_id": "modal-synthesis-d440710d2b7e60eb", "priority": 0.380748862536, "reconstruction_loss": 0.380748862536, "sample_id": "us-code-25-458aaa-13-9841567e37933284"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
