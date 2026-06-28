# packet-000051

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000051/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000051/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000051-20260518_121838

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-26bc59a37f4e4168` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-26bc59a37f4e4168` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.183353426868, "hint_id": "modal-synthesis-3f1b02074279de99", "priority": 0.561678623261, "reconstruction_loss": 0.561678623261, "sample_id": "us-code-16-450bb-4-6558c90d70b0fa90"}`
  evidence: `{"cosine_similarity": 0.334048096197, "hint_id": "modal-synthesis-7fd5af7a5094559a", "priority": 0.327832418304, "reconstruction_loss": 0.327832418304, "sample_id": "us-code-36-40305-f1a4fa842e3ab4fe"}`
  evidence: `{"cosine_similarity": -0.501766126432, "hint_id": "modal-synthesis-b21766f0d23f36d7", "priority": 0.516751441214, "reconstruction_loss": 0.516751441214, "sample_id": "us-code-42-4373.-9312773eac9f5c23"}`
  evidence: `{"cosine_similarity": -0.405028378512, "hint_id": "modal-synthesis-e338cd60059eeb5d", "priority": 0.649671055381, "reconstruction_loss": 0.649671055381, "sample_id": "us-code-16-410ww-25-f5b061f26a9aefac"}`
- `program-502aaef5a672ff18` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-26bc59a37f4e4168` score `0.993565`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.508313785262, "hint_id": "modal-synthesis-0df1aa686ddc1d9f", "priority": 0.321302065211, "reconstruction_loss": 0.321302065211, "sample_id": "us-code-42-285b-f3c171d763bcb70b"}`
  evidence: `{"cosine_similarity": 0.328829243515, "hint_id": "modal-synthesis-22035b8032f7a93a", "priority": 0.29810537773, "reconstruction_loss": 0.29810537773, "sample_id": "us-code-42-1886.-bb2116b2bdbea592"}`
  evidence: `{"cosine_similarity": 0.264205293083, "hint_id": "modal-synthesis-3d03d4b890ab6ba7", "priority": 0.317455021447, "reconstruction_loss": 0.317455021447, "sample_id": "us-code-22-2349aa-4-01cb56cfbad267db"}`
  evidence: `{"cosine_similarity": -0.73735395387, "hint_id": "modal-synthesis-ced4f474f95b5bd6", "priority": 1.003521786624, "reconstruction_loss": 1.003521786624, "sample_id": "us-code-16-837f-fd2e84e3568e662b"}`
- `program-1b269a8cb36146d8` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-26bc59a37f4e4168` score `0.993235`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.112767340233, "hint_id": "modal-synthesis-0b50d89dba1ff1c4", "priority": 0.659760328872, "reconstruction_loss": 0.659760328872, "sample_id": "us-code-7-940e-a3ff8dcb36296a51"}`
  evidence: `{"cosine_similarity": 0.336166270628, "hint_id": "modal-synthesis-1bf76ddd270d209d", "priority": 0.332407065601, "reconstruction_loss": 0.332407065601, "sample_id": "us-code-22-2388-29a94e35dc7b5f62"}`
  evidence: `{"cosine_similarity": -0.316020037085, "hint_id": "modal-synthesis-4a894f8b944e4abf", "priority": 0.438000921965, "reconstruction_loss": 0.438000921965, "sample_id": "us-code-18-5001-41ddfa5a2e8f5115"}`
  evidence: `{"cosine_similarity": -0.114668825585, "hint_id": "modal-synthesis-f0b427a95f94aa33", "priority": 0.524538414342, "reconstruction_loss": 0.524538414342, "sample_id": "us-code-10-931f-0e7d94f38d7213b8"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
