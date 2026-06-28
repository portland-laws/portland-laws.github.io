# packet-000032

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000032/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000032/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000032-20260518_071148

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-3693c93fdfac4d5e` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-3693c93fdfac4d5e` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.165918050931, "hint_id": "modal-synthesis-18db4255fa3ca890", "priority": 0.407830054743, "reconstruction_loss": 0.407830054743, "sample_id": "us-code-36-70106-73278ae51e89d117"}`
  evidence: `{"cosine_similarity": 0.917165526962, "hint_id": "modal-synthesis-5e8cb698a3a652e5", "priority": 0.055481214822, "reconstruction_loss": 0.055481214822, "sample_id": "us-code-18-2074-b9a9a415f557f92e"}`
  evidence: `{"cosine_similarity": 0.666504861949, "hint_id": "modal-synthesis-a094585b459cd8fc", "priority": 0.16834282508, "reconstruction_loss": 0.16834282508, "sample_id": "us-code-10-866-8b98b809e95dea95"}`
  evidence: `{"cosine_similarity": 0.031947337369, "hint_id": "modal-synthesis-c591cd170621b2c7", "priority": 0.373308534046, "reconstruction_loss": 0.373308534046, "sample_id": "us-code-15-30-0373429453f33a93"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
