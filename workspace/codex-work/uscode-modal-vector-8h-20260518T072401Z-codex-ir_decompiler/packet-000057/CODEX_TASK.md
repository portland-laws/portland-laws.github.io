# packet-000057

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000057/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000057/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000057-20260518_125748

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b1ea3679ce2a074a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b1ea3679ce2a074a` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.412482007506, "hint_id": "modal-synthesis-236439ac13685d84", "priority": 0.749301210761, "reconstruction_loss": 0.749301210761, "sample_id": "us-code-20-1131d-2a8fb06a45e3babe"}`
  evidence: `{"cosine_similarity": -0.301210288231, "hint_id": "modal-synthesis-771f9cc97b4e8f6b", "priority": 0.583693942863, "reconstruction_loss": 0.583693942863, "sample_id": "us-code-33-1207-a98c982b901e8e5d"}`
  evidence: `{"cosine_similarity": -0.283266884717, "hint_id": "modal-synthesis-a0d3c16b5ebb4112", "priority": 0.554081675403, "reconstruction_loss": 0.554081675403, "sample_id": "us-code-10-2518-f1d0e8da4af38b74"}`
  evidence: `{"cosine_similarity": -0.219707228515, "hint_id": "modal-synthesis-f3c6565729fa751d", "priority": 0.485167210903, "reconstruction_loss": 0.485167210903, "sample_id": "us-code-15-2689-30bb69b633c7dc79"}`
- `program-0e9ff8e1519caf30` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b1ea3679ce2a074a` score `0.995534`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.064165038778, "hint_id": "modal-synthesis-091889aa61724275", "priority": 0.424179575945, "reconstruction_loss": 0.424179575945, "sample_id": "us-code-12-5110-b6b70d5c0ee0dbf1"}`
  evidence: `{"cosine_similarity": 0.568490013897, "hint_id": "modal-synthesis-6b88398130516433", "priority": 0.21769630939, "reconstruction_loss": 0.21769630939, "sample_id": "us-code-7-7803-c794e90d87bff13f"}`
  evidence: `{"cosine_similarity": 0.178279800419, "hint_id": "modal-synthesis-7d9f33ebab0ce347", "priority": 0.351157009877, "reconstruction_loss": 0.351157009877, "sample_id": "us-code-10-1444-9aaddaf528bc681d"}`
  evidence: `{"cosine_similarity": -0.11245614471, "hint_id": "modal-synthesis-95d201f40bb9c7c0", "priority": 0.557164739332, "reconstruction_loss": 0.557164739332, "sample_id": "us-code-29-1185k-be9e330648877b91"}`
- `program-083f6b3dfa8fa1c1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b1ea3679ce2a074a` score `0.99515`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.246597814093, "hint_id": "modal-synthesis-555b138cdf86b95f", "priority": 0.270774952074, "reconstruction_loss": 0.270774952074, "sample_id": "us-code-20-1161x-f37b2c8fc9b87eb2"}`
  evidence: `{"cosine_similarity": -0.283017223379, "hint_id": "modal-synthesis-a07d57dd04048cf3", "priority": 0.396494568565, "reconstruction_loss": 0.396494568565, "sample_id": "us-code-18-440-505acd3b89de4931"}`
  evidence: `{"cosine_similarity": 0.374234205299, "hint_id": "modal-synthesis-cdd4582d3ac440a6", "priority": 0.303566166709, "reconstruction_loss": 0.303566166709, "sample_id": "us-code-26-9706-0300a1ce442886b6"}`
  evidence: `{"cosine_similarity": 0.442560744705, "hint_id": "modal-synthesis-f6db2679c7ec6bea", "priority": 0.200569456461, "reconstruction_loss": 0.200569456461, "sample_id": "us-code-38-7301-90743d5e69bff872"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
