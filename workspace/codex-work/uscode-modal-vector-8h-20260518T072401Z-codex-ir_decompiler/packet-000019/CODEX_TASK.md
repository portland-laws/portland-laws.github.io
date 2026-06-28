# packet-000019

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000019/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000019/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000019-20260518_090719

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-5314d9e3f76151c0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5314d9e3f76151c0` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.002954192345, "hint_id": "modal-synthesis-676006e2af7b03b1", "priority": 0.53336229084, "reconstruction_loss": 0.53336229084, "sample_id": "us-code-42-14044a.-a5d15faf26bebd39"}`
  evidence: `{"cosine_similarity": -0.394634777904, "hint_id": "modal-synthesis-93ffeedc929f1618", "priority": 0.726919232925, "reconstruction_loss": 0.726919232925, "sample_id": "us-code-20-2342-426e84f762e67c7f"}`
  evidence: `{"cosine_similarity": -0.618398468547, "hint_id": "modal-synthesis-b35aaef3b83506e4", "priority": 0.796057891206, "reconstruction_loss": 0.796057891206, "sample_id": "us-code-42-300a-277d94c58adbd5d8"}`
  evidence: `{"cosine_similarity": 0.120387440344, "hint_id": "modal-synthesis-e30dbd88f302ac92", "priority": 0.319822974795, "reconstruction_loss": 0.319822974795, "sample_id": "us-code-36-220510-9da1167519e50cb0"}`
- `program-3db0d84e1dc6db49` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5314d9e3f76151c0` score `0.996381`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.36964894654, "hint_id": "modal-synthesis-19da59e6ad2e7946", "priority": 0.479892456172, "reconstruction_loss": 0.479892456172, "sample_id": "us-code-43-390g-48f9d52a839f3ebf"}`
  evidence: `{"cosine_similarity": 0.111328034608, "hint_id": "modal-synthesis-3433b2c4b8df3020", "priority": 0.354474181057, "reconstruction_loss": 0.354474181057, "sample_id": "us-code-20-9704-55f997c1ab149995"}`
  evidence: `{"cosine_similarity": 0.156778220156, "hint_id": "modal-synthesis-59881dc2ecd50e16", "priority": 0.407602634784, "reconstruction_loss": 0.407602634784, "sample_id": "us-code-12-4711-2999f58c1fffc80e"}`
  evidence: `{"cosine_similarity": -0.002954192345, "hint_id": "modal-synthesis-676006e2af7b03b1", "priority": 0.53336229084, "reconstruction_loss": 0.53336229084, "sample_id": "us-code-42-14044a.-a5d15faf26bebd39"}`
- `program-686e14bddceb791f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5314d9e3f76151c0` score `0.995831`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.164754906856, "hint_id": "modal-synthesis-6080a3975afebd88", "priority": 0.298410797156, "reconstruction_loss": 0.298410797156, "sample_id": "us-code-50-171a.-b44deffd2b6380cc"}`
  evidence: `{"cosine_similarity": 0.181244725249, "hint_id": "modal-synthesis-89cd7d4bf6a2b9a5", "priority": 0.385507019194, "reconstruction_loss": 0.385507019194, "sample_id": "us-code-2-61b-1-a339ae305a87e417"}`
  evidence: `{"cosine_similarity": 0.211168436041, "hint_id": "modal-synthesis-9ec6525b5dc084fa", "priority": 0.349183293716, "reconstruction_loss": 0.349183293716, "sample_id": "us-code-16-823c-06480ad01c8bd740"}`
  evidence: `{"cosine_similarity": -0.386140065404, "hint_id": "modal-synthesis-f110ecf3081cb285", "priority": 0.345934947952, "reconstruction_loss": 0.345934947952, "sample_id": "us-code-21-155-c08159cecb68cc3e"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
