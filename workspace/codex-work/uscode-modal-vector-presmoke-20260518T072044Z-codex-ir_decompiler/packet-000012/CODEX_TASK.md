# packet-000012

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000012/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/packet-000012/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-presmoke-20260518T072044Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000012-20260518_072110

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-326070d1a8d6fcbe` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-326070d1a8d6fcbe` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.576871750268, "hint_id": "modal-synthesis-1846e5841ea06232", "priority": 0.65469988386, "reconstruction_loss": 0.65469988386, "sample_id": "us-code-7-2563-691a5826001c99d0"}`
  evidence: `{"cosine_similarity": 0.060668859399, "hint_id": "modal-synthesis-3bd0ab799a6bc6bd", "priority": 0.407851775836, "reconstruction_loss": 0.407851775836, "sample_id": "us-code-18-796-a1562639a021acf9"}`
  evidence: `{"cosine_similarity": -0.284125646631, "hint_id": "modal-synthesis-e5949d069b7e9f56", "priority": 0.74901868596, "reconstruction_loss": 0.74901868596, "sample_id": "us-code-20-1703-d96d239b54afbdf8"}`
  evidence: `{"cosine_similarity": -0.622630657712, "hint_id": "modal-synthesis-fc57f8c8c9264b05", "priority": 0.929440954476, "reconstruction_loss": 0.929440954476, "sample_id": "us-code-25-313-bf7627b91b7f3810"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
