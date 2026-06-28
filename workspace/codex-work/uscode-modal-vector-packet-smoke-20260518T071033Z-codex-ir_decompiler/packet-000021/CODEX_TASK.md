# packet-000021

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000021/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000021/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000021-20260518_071121

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-bbf409b1b8f8c504` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-bbf409b1b8f8c504` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.540580395517, "hint_id": "modal-synthesis-03f606c2d8febcdf", "priority": 0.373489159488, "reconstruction_loss": 0.373489159488, "sample_id": "us-code-16-460a-9-10cd613b63863e33"}`
  evidence: `{"cosine_similarity": 0.326823809107, "hint_id": "modal-synthesis-11644fa5c567dfb8", "priority": 0.210969427259, "reconstruction_loss": 0.210969427259, "sample_id": "us-code-16-7409-f46d3e8ac1907e49"}`
  evidence: `{"cosine_similarity": 0.097202331705, "hint_id": "modal-synthesis-5736d26a85e0fec5", "priority": 0.559878394372, "reconstruction_loss": 0.559878394372, "sample_id": "us-code-16-5012-62dc845f3ff85622"}`
  evidence: `{"cosine_similarity": 0.058878100335, "hint_id": "modal-synthesis-b022fba0b13f2ab6", "priority": 0.472500837707, "reconstruction_loss": 0.472500837707, "sample_id": "us-code-7-439c-c79a182d2c44a027"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
