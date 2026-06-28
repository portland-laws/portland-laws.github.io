# packet-000035

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000035/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000035/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000035-20260518_105210

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-7842f32923dade90` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7842f32923dade90` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.065907364652, "hint_id": "modal-synthesis-4deba4c4aa440c74", "priority": 0.460635897772, "reconstruction_loss": 0.460635897772, "sample_id": "us-code-50-2652.-5b06c52b88d9594d"}`
  evidence: `{"cosine_similarity": 0.31146464301, "hint_id": "modal-synthesis-59acba070c451cd6", "priority": 0.330112994049, "reconstruction_loss": 0.330112994049, "sample_id": "us-code-42-13491.-026a04e2da8612ac"}`
  evidence: `{"cosine_similarity": -0.658952914436, "hint_id": "modal-synthesis-6af79cc46f4367f0", "priority": 0.840847458181, "reconstruction_loss": 0.840847458181, "sample_id": "us-code-10-4842-dfc10da6dae95421"}`
  evidence: `{"cosine_similarity": -0.473785695374, "hint_id": "modal-synthesis-c90cab01f6636a9c", "priority": 0.562196193059, "reconstruction_loss": 0.562196193059, "sample_id": "us-code-16-2104-ded34d780332a5bf"}`
- `program-2a21216d85654d15` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7842f32923dade90` score `0.995226`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.312703547155, "hint_id": "modal-synthesis-4c220f9afc9ffd46", "priority": 0.18195593823, "reconstruction_loss": 0.18195593823, "sample_id": "us-code-25-1300g-5-bf527327ce74ff4c"}`
  evidence: `{"cosine_similarity": 0.495688549407, "hint_id": "modal-synthesis-6c2bb30b635ca6a2", "priority": 0.176596872861, "reconstruction_loss": 0.176596872861, "sample_id": "us-code-15-6004-3ba5f97ffcc47b7a"}`
  evidence: `{"cosine_similarity": 0.205024494875, "hint_id": "modal-synthesis-7713856e6e9f969c", "priority": 0.334066619239, "reconstruction_loss": 0.334066619239, "sample_id": "us-code-26-3121-8413f8804ff8289c"}`
  evidence: `{"cosine_similarity": 0.468913653274, "hint_id": "modal-synthesis-c32b65a1d3c8d945", "priority": 0.286941181386, "reconstruction_loss": 0.286941181386, "sample_id": "us-code-33-3403-36016211c72139b1"}`
- `program-b73e184537f834a4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7842f32923dade90` score `0.995042`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.140962288957, "hint_id": "modal-synthesis-3c799eb4d073da18", "priority": 0.546744313626, "reconstruction_loss": 0.546744313626, "sample_id": "us-code-16-662-12a9f24d409a58db"}`
  evidence: `{"cosine_similarity": 0.847210728371, "hint_id": "modal-synthesis-6d1f56b95c085e95", "priority": 0.169041284688, "reconstruction_loss": 0.169041284688, "sample_id": "us-code-46-41306.-41b23a8d4d02aa16"}`
  evidence: `{"cosine_similarity": -0.168809781226, "hint_id": "modal-synthesis-c723c2b9aaca0107", "priority": 0.710744195343, "reconstruction_loss": 0.710744195343, "sample_id": "us-code-10-8247-c9676075aa8092f3"}`
  evidence: `{"cosine_similarity": 0.247543641225, "hint_id": "modal-synthesis-f16f02e310590105", "priority": 0.46992466083, "reconstruction_loss": 0.46992466083, "sample_id": "us-code-24-6-25077ad498327047"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
