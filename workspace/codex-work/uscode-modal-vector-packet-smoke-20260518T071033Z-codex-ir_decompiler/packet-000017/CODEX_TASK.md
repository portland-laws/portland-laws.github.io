# packet-000017

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000017/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000017/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000017-20260518_071112

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b774b7c887b55d56` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b774b7c887b55d56` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.169670105411, "hint_id": "modal-synthesis-2d981f77e6feac7b", "priority": 0.551847934098, "reconstruction_loss": 0.551847934098, "sample_id": "us-code-7-2032-e45599d1c3b7a334"}`
  evidence: `{"cosine_similarity": -0.395176577456, "hint_id": "modal-synthesis-2de74ab6c8461df8", "priority": 0.714468989682, "reconstruction_loss": 0.714468989682, "sample_id": "us-code-33-549-6f82e0c7217912c5"}`
  evidence: `{"cosine_similarity": 0.138427528331, "hint_id": "modal-synthesis-a2b1026615cd1b7e", "priority": 0.374759681351, "reconstruction_loss": 0.374759681351, "sample_id": "us-code-35-313-0cdecd0367a5f7c3"}`
  evidence: `{"cosine_similarity": -0.395249364059, "hint_id": "modal-synthesis-c8c0813489c93587", "priority": 0.826507922731, "reconstruction_loss": 0.826507922731, "sample_id": "us-code-42-16928a.-51cc2f6b0ac5ca81"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
