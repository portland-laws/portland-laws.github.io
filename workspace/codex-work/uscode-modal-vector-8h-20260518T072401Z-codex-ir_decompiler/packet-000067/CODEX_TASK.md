# packet-000067

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000067/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000067/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000067-20260518_135807

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-5d138dee21387d94` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5d138dee21387d94` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.237251990951, "hint_id": "modal-synthesis-a0d99977d3dc855d", "priority": 0.566719916809, "reconstruction_loss": 0.566719916809, "sample_id": "us-code-49-13506.-0f85d1fcfffc7374"}`
  evidence: `{"cosine_similarity": 0.13841686901, "hint_id": "modal-synthesis-c19dab2f417bc441", "priority": 0.46897350181, "reconstruction_loss": 0.46897350181, "sample_id": "us-code-39-2010-ade65c65cadd8bf7"}`
  evidence: `{"cosine_similarity": -0.157699711299, "hint_id": "modal-synthesis-dd86773db63c7967", "priority": 0.641107018845, "reconstruction_loss": 0.641107018845, "sample_id": "us-code-10-9442-fd367bd6f735d292"}`
  evidence: `{"cosine_similarity": 0.017386057175, "hint_id": "modal-synthesis-f7cc52c933927a31", "priority": 0.547482425534, "reconstruction_loss": 0.547482425534, "sample_id": "us-code-15-3609-f3f2a21fda6eb38d"}`
- `program-2ab96de89a7230d9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5d138dee21387d94` score `0.993739`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.2201808371, "hint_id": "modal-synthesis-09a6a29c24d27557", "priority": 0.460207470898, "reconstruction_loss": 0.460207470898, "sample_id": "us-code-42-300i-7acdc5144f5c977d"}`
  evidence: `{"cosine_similarity": 0.225209610755, "hint_id": "modal-synthesis-6f7f0f948e0d87d0", "priority": 0.280251394435, "reconstruction_loss": 0.280251394435, "sample_id": "us-code-42-7404.-f9e3d5144e298b76"}`
  evidence: `{"cosine_similarity": 0.585685939229, "hint_id": "modal-synthesis-a4cbaaac84a0e11f", "priority": 0.302822112751, "reconstruction_loss": 0.302822112751, "sample_id": "us-code-16-395e-42efa4eebfdf62b3"}`
  evidence: `{"cosine_similarity": -0.566638145413, "hint_id": "modal-synthesis-cdbfa4d080236e2f", "priority": 0.616181251862, "reconstruction_loss": 0.616181251862, "sample_id": "us-code-6-231-362aa52f8a81dd8b"}`
- `program-47101e32bde603f9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5d138dee21387d94` score `0.993156`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.228066737025, "hint_id": "modal-synthesis-59a7fa2b991131e8", "priority": 0.303884832149, "reconstruction_loss": 0.303884832149, "sample_id": "us-code-5-5564-bdff7b035cd4f4cc"}`
  evidence: `{"cosine_similarity": 0.085452577677, "hint_id": "modal-synthesis-5b56cc35033d2e37", "priority": 0.543481265772, "reconstruction_loss": 0.543481265772, "sample_id": "us-code-15-2402-7e27f5e59f9ba39e"}`
  evidence: `{"cosine_similarity": 0.35378636506, "hint_id": "modal-synthesis-aef8ec697fec5d00", "priority": 0.303893581786, "reconstruction_loss": 0.303893581786, "sample_id": "us-code-20-1067j-13aeda303003f5af"}`
  evidence: `{"cosine_similarity": 0.199219356974, "hint_id": "modal-synthesis-d55a9e334d25ca75", "priority": 0.327605212868, "reconstruction_loss": 0.327605212868, "sample_id": "us-code-19-2372a-db684d3dbf8260c1"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
