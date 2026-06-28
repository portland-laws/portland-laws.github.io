# packet-000056

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000056/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000056/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000056-20260518_125201

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-57be2b3cdc8de4b1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-57be2b3cdc8de4b1` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.395791114693, "hint_id": "modal-synthesis-0da2dff63a30656a", "priority": 0.541418741879, "reconstruction_loss": 0.541418741879, "sample_id": "us-code-30-124-ddfebe0073695f77"}`
  evidence: `{"cosine_similarity": -0.406603833266, "hint_id": "modal-synthesis-18761ee282a64514", "priority": 0.792277110611, "reconstruction_loss": 0.792277110611, "sample_id": "us-code-45-403.-ad60af1a989d19d8"}`
  evidence: `{"cosine_similarity": -0.130820867514, "hint_id": "modal-synthesis-c2ca80dbcd82a643", "priority": 0.472690412818, "reconstruction_loss": 0.472690412818, "sample_id": "us-code-42-1396r-beb958786a37bbc8"}`
  evidence: `{"cosine_similarity": 0.673120904174, "hint_id": "modal-synthesis-ca46a59d54c7830a", "priority": 0.159816610733, "reconstruction_loss": 0.159816610733, "sample_id": "us-code-22-2593a-4fea8d0ee2b45641"}`
- `program-951da8208b33fa08` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-57be2b3cdc8de4b1` score `0.994408`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.354614419661, "hint_id": "modal-synthesis-02d798a0dc19999f", "priority": 0.502426448082, "reconstruction_loss": 0.502426448082, "sample_id": "us-code-38-1523-452ddad4ac026bc4"}`
  evidence: `{"cosine_similarity": 0.724832223895, "hint_id": "modal-synthesis-5ea4327cd4c75ef3", "priority": 0.144756877933, "reconstruction_loss": 0.144756877933, "sample_id": "us-code-38-709-b3d6f77e287cb7d7"}`
  evidence: `{"cosine_similarity": 0.175640781004, "hint_id": "modal-synthesis-e64ade8844bcdfbd", "priority": 0.368961289613, "reconstruction_loss": 0.368961289613, "sample_id": "us-code-16-1402-f974ecb04885f583"}`
  evidence: `{"cosine_similarity": -0.017883693938, "hint_id": "modal-synthesis-f3e141867d0671ca", "priority": 0.427600154824, "reconstruction_loss": 0.427600154824, "sample_id": "us-code-38-1909-90bd9b12148e4f09"}`
- `program-8b3045e0b3302f56` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-57be2b3cdc8de4b1` score `0.993816`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.136401542535, "hint_id": "modal-synthesis-b10f3027669bdb1a", "priority": 0.5253949523, "reconstruction_loss": 0.5253949523, "sample_id": "us-code-10-1585-fd5df2ba5a640c10"}`
  evidence: `{"cosine_similarity": -0.319998864779, "hint_id": "modal-synthesis-b3cfb2d7022b2c09", "priority": 0.57852138111, "reconstruction_loss": 0.57852138111, "sample_id": "us-code-7-5501-74608b2715112bdf"}`
  evidence: `{"cosine_similarity": 0.328869935932, "hint_id": "modal-synthesis-e4a6e3d834ba8b59", "priority": 0.310232577423, "reconstruction_loss": 0.310232577423, "sample_id": "us-code-28-2637-b8a2ff6552a64991"}`
  evidence: `{"cosine_similarity": 0.083331503599, "hint_id": "modal-synthesis-e9a6f52b5a3371e0", "priority": 0.386913973168, "reconstruction_loss": 0.386913973168, "sample_id": "us-code-12-1790b-eaca7020d69e4e1f"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
