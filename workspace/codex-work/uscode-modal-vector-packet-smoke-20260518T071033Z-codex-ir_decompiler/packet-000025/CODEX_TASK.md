# packet-000025

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000025/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000025/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_071131

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-7f665c1cc6a49260` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7f665c1cc6a49260` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.144849546185, "hint_id": "modal-synthesis-08326d8486ac981c", "priority": 0.57363258655, "reconstruction_loss": 0.57363258655, "sample_id": "us-code-15-278s-775f3e0c4c0d1e93"}`
  evidence: `{"cosine_similarity": 0.219685328542, "hint_id": "modal-synthesis-233672a2554ae1b1", "priority": 0.398714871338, "reconstruction_loss": 0.398714871338, "sample_id": "us-code-8-1454-45ff849cda8d2cb7"}`
  evidence: `{"cosine_similarity": -0.020881154729, "hint_id": "modal-synthesis-89b0a9b184a8f2ef", "priority": 0.438581418447, "reconstruction_loss": 0.438581418447, "sample_id": "us-code-15-767-e74000ac94b57e67"}`
  evidence: `{"cosine_similarity": 0.333986217437, "hint_id": "modal-synthesis-f4520f6d8e9729a5", "priority": 0.488111819598, "reconstruction_loss": 0.488111819598, "sample_id": "us-code-15-1693k-ed185e148b73082c"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
