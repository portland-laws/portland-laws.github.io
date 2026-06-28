# packet-000033

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000033/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000033/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000033-20260518_071151

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-9bff8b67a346b324` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9bff8b67a346b324` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.507209600604, "hint_id": "modal-synthesis-183b379b34bcbf82", "priority": 0.625943748255, "reconstruction_loss": 0.625943748255, "sample_id": "us-code-26-455-1a66a843f76c6812"}`
  evidence: `{"cosine_similarity": 0.351264734793, "hint_id": "modal-synthesis-26f4f1ce4a9e1c7f", "priority": 0.412779504645, "reconstruction_loss": 0.412779504645, "sample_id": "us-code-49-332.-7864dd8cea9c0675"}`
  evidence: `{"cosine_similarity": 0.359276846921, "hint_id": "modal-synthesis-5e793b4ea2de912b", "priority": 0.271956069227, "reconstruction_loss": 0.271956069227, "sample_id": "us-code-45-797k.-3992b88eab5a40c3"}`
  evidence: `{"cosine_similarity": 0.476897657104, "hint_id": "modal-synthesis-a468e0ff825f89cc", "priority": 0.151684164252, "reconstruction_loss": 0.151684164252, "sample_id": "us-code-49-15301.-22006f67889073a7"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
