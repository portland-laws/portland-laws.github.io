# packet-000014

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000014/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000014/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000014-20260518_072117

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-e99ddc41aaae81ea` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e99ddc41aaae81ea` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.133387183404, "hint_id": "modal-synthesis-2dbba7e84f0f5234", "priority": 0.647153571779, "reconstruction_loss": 0.647153571779, "sample_id": "us-code-28-1867-d654c1e7368f110c"}`
  evidence: `{"cosine_similarity": -0.391948180623, "hint_id": "modal-synthesis-476d7171c1ac7f1b", "priority": 0.577717224531, "reconstruction_loss": 0.577717224531, "sample_id": "us-code-50-3331.-f0c6cec23ce187a4"}`
  evidence: `{"cosine_similarity": -0.475289106784, "hint_id": "modal-synthesis-94f8812cae88410d", "priority": 0.730609238634, "reconstruction_loss": 0.730609238634, "sample_id": "us-code-39-411-4638a292b866b0a5"}`
  evidence: `{"cosine_similarity": 0.196912956438, "hint_id": "modal-synthesis-e442bab98a692d81", "priority": 0.388402853538, "reconstruction_loss": 0.388402853538, "sample_id": "us-code-42-290bb-bc61f3bd9ec4f811"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
