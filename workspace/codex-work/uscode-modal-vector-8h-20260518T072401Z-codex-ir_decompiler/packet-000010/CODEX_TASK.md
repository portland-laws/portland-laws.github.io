# packet-000010

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000010/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000010/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000010-20260518_080253

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-48ab43964cae0cc8` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-48ab43964cae0cc8` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.183668504686, "hint_id": "modal-synthesis-0921372762db3aa5", "priority": 0.527583729034, "reconstruction_loss": 0.527583729034, "sample_id": "us-code-7-7931-866ea6021207281f"}`
  evidence: `{"cosine_similarity": -0.485743940172, "hint_id": "modal-synthesis-26515d0e0e655d74", "priority": 0.758104607513, "reconstruction_loss": 0.758104607513, "sample_id": "us-code-44-737.-c2e056c13b1bf9b1"}`
  evidence: `{"cosine_similarity": -0.632744469481, "hint_id": "modal-synthesis-a6c2acfed1cb6e92", "priority": 0.63205028084, "reconstruction_loss": 0.63205028084, "sample_id": "us-code-22-4141a-0ede47d1cebc8655"}`
  evidence: `{"cosine_similarity": 0.01030974863, "hint_id": "modal-synthesis-a6fc945d389fcdcb", "priority": 0.52732372995, "reconstruction_loss": 0.52732372995, "sample_id": "us-code-38-8172-a95796571b7ca68f"}`
- `program-2f7db2e10081ea31` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-48ab43964cae0cc8` score `0.994748`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.415425839875, "hint_id": "modal-synthesis-07871cf2e1ab879e", "priority": 0.499713182211, "reconstruction_loss": 0.499713182211, "sample_id": "us-code-16-80a-2b97b2cf01190662"}`
  evidence: `{"cosine_similarity": -0.214540006357, "hint_id": "modal-synthesis-2277dd3c36066b06", "priority": 0.607915110566, "reconstruction_loss": 0.607915110566, "sample_id": "us-code-46-56101.-388a7506dd3d0a7e"}`
  evidence: `{"cosine_similarity": -0.185290424931, "hint_id": "modal-synthesis-346233b8ad2fea75", "priority": 0.550273026999, "reconstruction_loss": 0.550273026999, "sample_id": "us-code-22-1465cc-9465fda281180311"}`
  evidence: `{"cosine_similarity": 0.213692745442, "hint_id": "modal-synthesis-fed4e8036d2b6d1b", "priority": 0.274537405818, "reconstruction_loss": 0.274537405818, "sample_id": "us-code-15-9413-f5a8f52590d9aeca"}`
- `program-99c9dabf922d6f24` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-48ab43964cae0cc8` score `0.99472`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.03807801361, "hint_id": "modal-synthesis-0439da441586b1f4", "priority": 0.540469298418, "reconstruction_loss": 0.540469298418, "sample_id": "us-code-5-3346-ca5aa0d4985f9d91"}`
  evidence: `{"cosine_similarity": 0.345863471411, "hint_id": "modal-synthesis-4bc617bd8525746c", "priority": 0.399149744893, "reconstruction_loss": 0.399149744893, "sample_id": "us-code-15-1681v-7645f91f20487c09"}`
  evidence: `{"cosine_similarity": 0.473129268897, "hint_id": "modal-synthesis-93ab706e964a3223", "priority": 0.287484286895, "reconstruction_loss": 0.287484286895, "sample_id": "us-code-38-1720D-93b4ea776e53aa1a"}`
  evidence: `{"cosine_similarity": -0.009523997526, "hint_id": "modal-synthesis-b6f7245b68652bf9", "priority": 0.528981288918, "reconstruction_loss": 0.528981288918, "sample_id": "us-code-15-7704-5f3f0287e06eb49f"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
