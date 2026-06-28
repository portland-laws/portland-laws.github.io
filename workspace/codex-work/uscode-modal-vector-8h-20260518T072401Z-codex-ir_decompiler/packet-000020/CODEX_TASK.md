# packet-000020

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000020/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000020/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000020-20260518_090936

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-5e4caba45532a236` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5e4caba45532a236` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.09557456686, "hint_id": "modal-synthesis-4c16529b0f038e39", "priority": 0.517636196167, "reconstruction_loss": 0.517636196167, "sample_id": "us-code-25-478-ebbb6cefef299fc2"}`
  evidence: `{"cosine_similarity": 0.030720719037, "hint_id": "modal-synthesis-99b1e393fb3d19ac", "priority": 0.633066003951, "reconstruction_loss": 0.633066003951, "sample_id": "us-code-7-614-6e310cb5e196544b"}`
  evidence: `{"cosine_similarity": 0.038763902706, "hint_id": "modal-synthesis-d4a23f1f7c26c193", "priority": 0.435487259189, "reconstruction_loss": 0.435487259189, "sample_id": "us-code-7-7316-85781f95eae6399d"}`
  evidence: `{"cosine_similarity": -0.554795173894, "hint_id": "modal-synthesis-eac02c369996044f", "priority": 0.764718531138, "reconstruction_loss": 0.764718531138, "sample_id": "us-code-42-11449-759080776a8aad45"}`
- `program-2a6e601e2ffd524f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5e4caba45532a236` score `0.996169`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.439064207914, "hint_id": "modal-synthesis-3eb7abd58209a22d", "priority": 0.310238671651, "reconstruction_loss": 0.310238671651, "sample_id": "us-code-16-460l-12-358f64c7cd5d0eca"}`
  evidence: `{"cosine_similarity": -0.345561956212, "hint_id": "modal-synthesis-5cbec6354307c662", "priority": 0.551431452982, "reconstruction_loss": 0.551431452982, "sample_id": "us-code-28-2674-13d178046c4e836a"}`
  evidence: `{"cosine_similarity": 0.175788694137, "hint_id": "modal-synthesis-d2e0a672647b5dd2", "priority": 0.326906288956, "reconstruction_loss": 0.326906288956, "sample_id": "us-code-7-2270c-eb915fac2e5136af"}`
  evidence: `{"cosine_similarity": -0.07478513428, "hint_id": "modal-synthesis-d71e4d0e93df9e10", "priority": 0.524366605741, "reconstruction_loss": 0.524366605741, "sample_id": "us-code-34-20990-7253cf77ccb49e12"}`
- `program-4277d16478ce4015` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5e4caba45532a236` score `0.996077`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.006239101172, "hint_id": "modal-synthesis-948fe50ae4365cd0", "priority": 0.549640115568, "reconstruction_loss": 0.549640115568, "sample_id": "us-code-29-794f-4d7d67b92220c465"}`
  evidence: `{"cosine_similarity": -0.101251062568, "hint_id": "modal-synthesis-9554ac9cb9b2e3b9", "priority": 0.506081652976, "reconstruction_loss": 0.506081652976, "sample_id": "us-code-24-35-d56c9662a9f6d252"}`
  evidence: `{"cosine_similarity": -0.455499433391, "hint_id": "modal-synthesis-afd1ab428608226c", "priority": 0.502264367504, "reconstruction_loss": 0.502264367504, "sample_id": "us-code-16-583f-44c353a02934be4a"}`
  evidence: `{"cosine_similarity": 0.107702734531, "hint_id": "modal-synthesis-d7bd1d00d6c6ebef", "priority": 0.343826864708, "reconstruction_loss": 0.343826864708, "sample_id": "us-code-19-467-43d1468346683da3"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
