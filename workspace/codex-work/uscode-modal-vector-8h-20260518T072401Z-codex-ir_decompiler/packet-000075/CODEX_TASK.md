# packet-000075

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000075/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000075/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000075-20260518_145859

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-1c3b141cd69cf781` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-1c3b141cd69cf781` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.199926066876, "hint_id": "modal-synthesis-12e6a9d143b641d5", "priority": 0.602026313027, "reconstruction_loss": 0.602026313027, "sample_id": "us-code-42-8353.-1be9c1de5653d3d0"}`
  evidence: `{"cosine_similarity": 0.148161546051, "hint_id": "modal-synthesis-64f937e368a21a03", "priority": 0.366598701403, "reconstruction_loss": 0.366598701403, "sample_id": "us-code-16-470d-5270f7330f865592"}`
  evidence: `{"cosine_similarity": -0.150742571865, "hint_id": "modal-synthesis-9294ee25442f3325", "priority": 0.449823464988, "reconstruction_loss": 0.449823464988, "sample_id": "us-code-42-19068.-3ef9fba3a555c950"}`
  evidence: `{"cosine_similarity": -0.289736495899, "hint_id": "modal-synthesis-dac07b798a681956", "priority": 0.733073015664, "reconstruction_loss": 0.733073015664, "sample_id": "us-code-10-2645-3506d6f3ea78094e"}`
- `program-7ee9c017c68e14d4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-1c3b141cd69cf781` score `0.992462`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.523444614377, "hint_id": "modal-synthesis-28ae61aff074c4ce", "priority": 0.231512601999, "reconstruction_loss": 0.231512601999, "sample_id": "us-code-48-892.-b52315beaeab9503"}`
  evidence: `{"cosine_similarity": -0.497888992269, "hint_id": "modal-synthesis-442dc9361a447970", "priority": 0.703432916521, "reconstruction_loss": 0.703432916521, "sample_id": "us-code-16-470h-2-a9d5d315afa1b334"}`
  evidence: `{"cosine_similarity": 0.115076280256, "hint_id": "modal-synthesis-6b90b02766b703e0", "priority": 0.283372739754, "reconstruction_loss": 0.283372739754, "sample_id": "us-code-10-2835a-e9b86e5b8dfb0e94"}`
  evidence: `{"cosine_similarity": -0.064157830223, "hint_id": "modal-synthesis-b8068e64f94ef57a", "priority": 0.604680758302, "reconstruction_loss": 0.604680758302, "sample_id": "us-code-42-291m-9a5fc3d8e6571a44"}`
- `program-9a52e2afd532cbf1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-1c3b141cd69cf781` score `0.991754`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.302238285498, "hint_id": "modal-synthesis-6f53f1a946d815f1", "priority": 0.570624112701, "reconstruction_loss": 0.570624112701, "sample_id": "us-code-21-215-28f9be8b1943562c"}`
  evidence: `{"cosine_similarity": 0.091283668845, "hint_id": "modal-synthesis-94a9fd5d432839e6", "priority": 0.326544109322, "reconstruction_loss": 0.326544109322, "sample_id": "us-code-15-1681k-95f85126a15cb560"}`
  evidence: `{"cosine_similarity": 0.30654543527, "hint_id": "modal-synthesis-e4986242b895372b", "priority": 0.241985269213, "reconstruction_loss": 0.241985269213, "sample_id": "us-code-16-590z-1-d59fc82994cc9009"}`
  evidence: `{"cosine_similarity": 0.226336699245, "hint_id": "modal-synthesis-f8dd4fb06994ff38", "priority": 0.352216754891, "reconstruction_loss": 0.352216754891, "sample_id": "us-code-44-514.-95fdfb40d74c155b"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
