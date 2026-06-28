# packet-000035

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000035/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000035/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000035-20260518_071156

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-e00878e40532c3ac` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e00878e40532c3ac` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.615278274427, "hint_id": "modal-synthesis-1dbcb3aefcce9444", "priority": 0.739540963442, "reconstruction_loss": 0.739540963442, "sample_id": "us-code-51-70710.-12fcc705389b92d3"}`
  evidence: `{"cosine_similarity": 0.460730759924, "hint_id": "modal-synthesis-b834d3bc39f83127", "priority": 0.199887713775, "reconstruction_loss": 0.199887713775, "sample_id": "us-code-49-49103.-4d730eb4e74ab8c0"}`
  evidence: `{"cosine_similarity": -0.618679093647, "hint_id": "modal-synthesis-bae62a28f9619314", "priority": 0.534201106079, "reconstruction_loss": 0.534201106079, "sample_id": "us-code-22-6065-b5294523fa516c12"}`
  evidence: `{"cosine_similarity": -0.058278976891, "hint_id": "modal-synthesis-d4a744fd5f55ab40", "priority": 0.265423557767, "reconstruction_loss": 0.265423557767, "sample_id": "us-code-49-31145.-cb5988a31468ff54"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
