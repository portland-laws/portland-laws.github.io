# packet-000039

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000039/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000039/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000039-20260518_111250

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-672896f4a271e1a3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-672896f4a271e1a3` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.567988107463, "hint_id": "modal-synthesis-0f46ba5dcdf4f68e", "priority": 0.669240549753, "reconstruction_loss": 0.669240549753, "sample_id": "us-code-7-7937-a9522d78150a116c"}`
  evidence: `{"cosine_similarity": -0.353442162836, "hint_id": "modal-synthesis-3ae242aeaeabaadf", "priority": 0.724422991021, "reconstruction_loss": 0.724422991021, "sample_id": "us-code-50-4601.-e400e48c6f68c6b3"}`
  evidence: `{"cosine_similarity": 0.245178356803, "hint_id": "modal-synthesis-6e30d6ba1e20dc00", "priority": 0.280909311503, "reconstruction_loss": 0.280909311503, "sample_id": "us-code-22-284j-ab4eaceab7055b89"}`
  evidence: `{"cosine_similarity": 0.225844505805, "hint_id": "modal-synthesis-f134960c83698613", "priority": 0.617463606511, "reconstruction_loss": 0.617463606511, "sample_id": "us-code-25-1264-3f0f36a973b8ba8c"}`
- `program-131f0930d2e08f1b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-672896f4a271e1a3` score `0.994615`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.10384719817, "hint_id": "modal-synthesis-519ea095599ee3cf", "priority": 0.522918461324, "reconstruction_loss": 0.522918461324, "sample_id": "us-code-49-504.-ae0a0b5afcd58ca6"}`
  evidence: `{"cosine_similarity": -0.100714024189, "hint_id": "modal-synthesis-711415afe6317dd3", "priority": 0.465715235845, "reconstruction_loss": 0.465715235845, "sample_id": "us-code-26-6430-917e88c5739e5af4"}`
  evidence: `{"cosine_similarity": 0.543254921172, "hint_id": "modal-synthesis-aa46a2df9a09cea9", "priority": 0.20212478464, "reconstruction_loss": 0.20212478464, "sample_id": "us-code-16-47-1-6e3de5e414cbf6dd"}`
  evidence: `{"cosine_similarity": 0.292096847379, "hint_id": "modal-synthesis-cf04a6c7aea961cd", "priority": 0.27440357732, "reconstruction_loss": 0.27440357732, "sample_id": "us-code-15-2603-abfac481e9c54b86"}`
- `program-5298a819ccb306f3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-672896f4a271e1a3` score `0.99439`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.248303425098, "hint_id": "modal-synthesis-471baceda6ea2f7e", "priority": 0.499054764716, "reconstruction_loss": 0.499054764716, "sample_id": "us-code-25-1778e-25e092f2887fe20f"}`
  evidence: `{"cosine_similarity": 0.531437396077, "hint_id": "modal-synthesis-955e21778285f584", "priority": 0.114725287, "reconstruction_loss": 0.114725287, "sample_id": "us-code-33-1261-8af14efb820bff9d"}`
  evidence: `{"cosine_similarity": 0.106054344178, "hint_id": "modal-synthesis-c9c3bf0cd79c555f", "priority": 0.459383872024, "reconstruction_loss": 0.459383872024, "sample_id": "us-code-11-1511-18fa52ec5f7ed39d"}`
  evidence: `{"cosine_similarity": 0.079653677036, "hint_id": "modal-synthesis-ca072f7b3d4b8061", "priority": 0.325073643501, "reconstruction_loss": 0.325073643501, "sample_id": "us-code-16-669e-4065e5b0df1553b5"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
