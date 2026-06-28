# packet-000025

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000025/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000025/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000025-20260518_094317

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-76506c54ef4aa463` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76506c54ef4aa463` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.629252723257, "hint_id": "modal-synthesis-524fcc151b189d7c", "priority": 0.849200440679, "reconstruction_loss": 0.849200440679, "sample_id": "us-code-30-187-d868840429c41610"}`
  evidence: `{"cosine_similarity": -0.196224104288, "hint_id": "modal-synthesis-674302e85bc5cd94", "priority": 0.477201709271, "reconstruction_loss": 0.477201709271, "sample_id": "us-code-42-15702.-5c7945e145177d2a"}`
  evidence: `{"cosine_similarity": -0.241382344775, "hint_id": "modal-synthesis-7e1eb2f5c60e65de", "priority": 0.519461049305, "reconstruction_loss": 0.519461049305, "sample_id": "us-code-15-294-0239da67fbc11a82"}`
  evidence: `{"cosine_similarity": 0.005585283733, "hint_id": "modal-synthesis-a1cbab558660e91c", "priority": 0.590131112461, "reconstruction_loss": 0.590131112461, "sample_id": "us-code-12-1762-f9671e1be7c49fc5"}`
- `program-c5390408afefc873` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76506c54ef4aa463` score `0.994696`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.252356425916, "hint_id": "modal-synthesis-1e9e9f36aaead97d", "priority": 0.355598482019, "reconstruction_loss": 0.355598482019, "sample_id": "us-code-2-30-75f67eb859d29c60"}`
  evidence: `{"cosine_similarity": -0.440968465794, "hint_id": "modal-synthesis-1ee808a1e8e0cf56", "priority": 0.716239886145, "reconstruction_loss": 0.716239886145, "sample_id": "us-code-12-1715u-ea337e01854bfffa"}`
  evidence: `{"cosine_similarity": -0.349689969238, "hint_id": "modal-synthesis-5e746e2fbc8c3bc3", "priority": 0.504472480735, "reconstruction_loss": 0.504472480735, "sample_id": "us-code-28-1915A-674ea07f31b1be4c"}`
  evidence: `{"cosine_similarity": 0.048617388858, "hint_id": "modal-synthesis-9e5fe82d52b149e1", "priority": 0.455072203066, "reconstruction_loss": 0.455072203066, "sample_id": "us-code-50-2921.-3106bea3f4906157"}`
- `program-6d1b6861bd6035c0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76506c54ef4aa463` score `0.994679`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.35301529389, "hint_id": "modal-synthesis-6c2cbdefeb0310fa", "priority": 0.313529147867, "reconstruction_loss": 0.313529147867, "sample_id": "us-code-15-4712-dc1d9f66b7b15af0"}`
  evidence: `{"cosine_similarity": 0.155714271902, "hint_id": "modal-synthesis-6f9aaff2fabeede7", "priority": 0.417346749164, "reconstruction_loss": 0.417346749164, "sample_id": "us-code-2-123b-a41bd4aaf77abbf3"}`
  evidence: `{"cosine_similarity": -0.216638855967, "hint_id": "modal-synthesis-e62012964e239bd9", "priority": 0.617898614844, "reconstruction_loss": 0.617898614844, "sample_id": "us-code-7-2611-3091131587c51778"}`
  evidence: `{"cosine_similarity": 0.432322213394, "hint_id": "modal-synthesis-f398170645fec828", "priority": 0.174962574343, "reconstruction_loss": 0.174962574343, "sample_id": "us-code-33-1265-058d44e9ce9b3d2d"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
