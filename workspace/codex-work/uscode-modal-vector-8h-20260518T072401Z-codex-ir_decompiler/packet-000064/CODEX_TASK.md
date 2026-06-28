# packet-000064

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000064/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000064/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000064-20260518_133955

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-9927abd05a20393b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.393838688215, "hint_id": "modal-synthesis-01d46f9a4b581df3", "priority": 0.580689797434, "reconstruction_loss": 0.580689797434, "sample_id": "us-code-28-363-5f6bfa732952e00b"}`
  evidence: `{"cosine_similarity": 0.427614758839, "hint_id": "modal-synthesis-68aeabe5f6af6a2b", "priority": 0.244477998097, "reconstruction_loss": 0.244477998097, "sample_id": "us-code-25-4163-2eae7188dc5c764c"}`
  evidence: `{"cosine_similarity": -0.373051907987, "hint_id": "modal-synthesis-7c941214f6b488fe", "priority": 0.552639272259, "reconstruction_loss": 0.552639272259, "sample_id": "us-code-46-31109.-99db4340d1749cd8"}`
  evidence: `{"cosine_similarity": -0.753182057899, "hint_id": "modal-synthesis-c9cfd5a01bb38aa5", "priority": 0.653603794375, "reconstruction_loss": 0.653603794375, "sample_id": "us-code-25-1300d-2-13848766d43c7ed4"}`
- `program-0259022affa2db77` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `0.992853`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.621179143149, "hint_id": "modal-synthesis-39210b832bf8fd11", "priority": 0.178369647054, "reconstruction_loss": 0.178369647054, "sample_id": "us-code-7-2143-cbad35cf9d290cf0"}`
  evidence: `{"cosine_similarity": 0.128179243378, "hint_id": "modal-synthesis-5c779d3cdde46c39", "priority": 0.445644549679, "reconstruction_loss": 0.445644549679, "sample_id": "us-code-28-2245-d1ea16b1ac50014b"}`
  evidence: `{"cosine_similarity": -0.186394924636, "hint_id": "modal-synthesis-93424fb108379634", "priority": 0.683242663074, "reconstruction_loss": 0.683242663074, "sample_id": "us-code-20-6082-6a0e64a86e194aa8"}`
  evidence: `{"cosine_similarity": -0.452277523087, "hint_id": "modal-synthesis-be5ef7f07eaafb6e", "priority": 0.611143621452, "reconstruction_loss": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
- `program-7b683915216908c3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9927abd05a20393b` score `0.992527`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.315949751766, "hint_id": "modal-synthesis-2710b7b4c8bde0fc", "priority": 0.516439971177, "reconstruction_loss": 0.516439971177, "sample_id": "us-code-42-2981 to 2981c.-4bed92f2f879fa8f"}`
  evidence: `{"cosine_similarity": -0.33229760373, "hint_id": "modal-synthesis-837aa6806f891a54", "priority": 0.539929254334, "reconstruction_loss": 0.539929254334, "sample_id": "us-code-7-6416-7ac2926c94b239ae"}`
  evidence: `{"cosine_similarity": 0.018374851804, "hint_id": "modal-synthesis-895a91d028b40bbb", "priority": 0.392714684205, "reconstruction_loss": 0.392714684205, "sample_id": "us-code-50-3076.-f7b429a4acb2df69"}`
  evidence: `{"cosine_similarity": 0.221937538484, "hint_id": "modal-synthesis-e17e7a98b5e59525", "priority": 0.504428467593, "reconstruction_loss": 0.504428467593, "sample_id": "us-code-10-8821-c6406d88586fd9c4"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
