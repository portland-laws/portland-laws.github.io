# packet-000074

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000074/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000074/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000074-20260518_144901

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-fef0bae2650a230a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-fef0bae2650a230a` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.044768328285, "hint_id": "modal-synthesis-1d60bc4188d1893f", "priority": 0.422784523629, "reconstruction_loss": 0.422784523629, "sample_id": "us-code-43-3201.-0a9b99db355dece8"}`
  evidence: `{"cosine_similarity": -0.781791091383, "hint_id": "modal-synthesis-5c164366b24441bc", "priority": 0.690759178569, "reconstruction_loss": 0.690759178569, "sample_id": "us-code-46-53406.-637098affd9ed9df"}`
  evidence: `{"cosine_similarity": 0.236748540057, "hint_id": "modal-synthesis-a129329b123e5682", "priority": 0.270767180009, "reconstruction_loss": 0.270767180009, "sample_id": "us-code-15-634g-8119c5b78892376f"}`
  evidence: `{"cosine_similarity": -0.02803421069, "hint_id": "modal-synthesis-beef72033b0f33e1", "priority": 0.489812677841, "reconstruction_loss": 0.489812677841, "sample_id": "us-code-15-182-cc611803c81ebe15"}`
- `program-a44875dad0fa430f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-fef0bae2650a230a` score `0.987913`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.267314048873, "hint_id": "modal-synthesis-09c985f114804f8f", "priority": 0.196876596941, "reconstruction_loss": 0.196876596941, "sample_id": "us-code-12-1151-afebe77e52df6399"}`
  evidence: `{"cosine_similarity": 0.499988728566, "hint_id": "modal-synthesis-12b09c7ccd491e64", "priority": 0.235552264377, "reconstruction_loss": 0.235552264377, "sample_id": "us-code-28-1347-9840756d66d01989"}`
  evidence: `{"cosine_similarity": 0.385849472341, "hint_id": "modal-synthesis-896da7531d5f45f0", "priority": 0.243783037638, "reconstruction_loss": 0.243783037638, "sample_id": "us-code-42-3020a.-d4940147df582f39"}`
  evidence: `{"cosine_similarity": -0.749763460588, "hint_id": "modal-synthesis-c0ad41de9ce358fd", "priority": 0.926183500445, "reconstruction_loss": 0.926183500445, "sample_id": "us-code-20-79e-316329f58ba98698"}`
- `program-1f63d5a5fb5e509c` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-fef0bae2650a230a` score `0.987087`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.307957938364, "hint_id": "modal-synthesis-096da69033da2f14", "priority": 0.499677491556, "reconstruction_loss": 0.499677491556, "sample_id": "us-code-26-7503-acbc015f6a204db3"}`
  evidence: `{"cosine_similarity": 0.237730529348, "hint_id": "modal-synthesis-1da85307de66c91f", "priority": 0.425531857069, "reconstruction_loss": 0.425531857069, "sample_id": "us-code-43-1611.-4d2892d41c4a2bde"}`
  evidence: `{"cosine_similarity": 0.295321605381, "hint_id": "modal-synthesis-296bc1243f54c54c", "priority": 0.401304681294, "reconstruction_loss": 0.401304681294, "sample_id": "us-code-22-6034-cf00fd1585859c38"}`
  evidence: `{"cosine_similarity": 0.199777847112, "hint_id": "modal-synthesis-d57f74ee4d61196b", "priority": 0.479177955346, "reconstruction_loss": 0.479177955346, "sample_id": "us-code-16-460aa-7-59175b1bb60bc5a5"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
