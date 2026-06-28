# packet-000054

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000054/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000054/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000054-20260518_123545

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-92a25a00026bd143` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-92a25a00026bd143` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.00099597593, "hint_id": "modal-synthesis-2641b6a3a2c7b89e", "priority": 0.495408562502, "reconstruction_loss": 0.495408562502, "sample_id": "us-code-28-3010-ec7367efc1ef5126"}`
  evidence: `{"cosine_similarity": -0.173872785798, "hint_id": "modal-synthesis-556195dbc6451af7", "priority": 0.545698180318, "reconstruction_loss": 0.545698180318, "sample_id": "us-code-42-2624 to 2628.-1baa32ea8781e124"}`
  evidence: `{"cosine_similarity": -0.060857566736, "hint_id": "modal-synthesis-62d0f0de7b8f5c33", "priority": 0.558414263938, "reconstruction_loss": 0.558414263938, "sample_id": "us-code-18-470-b33ab957b2c8c744"}`
  evidence: `{"cosine_similarity": -0.132986800396, "hint_id": "modal-synthesis-9c880385a0da2a96", "priority": 0.424007839448, "reconstruction_loss": 0.424007839448, "sample_id": "us-code-7-1341-45d5b03d9abea474"}`
- `program-42b96cd14984c9fd` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-92a25a00026bd143` score `0.994442`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.028230042286, "hint_id": "modal-synthesis-590d0a4a33d94841", "priority": 0.423569284578, "reconstruction_loss": 0.423569284578, "sample_id": "us-code-2-1825-062b1f41997dd71d"}`
  evidence: `{"cosine_similarity": 0.01416464367, "hint_id": "modal-synthesis-86969229effbbccc", "priority": 0.436349087619, "reconstruction_loss": 0.436349087619, "sample_id": "us-code-28-3009-c96b41b5d2db9915"}`
  evidence: `{"cosine_similarity": -0.008836894359, "hint_id": "modal-synthesis-cc611847ca66685f", "priority": 0.478214553186, "reconstruction_loss": 0.478214553186, "sample_id": "us-code-50-1381 to 1398.-83310e751ed0d7a2"}`
  evidence: `{"cosine_similarity": -0.021868422698, "hint_id": "modal-synthesis-d316808984595902", "priority": 0.585503996154, "reconstruction_loss": 0.585503996154, "sample_id": "us-code-34-10615-8d5581cd1113bc5b"}`
- `program-6349356fc6e4dccf` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-92a25a00026bd143` score `0.993878`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.389746647931, "hint_id": "modal-synthesis-12d608ff12f3d45f", "priority": 0.428115871177, "reconstruction_loss": 0.428115871177, "sample_id": "us-code-16-192b-10-0422f4fd5bfc290b"}`
  evidence: `{"cosine_similarity": -0.14322557567, "hint_id": "modal-synthesis-326799c87bfe35f7", "priority": 0.379099587912, "reconstruction_loss": 0.379099587912, "sample_id": "us-code-42-3796gg-8fa27f093a17bc0c"}`
  evidence: `{"cosine_similarity": 0.003422267662, "hint_id": "modal-synthesis-b97bd3cb76a5fb2d", "priority": 0.527328315236, "reconstruction_loss": 0.527328315236, "sample_id": "us-code-30-49d-450397eabc2ed637"}`
  evidence: `{"cosine_similarity": 0.728731576645, "hint_id": "modal-synthesis-c5dd72ba38cf07d2", "priority": 0.131458581508, "reconstruction_loss": 0.131458581508, "sample_id": "us-code-10-8033-d6f331db0fe8d7bd"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
