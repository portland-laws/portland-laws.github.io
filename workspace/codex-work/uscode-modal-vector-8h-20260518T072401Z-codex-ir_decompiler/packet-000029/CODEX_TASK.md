# packet-000029

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000029/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000029/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000029-20260518_101414

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-bdbc36976168d94a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-bdbc36976168d94a` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.551111519358, "hint_id": "modal-synthesis-4525b1753eedacf6", "priority": 0.640129310878, "reconstruction_loss": 0.640129310878, "sample_id": "us-code-7-1621-7e4ed6bc2e72e317"}`
  evidence: `{"cosine_similarity": -0.038271627409, "hint_id": "modal-synthesis-471eb2c3513fc2b9", "priority": 0.626918750925, "reconstruction_loss": 0.626918750925, "sample_id": "us-code-20-1092b-384e8ca02bd19815"}`
  evidence: `{"cosine_similarity": -0.473625428967, "hint_id": "modal-synthesis-59d7bb10566dcb48", "priority": 0.376786801596, "reconstruction_loss": 0.376786801596, "sample_id": "us-code-42-283a-9380abe320a44b8e"}`
  evidence: `{"cosine_similarity": -0.444632027719, "hint_id": "modal-synthesis-5dc84707691b73e7", "priority": 0.625586988654, "reconstruction_loss": 0.625586988654, "sample_id": "us-code-16-583j-6-f059330ce82e2639"}`
- `program-76fd6093a0d0391a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-bdbc36976168d94a` score `0.995169`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.207815145585, "hint_id": "modal-synthesis-0a0c001d30e77f0e", "priority": 0.414226038982, "reconstruction_loss": 0.414226038982, "sample_id": "us-code-15-1193-9a13ca81d6192eb7"}`
  evidence: `{"cosine_similarity": -0.100106074799, "hint_id": "modal-synthesis-553ce55447f56eef", "priority": 0.461026336538, "reconstruction_loss": 0.461026336538, "sample_id": "us-code-42-15362.-c7a145faec5f2ad6"}`
  evidence: `{"cosine_similarity": 0.324352950954, "hint_id": "modal-synthesis-9805ae467066ba30", "priority": 0.234154334225, "reconstruction_loss": 0.234154334225, "sample_id": "us-code-42-6930.-5842e7569af665c8"}`
  evidence: `{"cosine_similarity": 0.071699901588, "hint_id": "modal-synthesis-c1b91acb1a15c1f9", "priority": 0.43491676447, "reconstruction_loss": 0.43491676447, "sample_id": "us-code-22-2688-83d45528085ab9e0"}`
- `program-d3d76e135b9d608d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-bdbc36976168d94a` score `0.994692`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.257072265403, "hint_id": "modal-synthesis-28b10cdd4fd52c5e", "priority": 0.5710991146, "reconstruction_loss": 0.5710991146, "sample_id": "us-code-7-2352-2f9c3d9547f523b4"}`
  evidence: `{"cosine_similarity": 0.026273946755, "hint_id": "modal-synthesis-d434ca895916d32e", "priority": 0.332273621628, "reconstruction_loss": 0.332273621628, "sample_id": "us-code-22-2507f-a61e3292cb046c10"}`
  evidence: `{"cosine_similarity": 0.210698142657, "hint_id": "modal-synthesis-e88e91000ba375bb", "priority": 0.510642367769, "reconstruction_loss": 0.510642367769, "sample_id": "us-code-10-2361-23489ad3f4ec6e52"}`
  evidence: `{"cosine_similarity": -0.442435655769, "hint_id": "modal-synthesis-f19cb9bfa0baa743", "priority": 0.49138526336, "reconstruction_loss": 0.49138526336, "sample_id": "us-code-31-3102-3c803c7bc3777976"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
