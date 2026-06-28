# packet-000063

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000063/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000063/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000063-20260518_133212

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-ccefc58917f9c568` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ccefc58917f9c568` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.166667387482, "hint_id": "modal-synthesis-0941241ee6aebece", "priority": 0.464772360175, "reconstruction_loss": 0.464772360175, "sample_id": "us-code-16-17e-698ac8bdea6aa3ce"}`
  evidence: `{"cosine_similarity": -0.12366569992, "hint_id": "modal-synthesis-67c54587fa2b57ba", "priority": 0.626003010608, "reconstruction_loss": 0.626003010608, "sample_id": "us-code-5-2905-4a941b05c3656a1b"}`
  evidence: `{"cosine_similarity": -0.056880529103, "hint_id": "modal-synthesis-737b60909d7eddc7", "priority": 0.474108403033, "reconstruction_loss": 0.474108403033, "sample_id": "us-code-16-825o-1-94e73fe52265ef75"}`
  evidence: `{"cosine_similarity": -0.761099316679, "hint_id": "modal-synthesis-e6b90a0029dd1959", "priority": 1.023965603579, "reconstruction_loss": 1.023965603579, "sample_id": "us-code-38-7254-164f1ef679273a70"}`
- `program-6b7b8ae55437358f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ccefc58917f9c568` score `0.992872`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.120076752501, "hint_id": "modal-synthesis-1832374daaceee6a", "priority": 0.417662154253, "reconstruction_loss": 0.417662154253, "sample_id": "us-code-16-2305-4530269a2b949a8e"}`
  evidence: `{"cosine_similarity": -0.198943136913, "hint_id": "modal-synthesis-2cbbeedf43e2aaf8", "priority": 0.645943598259, "reconstruction_loss": 0.645943598259, "sample_id": "us-code-18-485-f90083655c04da88"}`
  evidence: `{"cosine_similarity": 0.098530345438, "hint_id": "modal-synthesis-b5034da0932df65a", "priority": 0.63551319279, "reconstruction_loss": 0.63551319279, "sample_id": "us-code-5-7371-ce01882450d379a1"}`
  evidence: `{"cosine_similarity": 0.611219520739, "hint_id": "modal-synthesis-bd36f4e4beabe4ca", "priority": 0.234812235152, "reconstruction_loss": 0.234812235152, "sample_id": "us-code-16-425-8c58ad2a967ffc0c"}`
- `program-1daef6d079aec3e9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ccefc58917f9c568` score `0.992852`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.231232620017, "hint_id": "modal-synthesis-27117a66a5205531", "priority": 0.21482522829, "reconstruction_loss": 0.21482522829, "sample_id": "us-code-16-410iii-3-31dabd5cf6dbed26"}`
  evidence: `{"cosine_similarity": -0.169099386803, "hint_id": "modal-synthesis-7eca15917e199c25", "priority": 0.400661840556, "reconstruction_loss": 0.400661840556, "sample_id": "us-code-18-1719-6841cc7ab2076858"}`
  evidence: `{"cosine_similarity": -0.508767290686, "hint_id": "modal-synthesis-c0c60280e1109b4c", "priority": 0.557622616724, "reconstruction_loss": 0.557622616724, "sample_id": "us-code-50-3091.-8130665c952dd22a"}`
  evidence: `{"cosine_similarity": 0.051097166905, "hint_id": "modal-synthesis-e7063a4fd4beffef", "priority": 0.465206187339, "reconstruction_loss": 0.465206187339, "sample_id": "us-code-22-7636-27b6423bb5340be0"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
