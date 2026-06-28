# packet-000073

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000073/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000073/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000073-20260518_144041

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-90f86fde7c260b0b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-90f86fde7c260b0b` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.371810103313, "hint_id": "modal-synthesis-181a33ded0240c87", "priority": 0.56283414876, "reconstruction_loss": 0.56283414876, "sample_id": "us-code-22-2595b-1-9a8fa6c1400541b5"}`
  evidence: `{"cosine_similarity": -0.199442685539, "hint_id": "modal-synthesis-4cf364521b5e9edb", "priority": 0.58609467987, "reconstruction_loss": 0.58609467987, "sample_id": "us-code-49-47126.-2322d39a63b9ba2d"}`
  evidence: `{"cosine_similarity": -0.786604251715, "hint_id": "modal-synthesis-dda30a45f3b3a376", "priority": 0.523167080747, "reconstruction_loss": 0.523167080747, "sample_id": "us-code-46-7503.-38a7bb1327d16036"}`
  evidence: `{"cosine_similarity": 0.366594057995, "hint_id": "modal-synthesis-e03c99ca6ae1a159", "priority": 0.253005627143, "reconstruction_loss": 0.253005627143, "sample_id": "us-code-42-9801.-57bda6766c8a18d9"}`
- `program-94628860a70522ef` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-90f86fde7c260b0b` score `0.993433`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.053855620948, "hint_id": "modal-synthesis-21300e9bb7e50129", "priority": 0.599104543145, "reconstruction_loss": 0.599104543145, "sample_id": "us-code-10-1076c-14f9d0a04acc2314"}`
  evidence: `{"cosine_similarity": -0.235323748168, "hint_id": "modal-synthesis-c69136be284b6cd9", "priority": 0.365037395259, "reconstruction_loss": 0.365037395259, "sample_id": "us-code-16-430a-2-f8a49e51d685faac"}`
  evidence: `{"cosine_similarity": 0.412973038686, "hint_id": "modal-synthesis-daefa1ea1827c4b0", "priority": 0.207501865347, "reconstruction_loss": 0.207501865347, "sample_id": "us-code-47-274.-147d5961fd9102d9"}`
  evidence: `{"cosine_similarity": 0.021117124708, "hint_id": "modal-synthesis-f7687bcf6331f0f6", "priority": 0.320593985028, "reconstruction_loss": 0.320593985028, "sample_id": "us-code-15-77g-c4e632c18f2972f9"}`
- `program-db04f7439ea9eec9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-90f86fde7c260b0b` score `0.993387`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.090676708295, "hint_id": "modal-synthesis-6794d4cb6428c597", "priority": 0.365294233335, "reconstruction_loss": 0.365294233335, "sample_id": "us-code-50-3308a.-6df1f11fe057fc1a"}`
  evidence: `{"cosine_similarity": 0.442824033776, "hint_id": "modal-synthesis-728f5fca76a0a1f3", "priority": 0.151353749328, "reconstruction_loss": 0.151353749328, "sample_id": "us-code-46-10318.-fce306c016fdd990"}`
  evidence: `{"cosine_similarity": -0.161770751236, "hint_id": "modal-synthesis-d219bd5eb2e0baec", "priority": 0.74597942661, "reconstruction_loss": 0.74597942661, "sample_id": "us-code-50-4605 to 4610.-d52505ec5c91561e"}`
  evidence: `{"cosine_similarity": 0.431663200964, "hint_id": "modal-synthesis-eaf02c0a40f73b35", "priority": 0.16413110325, "reconstruction_loss": 0.16413110325, "sample_id": "us-code-18-4-f35ba69f561a11b2"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
