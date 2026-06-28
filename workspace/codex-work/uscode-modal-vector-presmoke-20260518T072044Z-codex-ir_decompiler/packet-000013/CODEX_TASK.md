# packet-000013

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000013/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000013/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000013-20260518_072114

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-2e9079bda751bdc9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2e9079bda751bdc9` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.142248294992, "hint_id": "modal-synthesis-3d3e5aefad034216", "priority": 0.553286513998, "reconstruction_loss": 0.553286513998, "sample_id": "us-code-7-2242b-7df2adee0c5f0d2e"}`
  evidence: `{"cosine_similarity": -0.061252915048, "hint_id": "modal-synthesis-415a954c633a3b43", "priority": 0.233254695712, "reconstruction_loss": 0.233254695712, "sample_id": "us-code-42-2000a-0766e54fdbc8e842"}`
  evidence: `{"cosine_similarity": -0.490850747382, "hint_id": "modal-synthesis-8e2baa9ee502fc30", "priority": 0.654155660621, "reconstruction_loss": 0.654155660621, "sample_id": "us-code-2-1869-7375b527576801fb"}`
  evidence: `{"cosine_similarity": 0.096527780289, "hint_id": "modal-synthesis-d05a0e35008f4d26", "priority": 0.443882768974, "reconstruction_loss": 0.443882768974, "sample_id": "us-code-10-246-dbcc3c995876961f"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
