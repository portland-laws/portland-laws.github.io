# packet-000023

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000023/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000023/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000023-20260518_093025

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-dcaf5d51abd21b7c` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-dcaf5d51abd21b7c` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.173292510588, "hint_id": "modal-synthesis-1ea406a831113ee9", "priority": 0.5401433754, "reconstruction_loss": 0.5401433754, "sample_id": "us-code-15-8815-7a8fe7731c198370"}`
  evidence: `{"cosine_similarity": -0.24660569199, "hint_id": "modal-synthesis-31513cd1f6c0e6b6", "priority": 0.488099020874, "reconstruction_loss": 0.488099020874, "sample_id": "us-code-16-430f-8-91c3b1b55cfdaf46"}`
  evidence: `{"cosine_similarity": -0.53456568694, "hint_id": "modal-synthesis-8123d1e9e7d9d7a5", "priority": 0.839514668046, "reconstruction_loss": 0.839514668046, "sample_id": "us-code-42-285g-3fa5794188fc34c1"}`
  evidence: `{"cosine_similarity": -0.180190219025, "hint_id": "modal-synthesis-92afd2c6cf0ad733", "priority": 0.445993374342, "reconstruction_loss": 0.445993374342, "sample_id": "us-code-16-1605-73b99c7d350fab02"}`
- `program-b1bd516a179a8fef` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-dcaf5d51abd21b7c` score `0.995532`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.365879650492, "hint_id": "modal-synthesis-7e4ba4e9beb27d3e", "priority": 0.252113852016, "reconstruction_loss": 0.252113852016, "sample_id": "us-code-12-3409-1d28e9f71601cb12"}`
  evidence: `{"cosine_similarity": -0.401986752884, "hint_id": "modal-synthesis-89e7ea9ac4308856", "priority": 0.635462234206, "reconstruction_loss": 0.635462234206, "sample_id": "us-code-16-403-3-3f7beeadf54c5093"}`
  evidence: `{"cosine_similarity": 0.093254164961, "hint_id": "modal-synthesis-cb0c29071ce900d4", "priority": 0.470404006762, "reconstruction_loss": 0.470404006762, "sample_id": "us-code-22-288a-de6faeb5565899b5"}`
  evidence: `{"cosine_similarity": -0.231783634377, "hint_id": "modal-synthesis-ed66d848bb5f0007", "priority": 0.367683117565, "reconstruction_loss": 0.367683117565, "sample_id": "us-code-16-956-8d308bcf797c5583"}`
- `program-0f9226fa284e97f2` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-dcaf5d51abd21b7c` score `0.995047`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.472804325862, "hint_id": "modal-synthesis-5fcc9917491d1966", "priority": 0.765890502144, "reconstruction_loss": 0.765890502144, "sample_id": "us-code-10-247-2178e10f8388afbd"}`
  evidence: `{"cosine_similarity": -0.080116108935, "hint_id": "modal-synthesis-73bc5dfb8a38c12f", "priority": 0.542363827503, "reconstruction_loss": 0.542363827503, "sample_id": "us-code-52-10305.-bdcb0d70692f2c2d"}`
  evidence: `{"cosine_similarity": 0.15315676126, "hint_id": "modal-synthesis-b7f934ead110c299", "priority": 0.387742482595, "reconstruction_loss": 0.387742482595, "sample_id": "us-code-28-92-e1782fae7ceb7d0d"}`
  evidence: `{"cosine_similarity": -0.083491069016, "hint_id": "modal-synthesis-de22191c7ee2a000", "priority": 0.581404516111, "reconstruction_loss": 0.581404516111, "sample_id": "us-code-36-150510-8508360bb4174d31"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
