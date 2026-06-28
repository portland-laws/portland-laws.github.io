# packet-000009

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000009/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000009/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000009-20260518_075235

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-f2a506d4d35e390d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f2a506d4d35e390d` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.234770263096, "hint_id": "modal-synthesis-05ab5ee3d49167ef", "priority": 0.540225108428, "reconstruction_loss": 0.540225108428, "sample_id": "us-code-42-13705.-6104fe4efa445f77"}`
  evidence: `{"cosine_similarity": -0.498564022064, "hint_id": "modal-synthesis-22e2c4feaeeed0ae", "priority": 0.700534426581, "reconstruction_loss": 0.700534426581, "sample_id": "us-code-20-6692-a93d8062b79e3918"}`
  evidence: `{"cosine_similarity": 0.014695254641, "hint_id": "modal-synthesis-3ad68111354b3159", "priority": 0.574389187781, "reconstruction_loss": 0.574389187781, "sample_id": "us-code-20-4451-c336bf3b2714e1af"}`
  evidence: `{"cosine_similarity": -0.073747492906, "hint_id": "modal-synthesis-b535739d055ef20a", "priority": 0.629973055709, "reconstruction_loss": 0.629973055709, "sample_id": "us-code-49-30308.-3dcdf369e9002109"}`
- `program-758b9f5cedc3f04a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f2a506d4d35e390d` score `0.994188`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.204100660631, "hint_id": "modal-synthesis-064065cb39ddaef3", "priority": 0.316485570326, "reconstruction_loss": 0.316485570326, "sample_id": "us-code-22-1031-6f5844d1be055539"}`
  evidence: `{"cosine_similarity": -0.299241766305, "hint_id": "modal-synthesis-1549c2b9d1b45312", "priority": 0.34085685794, "reconstruction_loss": 0.34085685794, "sample_id": "us-code-42-6323.-1c7e7d2f53c36e15"}`
  evidence: `{"cosine_similarity": 0.304576324105, "hint_id": "modal-synthesis-67cd2b65489d99db", "priority": 0.347309304674, "reconstruction_loss": 0.347309304674, "sample_id": "us-code-2-74b-55df9e8ab40ae3a5"}`
  evidence: `{"cosine_similarity": 0.072240345965, "hint_id": "modal-synthesis-9b016504fc0f1438", "priority": 0.314161532982, "reconstruction_loss": 0.314161532982, "sample_id": "us-code-48-1572.-8711c64e2d6b256c"}`
- `program-03e69c2a3519a798` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f2a506d4d35e390d` score `0.993751`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.54425764343, "hint_id": "modal-synthesis-37fabae37c844807", "priority": 0.326941559086, "reconstruction_loss": 0.326941559086, "sample_id": "us-code-22-183-9272d613cfbb0f5f"}`
  evidence: `{"cosine_similarity": 0.271955024371, "hint_id": "modal-synthesis-62bbc465f0e3269e", "priority": 0.2567555523, "reconstruction_loss": 0.2567555523, "sample_id": "us-code-49-329.-930183d98235e137"}`
  evidence: `{"cosine_similarity": -0.197245284999, "hint_id": "modal-synthesis-7e2a28e711bf5bd4", "priority": 0.513439327901, "reconstruction_loss": 0.513439327901, "sample_id": "us-code-42-7138.-c336418057a65c1d"}`
  evidence: `{"cosine_similarity": 0.019147254192, "hint_id": "modal-synthesis-d221e320eb6dda03", "priority": 0.388228935042, "reconstruction_loss": 0.388228935042, "sample_id": "us-code-22-286b-1-c03d45d89ce69337"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
