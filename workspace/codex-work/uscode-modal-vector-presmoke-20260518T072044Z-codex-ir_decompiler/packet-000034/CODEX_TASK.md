# packet-000034

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000034/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000034/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000034-20260518_072158

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-427ac509c32fac66` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-427ac509c32fac66` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.248449075303, "hint_id": "modal-synthesis-5a8132142edcb13a", "priority": 0.412087752021, "reconstruction_loss": 0.412087752021, "sample_id": "us-code-22-286ee-6742eff5bf2ba235"}`
  evidence: `{"cosine_similarity": -0.014383590963, "hint_id": "modal-synthesis-826b3aee54a23aad", "priority": 0.53893448036, "reconstruction_loss": 0.53893448036, "sample_id": "us-code-25-712d-21dfbbe4ca8c836d"}`
  evidence: `{"cosine_similarity": -0.013895991369, "hint_id": "modal-synthesis-83500861d5652129", "priority": 0.550212006359, "reconstruction_loss": 0.550212006359, "sample_id": "us-code-50-213.-b38307b371a573c8"}`
  evidence: `{"cosine_similarity": 0.469064169429, "hint_id": "modal-synthesis-948129f30b25bf0e", "priority": 0.384294559119, "reconstruction_loss": 0.384294559119, "sample_id": "us-code-20-18-cd9a248f07f46dcf"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
