# packet-000068

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000068/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000068/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000068-20260518_140310

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-c8e8b06077ebc7d2` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-c8e8b06077ebc7d2` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.662019764084, "hint_id": "modal-synthesis-6108d7a245d71037", "priority": 0.674179271128, "reconstruction_loss": 0.674179271128, "sample_id": "us-code-2-5322-bd39bd238c24f5c3"}`
  evidence: `{"cosine_similarity": -0.534923232188, "hint_id": "modal-synthesis-7c2e857800df3d13", "priority": 0.715205504555, "reconstruction_loss": 0.715205504555, "sample_id": "us-code-15-6403-cf9cff1c03f67391"}`
  evidence: `{"cosine_similarity": 0.115353966727, "hint_id": "modal-synthesis-c01381257950a7f3", "priority": 0.417161974244, "reconstruction_loss": 0.417161974244, "sample_id": "us-code-14-2164-f08c60bfd9e3606a"}`
  evidence: `{"cosine_similarity": 0.183868297381, "hint_id": "modal-synthesis-c5740d33a165b3eb", "priority": 0.417709085249, "reconstruction_loss": 0.417709085249, "sample_id": "us-code-25-1300j-6-960cae3b4783bb4e"}`
- `program-f8ea25bfb3d75527` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-c8e8b06077ebc7d2` score `0.994076`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.093257360432, "hint_id": "modal-synthesis-a4ec3aafe033f522", "priority": 0.343317385507, "reconstruction_loss": 0.343317385507, "sample_id": "us-code-33-561a-f07d6030d4abf6e2"}`
  evidence: `{"cosine_similarity": 0.103897854372, "hint_id": "modal-synthesis-ecb2576262fe0598", "priority": 0.388416167141, "reconstruction_loss": 0.388416167141, "sample_id": "us-code-2-158-772674fb97b30966"}`
  evidence: `{"cosine_similarity": -0.35382366036, "hint_id": "modal-synthesis-fbda33b09544128f", "priority": 0.463660702366, "reconstruction_loss": 0.463660702366, "sample_id": "us-code-7-6409-502d7cea35400f08"}`
  evidence: `{"cosine_similarity": 0.074926059742, "hint_id": "modal-synthesis-fef90fd5e97c825e", "priority": 0.246006770615, "reconstruction_loss": 0.246006770615, "sample_id": "us-code-15-4014-b1673add0797b07b"}`
- `program-8294782093c1120f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-c8e8b06077ebc7d2` score `0.994021`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.199535259792, "hint_id": "modal-synthesis-37db26b40b45f509", "priority": 0.618803896815, "reconstruction_loss": 0.618803896815, "sample_id": "us-code-43-438.-14380fbb55e855c7"}`
  evidence: `{"cosine_similarity": 0.324762611361, "hint_id": "modal-synthesis-96b2daf34717a50f", "priority": 0.232587736588, "reconstruction_loss": 0.232587736588, "sample_id": "us-code-39-3203-320abf45ca56a11d"}`
  evidence: `{"cosine_similarity": -0.052216187879, "hint_id": "modal-synthesis-ab9f9b09a53d8243", "priority": 0.222387976002, "reconstruction_loss": 0.222387976002, "sample_id": "us-code-7-4304-2a3bc1120d0bce4e"}`
  evidence: `{"cosine_similarity": -0.275519057619, "hint_id": "modal-synthesis-fda9b18309ac9332", "priority": 0.7344492076, "reconstruction_loss": 0.7344492076, "sample_id": "us-code-22-7514-4cdd584a1b85cf1c"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
