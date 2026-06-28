# packet-000024

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000024/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000024/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000024-20260518_093639

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-d47765bc563206e8` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d47765bc563206e8` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.273864569934, "hint_id": "modal-synthesis-17b3b803cb6fa0e0", "priority": 0.513537153399, "reconstruction_loss": 0.513537153399, "sample_id": "us-code-16-460uu-44-4bf9d7b47c9eceb7"}`
  evidence: `{"cosine_similarity": -0.271091359435, "hint_id": "modal-synthesis-2f93d7309839a79c", "priority": 0.756953193508, "reconstruction_loss": 0.756953193508, "sample_id": "us-code-21-360bbb-0-98e14cf1a6e12d46"}`
  evidence: `{"cosine_similarity": -0.388083718863, "hint_id": "modal-synthesis-64a85f6fe05e5b9d", "priority": 0.788547113136, "reconstruction_loss": 0.788547113136, "sample_id": "us-code-38-5120-2d682c2727b5e1dc"}`
  evidence: `{"cosine_similarity": 0.370867916504, "hint_id": "modal-synthesis-c83fa829db0fc59c", "priority": 0.253838416071, "reconstruction_loss": 0.253838416071, "sample_id": "us-code-16-539l-1-9f767a192217511f"}`
- `program-97ae60fab301564f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d47765bc563206e8` score `0.991459`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.177009070488, "hint_id": "modal-synthesis-36c7f472403ef35f", "priority": 0.526349126079, "reconstruction_loss": 0.526349126079, "sample_id": "us-code-13-303-bcfda0ce2292fef5"}`
  evidence: `{"cosine_similarity": 0.108153215781, "hint_id": "modal-synthesis-53c83a760ae64b68", "priority": 0.477755204574, "reconstruction_loss": 0.477755204574, "sample_id": "us-code-7-7311-017c4d8b52982ca1"}`
  evidence: `{"cosine_similarity": -0.092098817239, "hint_id": "modal-synthesis-5f633c9d2c210ef5", "priority": 0.432653281983, "reconstruction_loss": 0.432653281983, "sample_id": "us-code-19-3702-fb4c53c1694c688a"}`
  evidence: `{"cosine_similarity": -0.14825348294, "hint_id": "modal-synthesis-e4c51c89fddebd45", "priority": 0.576041570117, "reconstruction_loss": 0.576041570117, "sample_id": "us-code-26-3201-bd4f34df4d869df4"}`
- `program-672217e6b68b2755` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d47765bc563206e8` score `0.990232`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.290571151382, "hint_id": "modal-synthesis-4b54ee9f8ac71b18", "priority": 0.501713471009, "reconstruction_loss": 0.501713471009, "sample_id": "us-code-54-100753.-b2e45d47a388e4ba"}`
  evidence: `{"cosine_similarity": 0.175797019379, "hint_id": "modal-synthesis-5c081a801ea4e13f", "priority": 0.496988833406, "reconstruction_loss": 0.496988833406, "sample_id": "us-code-22-2349cc-1-bc7e7401a6fc42dc"}`
  evidence: `{"cosine_similarity": 0.107566362559, "hint_id": "modal-synthesis-9592c3004a305bdb", "priority": 0.431917359799, "reconstruction_loss": 0.431917359799, "sample_id": "us-code-22-5117-b6be89b991c55bbd"}`
  evidence: `{"cosine_similarity": -0.200809156211, "hint_id": "modal-synthesis-b313a09c781f201c", "priority": 0.675404214175, "reconstruction_loss": 0.675404214175, "sample_id": "us-code-22-275-6f477d74ecc79a10"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
