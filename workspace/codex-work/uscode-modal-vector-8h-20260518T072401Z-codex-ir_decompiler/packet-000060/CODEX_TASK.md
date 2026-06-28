# packet-000060

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000060/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000060/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000060-20260518_131415

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-9c30d943bb7c6bae` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9c30d943bb7c6bae` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.525900146303, "hint_id": "modal-synthesis-273c7feead1373e1", "priority": 0.843703547603, "reconstruction_loss": 0.843703547603, "sample_id": "us-code-16-181b-5ee67e9f6427da52"}`
  evidence: `{"cosine_similarity": 0.592988645898, "hint_id": "modal-synthesis-7e16288532f7ead9", "priority": 0.141629011274, "reconstruction_loss": 0.141629011274, "sample_id": "us-code-54-102701.-df9712ab6f6c6b39"}`
  evidence: `{"cosine_similarity": -0.577124353102, "hint_id": "modal-synthesis-a1d8aedf50b15318", "priority": 0.81932781679, "reconstruction_loss": 0.81932781679, "sample_id": "us-code-5-7102-f473abb79a3101c2"}`
  evidence: `{"cosine_similarity": 0.311183751534, "hint_id": "modal-synthesis-dc000838811543e1", "priority": 0.356713667131, "reconstruction_loss": 0.356713667131, "sample_id": "us-code-29-764-4c69f7db3c908042"}`
- `program-0466c53ca2b9f2b4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9c30d943bb7c6bae` score `0.995261`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.399279143465, "hint_id": "modal-synthesis-327e46c2d67c08cb", "priority": 0.685836352512, "reconstruction_loss": 0.685836352512, "sample_id": "us-code-1-106-c6fcaaf1ac721c17"}`
  evidence: `{"cosine_similarity": 0.543817268834, "hint_id": "modal-synthesis-4e6da2d6b0b4b791", "priority": 0.218524219486, "reconstruction_loss": 0.218524219486, "sample_id": "us-code-49-44307.-afc1426bffbab587"}`
  evidence: `{"cosine_similarity": -0.317558884958, "hint_id": "modal-synthesis-957a1b150c572acd", "priority": 0.423270343241, "reconstruction_loss": 0.423270343241, "sample_id": "us-code-26-1396-140b3f7390330119"}`
  evidence: `{"cosine_similarity": -0.195578372254, "hint_id": "modal-synthesis-e265be2ec482cfc0", "priority": 0.545898981886, "reconstruction_loss": 0.545898981886, "sample_id": "us-code-44-1101.-6b5422a28c49042f"}`
- `program-131ad4070ce04340` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9c30d943bb7c6bae` score `0.994726`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.12542603868, "hint_id": "modal-synthesis-270d10f239ffb4eb", "priority": 0.561729914017, "reconstruction_loss": 0.561729914017, "sample_id": "us-code-15-7109-a16f95fd906c6076"}`
  evidence: `{"cosine_similarity": 0.513918035825, "hint_id": "modal-synthesis-584888078edc3a69", "priority": 0.272812312636, "reconstruction_loss": 0.272812312636, "sample_id": "us-code-38-7431-b1671c2367cb2f95"}`
  evidence: `{"cosine_similarity": -0.161144489726, "hint_id": "modal-synthesis-6d712dad00af6872", "priority": 0.545359368684, "reconstruction_loss": 0.545359368684, "sample_id": "us-code-22-2676-234f98bf946590a5"}`
  evidence: `{"cosine_similarity": -0.204561002622, "hint_id": "modal-synthesis-79d9e4636471bfba", "priority": 0.519409844193, "reconstruction_loss": 0.519409844193, "sample_id": "us-code-26-1377-b3a728a9661ff361"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
