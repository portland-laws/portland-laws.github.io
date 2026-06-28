# packet-000014

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000014/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000014/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000014-20260518_083454

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-657a0740e76208f3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-657a0740e76208f3` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.416204258709, "hint_id": "modal-synthesis-3792573c1ceab058", "priority": 0.616180313922, "reconstruction_loss": 0.616180313922, "sample_id": "us-code-25-1680l-38f420a040e6face"}`
  evidence: `{"cosine_similarity": -0.61415322886, "hint_id": "modal-synthesis-7e5bf56e95c46aa0", "priority": 0.748607943168, "reconstruction_loss": 0.748607943168, "sample_id": "us-code-29-3121-da7d5224c3804b0e"}`
  evidence: `{"cosine_similarity": -0.379606355185, "hint_id": "modal-synthesis-ba88d4ad97fce6e8", "priority": 0.526491446224, "reconstruction_loss": 0.526491446224, "sample_id": "us-code-43-2105.-77cd7481e6168e1a"}`
  evidence: `{"cosine_similarity": -0.203749505192, "hint_id": "modal-synthesis-d648172762ce094f", "priority": 0.715097392607, "reconstruction_loss": 0.715097392607, "sample_id": "us-code-16-410aaa-50-d93ecd7b2c265bca"}`
- `program-38b248676e485840` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-657a0740e76208f3` score `0.996067`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.291375074724, "hint_id": "modal-synthesis-05f89a9e58d0ad35", "priority": 0.558906764987, "reconstruction_loss": 0.558906764987, "sample_id": "us-code-20-1101a-11fb14b989205ecd"}`
  evidence: `{"cosine_similarity": -0.417393981918, "hint_id": "modal-synthesis-09232ec52e73e4b9", "priority": 0.70642641108, "reconstruction_loss": 0.70642641108, "sample_id": "us-code-15-2623-c273d575f82ca379"}`
  evidence: `{"cosine_similarity": 0.030228705223, "hint_id": "modal-synthesis-27a86a5e53e2f380", "priority": 0.49446180474, "reconstruction_loss": 0.49446180474, "sample_id": "us-code-15-80b-10a-ff0d6edba304626c"}`
  evidence: `{"cosine_similarity": 0.041532808914, "hint_id": "modal-synthesis-a9fd784f6b9771b8", "priority": 0.506816831466, "reconstruction_loss": 0.506816831466, "sample_id": "us-code-46-70305.-2aeef562f40c2fa3"}`
- `program-5c449eefd14784e7` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-657a0740e76208f3` score `0.995782`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.393103965508, "hint_id": "modal-synthesis-692e0b5568bd6497", "priority": 0.350645677415, "reconstruction_loss": 0.350645677415, "sample_id": "us-code-42-1395w-c9a66df7fb1dd0e6"}`
  evidence: `{"cosine_similarity": -0.178862864788, "hint_id": "modal-synthesis-b9f447813476c1a3", "priority": 0.376085513209, "reconstruction_loss": 0.376085513209, "sample_id": "us-code-42-12643.-7bbe762eda7b1af8"}`
  evidence: `{"cosine_similarity": -0.295534273598, "hint_id": "modal-synthesis-ba814271d002d885", "priority": 0.604472978178, "reconstruction_loss": 0.604472978178, "sample_id": "us-code-50-3031.-8c0ec9543c43739d"}`
  evidence: `{"cosine_similarity": 0.16390599411, "hint_id": "modal-synthesis-c7e950cc80684204", "priority": 0.532752337434, "reconstruction_loss": 0.532752337434, "sample_id": "us-code-33-503-acf975b5ffecc9fb"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
