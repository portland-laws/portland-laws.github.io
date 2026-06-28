# packet-000030

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000030/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000030/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000030-20260518_071143

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-db7043a6ee35b0f5` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db7043a6ee35b0f5` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.275974774094, "hint_id": "modal-synthesis-1970e3f5f2f75e57", "priority": 0.373357393144, "reconstruction_loss": 0.373357393144, "sample_id": "us-code-34-20928-7d6dcae460c25e72"}`
  evidence: `{"cosine_similarity": -0.258184336438, "hint_id": "modal-synthesis-3b9ff34a34bab521", "priority": 0.685806141366, "reconstruction_loss": 0.685806141366, "sample_id": "us-code-42-16042.-619283573cf7c708"}`
  evidence: `{"cosine_similarity": 0.008844691589, "hint_id": "modal-synthesis-5ac6dcfff16fb79e", "priority": 0.612277833011, "reconstruction_loss": 0.612277833011, "sample_id": "us-code-18-3106-74e02e164a46174f"}`
  evidence: `{"cosine_similarity": -0.056337568366, "hint_id": "modal-synthesis-a94eaa38b67f2e6f", "priority": 0.469936186227, "reconstruction_loss": 0.469936186227, "sample_id": "us-code-32-323-a596bbb0bff87650"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
