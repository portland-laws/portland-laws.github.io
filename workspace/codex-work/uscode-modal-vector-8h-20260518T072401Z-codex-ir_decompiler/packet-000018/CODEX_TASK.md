# packet-000018

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000018/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000018/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000018-20260518_085809

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-70635e572dbdbfdb` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-70635e572dbdbfdb` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.230866725948, "hint_id": "modal-synthesis-565c590d086bcff1", "priority": 0.541176371571, "reconstruction_loss": 0.541176371571, "sample_id": "us-code-42-2000e-08e70c86935b20a5"}`
  evidence: `{"cosine_similarity": -0.436083855479, "hint_id": "modal-synthesis-b9a8ccf63b0b5019", "priority": 0.716029282899, "reconstruction_loss": 0.716029282899, "sample_id": "us-code-10-8477-0b133df625e51d8c"}`
  evidence: `{"cosine_similarity": -0.099008207121, "hint_id": "modal-synthesis-bfae024d2c76130f", "priority": 0.423898859127, "reconstruction_loss": 0.423898859127, "sample_id": "us-code-36-154304-478ad4ab5e8cbcf0"}`
  evidence: `{"cosine_similarity": -0.273835212811, "hint_id": "modal-synthesis-c81d5d9f150daa60", "priority": 0.723040605878, "reconstruction_loss": 0.723040605878, "sample_id": "us-code-42-300d-f00739e3a8a0542e"}`
- `program-9d9fe79d1f17d6ea` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-70635e572dbdbfdb` score `0.994488`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.337089775442, "hint_id": "modal-synthesis-2e6e972cf68b000d", "priority": 0.661873944455, "reconstruction_loss": 0.661873944455, "sample_id": "us-code-36-110301-8f948b5be6e9501a"}`
  evidence: `{"cosine_similarity": -0.273360109639, "hint_id": "modal-synthesis-58e481e64c008631", "priority": 0.561419947891, "reconstruction_loss": 0.561419947891, "sample_id": "us-code-36-21706-db0c3603ae953674"}`
  evidence: `{"cosine_similarity": 0.164754906856, "hint_id": "modal-synthesis-6080a3975afebd88", "priority": 0.298410797156, "reconstruction_loss": 0.298410797156, "sample_id": "us-code-50-171a.-b44deffd2b6380cc"}`
  evidence: `{"cosine_similarity": 0.23764877179, "hint_id": "modal-synthesis-f7f10a0e0c143dec", "priority": 0.212228581027, "reconstruction_loss": 0.212228581027, "sample_id": "us-code-7-1632c-8b2a2851bd662966"}`
- `program-560e52658bdb9530` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-70635e572dbdbfdb` score `0.993886`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.009266948524, "hint_id": "modal-synthesis-02cb2dec7e08d87a", "priority": 0.360910016382, "reconstruction_loss": 0.360910016382, "sample_id": "us-code-43-1349.-0001c7c9a827025c"}`
  evidence: `{"cosine_similarity": 0.204253350856, "hint_id": "modal-synthesis-0b46a02953ffd5b8", "priority": 0.392226209576, "reconstruction_loss": 0.392226209576, "sample_id": "us-code-20-53a-e0a881e6a6301e3f"}`
  evidence: `{"cosine_similarity": 0.139324847193, "hint_id": "modal-synthesis-9a9b4e2ae4803abf", "priority": 0.419932599042, "reconstruction_loss": 0.419932599042, "sample_id": "us-code-31-9107-b7ed943720f3913f"}`
  evidence: `{"cosine_similarity": -0.386940018228, "hint_id": "modal-synthesis-c6a8b2d17d99dc0f", "priority": 0.554515085903, "reconstruction_loss": 0.554515085903, "sample_id": "us-code-31-3125-9a90bf90761a0ef1"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
