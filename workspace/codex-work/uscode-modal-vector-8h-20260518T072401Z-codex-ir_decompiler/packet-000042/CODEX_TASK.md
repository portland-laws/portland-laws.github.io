# packet-000042

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000042/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000042/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000042-20260518_112935

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-e640c9cb7098f50a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e640c9cb7098f50a` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.414644534117, "hint_id": "modal-synthesis-143a4ac9782b5bec", "priority": 0.657722778467, "reconstruction_loss": 0.657722778467, "sample_id": "us-code-25-1300l-6-7954960651e77afd"}`
  evidence: `{"cosine_similarity": -0.063249161789, "hint_id": "modal-synthesis-2b98d47fa6381111", "priority": 0.483534201306, "reconstruction_loss": 0.483534201306, "sample_id": "us-code-26-5702-bb96bb9341ab14db"}`
  evidence: `{"cosine_similarity": -0.378236093099, "hint_id": "modal-synthesis-6c82d8b4b300d474", "priority": 0.564838712251, "reconstruction_loss": 0.564838712251, "sample_id": "us-code-42-1303.-fbeb64885eadfaf5"}`
  evidence: `{"cosine_similarity": -0.216200022973, "hint_id": "modal-synthesis-f93d5e26ab076b6e", "priority": 0.437448592656, "reconstruction_loss": 0.437448592656, "sample_id": "us-code-21-360eee-5922b89e3a41a2d6"}`
- `program-e50dbe26aa225ff7` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e640c9cb7098f50a` score `0.994605`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.766639924945, "hint_id": "modal-synthesis-1c428a45775ea88f", "priority": 0.05579561556, "reconstruction_loss": 0.05579561556, "sample_id": "us-code-7-6a-d9ce3a68898e6313"}`
  evidence: `{"cosine_similarity": 0.535578805722, "hint_id": "modal-synthesis-340696597f51e7b3", "priority": 0.246140074698, "reconstruction_loss": 0.246140074698, "sample_id": "us-code-16-410bbb-3-4898d8ff12219cd3"}`
  evidence: `{"cosine_similarity": 0.448003698315, "hint_id": "modal-synthesis-b295f8fb12eae903", "priority": 0.264831907757, "reconstruction_loss": 0.264831907757, "sample_id": "us-code-22-1457-7ed169294d830c94"}`
  evidence: `{"cosine_similarity": -0.068350239308, "hint_id": "modal-synthesis-eb9235463180985b", "priority": 0.470064420334, "reconstruction_loss": 0.470064420334, "sample_id": "us-code-10-140a-416477bbb419526b"}`
- `program-58c816dd2ec5a690` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e640c9cb7098f50a` score `0.994295`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.302367553893, "hint_id": "modal-synthesis-3a43dd426a5c3b93", "priority": 0.282584580137, "reconstruction_loss": 0.282584580137, "sample_id": "us-code-49-10904.-4e57a60d8b4c8369"}`
  evidence: `{"cosine_similarity": 0.23828347162, "hint_id": "modal-synthesis-89e1f79f7d205054", "priority": 0.313039082509, "reconstruction_loss": 0.313039082509, "sample_id": "us-code-21-360ll-11684335ce2f2caa"}`
  evidence: `{"cosine_similarity": -0.408664197902, "hint_id": "modal-synthesis-b7e0f489045ea78f", "priority": 0.87682197794, "reconstruction_loss": 0.87682197794, "sample_id": "us-code-16-460x-9-908f36f6fcd27905"}`
  evidence: `{"cosine_similarity": -0.283303913292, "hint_id": "modal-synthesis-eb336263b1f5634b", "priority": 0.505966614873, "reconstruction_loss": 0.505966614873, "sample_id": "us-code-30-1264-7adfeffcc1753ff0"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
