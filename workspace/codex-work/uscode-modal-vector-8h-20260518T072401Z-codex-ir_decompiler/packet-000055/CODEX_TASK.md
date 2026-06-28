# packet-000055

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000055/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000055/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000055-20260518_124519

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-2673daa7aa7da3f1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2673daa7aa7da3f1` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.287443939812, "hint_id": "modal-synthesis-6d8e63d9e18933ab", "priority": 0.752849233989, "reconstruction_loss": 0.752849233989, "sample_id": "us-code-2-5571-bfeba45d205fd273"}`
  evidence: `{"cosine_similarity": 0.250459153212, "hint_id": "modal-synthesis-892b6a027a8694ea", "priority": 0.330948351658, "reconstruction_loss": 0.330948351658, "sample_id": "us-code-42-10251.-bfe018f8e3609558"}`
  evidence: `{"cosine_similarity": 0.089334838794, "hint_id": "modal-synthesis-a76673fc52678314", "priority": 0.344450855698, "reconstruction_loss": 0.344450855698, "sample_id": "us-code-25-1635-faf2769d771b8f47"}`
  evidence: `{"cosine_similarity": -0.25432888416, "hint_id": "modal-synthesis-c395f1a5196d9dfc", "priority": 0.574306766115, "reconstruction_loss": 0.574306766115, "sample_id": "us-code-24-7-b124660d335aba02"}`
- `program-30e90cce1c6656de` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2673daa7aa7da3f1` score `0.991881`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.105529936762, "hint_id": "modal-synthesis-166903c62c995739", "priority": 0.296574711754, "reconstruction_loss": 0.296574711754, "sample_id": "us-code-19-1882-5b06f2c8b6821c35"}`
  evidence: `{"cosine_similarity": 0.304243252696, "hint_id": "modal-synthesis-5434579ce0ec464d", "priority": 0.316439343948, "reconstruction_loss": 0.316439343948, "sample_id": "us-code-42-300gg-c570d3dac9609cdf"}`
  evidence: `{"cosine_similarity": 0.626403734133, "hint_id": "modal-synthesis-94aed69a623d0c3f", "priority": 0.299718070721, "reconstruction_loss": 0.299718070721, "sample_id": "us-code-22-1064-8bcf9a93d82022cf"}`
  evidence: `{"cosine_similarity": -0.273506600809, "hint_id": "modal-synthesis-9fe6bd484c424b0d", "priority": 0.337458627001, "reconstruction_loss": 0.337458627001, "sample_id": "us-code-22-8771-3e41f3d8cf08a4c5"}`
- `program-b0e6b79dbf225a5a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2673daa7aa7da3f1` score `0.991693`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.327708498637, "hint_id": "modal-synthesis-444980039f82b3da", "priority": 0.257567864313, "reconstruction_loss": 0.257567864313, "sample_id": "us-code-36-151712-a897a7f3fbd445cc"}`
  evidence: `{"cosine_similarity": -0.402095086541, "hint_id": "modal-synthesis-96f8021a2058061e", "priority": 0.49809075842, "reconstruction_loss": 0.49809075842, "sample_id": "us-code-30-541-9c82ca2f186881a4"}`
  evidence: `{"cosine_similarity": 0.400196667009, "hint_id": "modal-synthesis-c09f46fe23c15ae9", "priority": 0.226604358897, "reconstruction_loss": 0.226604358897, "sample_id": "us-code-22-5606-efcc8e5648db1f24"}`
  evidence: `{"cosine_similarity": 0.303941128995, "hint_id": "modal-synthesis-dbd9a37b0663ec8b", "priority": 0.292643582186, "reconstruction_loss": 0.292643582186, "sample_id": "us-code-16-5612-2792b83eb7324466"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
