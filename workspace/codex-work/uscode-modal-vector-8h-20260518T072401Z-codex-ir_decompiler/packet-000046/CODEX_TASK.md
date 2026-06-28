# packet-000046

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000046/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000046/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000046-20260518_115211

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-9a325e74a3a76575` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9a325e74a3a76575` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.632649452781, "hint_id": "modal-synthesis-701983d3258a9465", "priority": 0.596738710528, "reconstruction_loss": 0.596738710528, "sample_id": "us-code-25-4104-60f38eda8457e605"}`
  evidence: `{"cosine_similarity": 0.416753502874, "hint_id": "modal-synthesis-7dd5df1fa7ad0013", "priority": 0.307334255625, "reconstruction_loss": 0.307334255625, "sample_id": "us-code-16-460l-2-d5a72237fcd0f550"}`
  evidence: `{"cosine_similarity": -0.412890983157, "hint_id": "modal-synthesis-dc59cce35939e488", "priority": 0.737652458627, "reconstruction_loss": 0.737652458627, "sample_id": "us-code-54-308103.-e561e4f16266b6e0"}`
  evidence: `{"cosine_similarity": 0.05634283084, "hint_id": "modal-synthesis-ec7076dd2e00438a", "priority": 0.453666806353, "reconstruction_loss": 0.453666806353, "sample_id": "us-code-49-44919.-d5abf1ea1d3edc77"}`
- `program-9402cc4a22b03572` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9a325e74a3a76575` score `0.994441`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.719967958971, "hint_id": "modal-synthesis-16e47203d3d4c9d7", "priority": 0.152317803307, "reconstruction_loss": 0.152317803307, "sample_id": "us-code-42-12141.-a4fb08cd1f684d37"}`
  evidence: `{"cosine_similarity": -0.120388026206, "hint_id": "modal-synthesis-842e25b5918eac93", "priority": 0.455105208621, "reconstruction_loss": 0.455105208621, "sample_id": "us-code-38-1160-40539597c47abf7c"}`
  evidence: `{"cosine_similarity": -0.300746786665, "hint_id": "modal-synthesis-c7fce3259139d6a7", "priority": 0.732000863509, "reconstruction_loss": 0.732000863509, "sample_id": "us-code-15-9414-0a54386e42477239"}`
  evidence: `{"cosine_similarity": -0.604172490055, "hint_id": "modal-synthesis-d9ff5e1287d643ee", "priority": 0.657997809255, "reconstruction_loss": 0.657997809255, "sample_id": "us-code-42-1436.-1781db31d04cac39"}`
- `program-f69f0e9c139f988d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9a325e74a3a76575` score `0.993914`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.329734866767, "hint_id": "modal-synthesis-9b3d2364e4c8e102", "priority": 0.528068173286, "reconstruction_loss": 0.528068173286, "sample_id": "us-code-42-15205.-2204c1f72fb3f3e5"}`
  evidence: `{"cosine_similarity": 0.084846726557, "hint_id": "modal-synthesis-c358804687e9a05e", "priority": 0.48991840029, "reconstruction_loss": 0.48991840029, "sample_id": "us-code-10-7284-27b21dc53287a67c"}`
  evidence: `{"cosine_similarity": -0.063471253884, "hint_id": "modal-synthesis-daf47594b01eb2df", "priority": 0.526871966408, "reconstruction_loss": 0.526871966408, "sample_id": "us-code-50-1861.-22e16ebb764ce3e8"}`
  evidence: `{"cosine_similarity": -0.027457858857, "hint_id": "modal-synthesis-ea870e1289a3de75", "priority": 0.271694885876, "reconstruction_loss": 0.271694885876, "sample_id": "us-code-7-6917-48a09915bd5dc773"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
