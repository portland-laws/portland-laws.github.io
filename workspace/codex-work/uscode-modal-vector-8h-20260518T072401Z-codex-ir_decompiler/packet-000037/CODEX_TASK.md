# packet-000037

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000037/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000037/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000037-20260518_110226

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-189ae92338ab26a2` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-189ae92338ab26a2` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.271533730294, "hint_id": "modal-synthesis-2500f5f069a19216", "priority": 0.235152058308, "reconstruction_loss": 0.235152058308, "sample_id": "us-code-38-3674A-2002a982cfacd345"}`
  evidence: `{"cosine_similarity": -0.469310075638, "hint_id": "modal-synthesis-26b1f5f43a898d4d", "priority": 0.548978011632, "reconstruction_loss": 0.548978011632, "sample_id": "us-code-26-9038-f0e423cec6d53772"}`
  evidence: `{"cosine_similarity": -0.398583075833, "hint_id": "modal-synthesis-6c9557984824f209", "priority": 0.652236533152, "reconstruction_loss": 0.652236533152, "sample_id": "us-code-49-5902.-175e87e3ae6047a1"}`
  evidence: `{"cosine_similarity": -0.57824905372, "hint_id": "modal-synthesis-7120d75dc94dcd15", "priority": 0.707677352064, "reconstruction_loss": 0.707677352064, "sample_id": "us-code-42-3231.-a55a6ca4222ab9bf"}`
- `program-dc7cb04cadca2f2f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-189ae92338ab26a2` score `0.99449`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.239986285386, "hint_id": "modal-synthesis-4b7d6e06c92516c4", "priority": 0.266611779508, "reconstruction_loss": 0.266611779508, "sample_id": "us-code-16-460l-6c-ff7eaf121901cb11"}`
  evidence: `{"cosine_similarity": -0.100531623589, "hint_id": "modal-synthesis-9487366398ebf20c", "priority": 0.578827385736, "reconstruction_loss": 0.578827385736, "sample_id": "us-code-20-107c-b8384c936114f4d1"}`
  evidence: `{"cosine_similarity": -0.186171911985, "hint_id": "modal-synthesis-a6f38d9ab9eee1a2", "priority": 0.523240788447, "reconstruction_loss": 0.523240788447, "sample_id": "us-code-42-17152.-b082effb76574744"}`
  evidence: `{"cosine_similarity": -0.148686909935, "hint_id": "modal-synthesis-ba4e171b60a7226a", "priority": 0.486135537236, "reconstruction_loss": 0.486135537236, "sample_id": "us-code-8-1404-616bc3cad43b70f0"}`
- `program-9f49af2b139bf43b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-189ae92338ab26a2` score `0.993975`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.007831209198, "hint_id": "modal-synthesis-265b63bf75d49917", "priority": 0.531022325936, "reconstruction_loss": 0.531022325936, "sample_id": "us-code-42-5903b.-344172256cfa2cdb"}`
  evidence: `{"cosine_similarity": 0.049683067652, "hint_id": "modal-synthesis-a5b82dcde930138f", "priority": 0.456233996252, "reconstruction_loss": 0.456233996252, "sample_id": "us-code-33-643-8ae4c55e98028043"}`
  evidence: `{"cosine_similarity": -0.219603818808, "hint_id": "modal-synthesis-d7d1afd7d482b462", "priority": 0.595628305756, "reconstruction_loss": 0.595628305756, "sample_id": "us-code-7-2904-dc1069a8022aa947"}`
  evidence: `{"cosine_similarity": 0.342810244859, "hint_id": "modal-synthesis-ee9bf39bc0cdf97f", "priority": 0.371664025947, "reconstruction_loss": 0.371664025947, "sample_id": "us-code-26-6689-7b85edb53794cdde"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
