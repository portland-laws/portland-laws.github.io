# packet-000030

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000030/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000030/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000030-20260518_102136

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-8304afdc81c56225` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8304afdc81c56225` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.224791548977, "hint_id": "modal-synthesis-839edee3771e35c9", "priority": 0.497139233567, "reconstruction_loss": 0.497139233567, "sample_id": "us-code-7-1441a-6cfe8dd43437e205"}`
  evidence: `{"cosine_similarity": 0.356518754928, "hint_id": "modal-synthesis-94e0d958eb452dbd", "priority": 0.363433853529, "reconstruction_loss": 0.363433853529, "sample_id": "us-code-42-300gg-3054d2bde0048620"}`
  evidence: `{"cosine_similarity": -0.427953326045, "hint_id": "modal-synthesis-e4243d55660bb647", "priority": 0.842665295762, "reconstruction_loss": 0.842665295762, "sample_id": "us-code-18-982-4031a27b930b8309"}`
  evidence: `{"cosine_similarity": -0.235563158847, "hint_id": "modal-synthesis-f0a804388234fc00", "priority": 0.556331850037, "reconstruction_loss": 0.556331850037, "sample_id": "us-code-15-7508-545c4a1a3f5cf2b1"}`
- `program-bf7be6f459a23912` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8304afdc81c56225` score `0.99533`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.229761808106, "hint_id": "modal-synthesis-324d966120df1fbe", "priority": 0.61400939191, "reconstruction_loss": 0.61400939191, "sample_id": "us-code-7-3603-145b25ec66375aa0"}`
  evidence: `{"cosine_similarity": 0.258814191647, "hint_id": "modal-synthesis-5ffd1f1f8ccd5e94", "priority": 0.377157187772, "reconstruction_loss": 0.377157187772, "sample_id": "us-code-25-3331-87ea6078c016b573"}`
  evidence: `{"cosine_similarity": 0.526832394413, "hint_id": "modal-synthesis-7b536bb7a2086c76", "priority": 0.133507606632, "reconstruction_loss": 0.133507606632, "sample_id": "us-code-50-494.-a97da6e0daf266af"}`
  evidence: `{"cosine_similarity": 0.143507869447, "hint_id": "modal-synthesis-997ab29c59058286", "priority": 0.340833799987, "reconstruction_loss": 0.340833799987, "sample_id": "us-code-42-300ff-896565ebf8799cb4"}`
- `program-a910923a509443a7` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8304afdc81c56225` score `0.995043`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.452369676506, "hint_id": "modal-synthesis-5942bc2710bfec98", "priority": 0.433218694108, "reconstruction_loss": 0.433218694108, "sample_id": "us-code-21-619-6c53879113090cdf"}`
  evidence: `{"cosine_similarity": -0.298215343662, "hint_id": "modal-synthesis-6d3e969ca049e263", "priority": 0.659413870679, "reconstruction_loss": 0.659413870679, "sample_id": "us-code-43-641.-04c06de9984aabe7"}`
  evidence: `{"cosine_similarity": -0.239473362003, "hint_id": "modal-synthesis-976db7eee4acf483", "priority": 0.356233867765, "reconstruction_loss": 0.356233867765, "sample_id": "us-code-16-6804-262347e40e3f269e"}`
  evidence: `{"cosine_similarity": -0.347937623031, "hint_id": "modal-synthesis-9bcf70fda8adf2af", "priority": 0.652330473134, "reconstruction_loss": 0.652330473134, "sample_id": "us-code-42-295.-ce0ec4d108b2d50e"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
