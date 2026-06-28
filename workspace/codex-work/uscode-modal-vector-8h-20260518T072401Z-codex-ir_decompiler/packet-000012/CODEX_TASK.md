# packet-000012

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000012/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000012/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000012-20260518_082114

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-a5ee428cc25dcab7` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a5ee428cc25dcab7` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.623262487429, "hint_id": "modal-synthesis-0020a018b16352a1", "priority": 0.759308336573, "reconstruction_loss": 0.759308336573, "sample_id": "us-code-7-7913-1aaa3fd59c5ff146"}`
  evidence: `{"cosine_similarity": -0.810590272843, "hint_id": "modal-synthesis-2f33b6fd8eaace9b", "priority": 0.919041520622, "reconstruction_loss": 0.919041520622, "sample_id": "us-code-2-31a-2b-a99b26c5ad622cfe"}`
  evidence: `{"cosine_similarity": 0.129992978253, "hint_id": "modal-synthesis-83a1c13f4087d049", "priority": 0.38076657625, "reconstruction_loss": 0.38076657625, "sample_id": "us-code-15-2501-eb4a7816e81bb710"}`
  evidence: `{"cosine_similarity": 0.146502464405, "hint_id": "modal-synthesis-f26d01f713015be0", "priority": 0.623449951677, "reconstruction_loss": 0.623449951677, "sample_id": "us-code-15-828-103d21b6b8cb41ed"}`
- `program-3e52dea1109b2095` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a5ee428cc25dcab7` score `0.994568`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.244026934086, "hint_id": "modal-synthesis-2cb3b198b09f075e", "priority": 0.475941523936, "reconstruction_loss": 0.475941523936, "sample_id": "us-code-20-107e-19233e1a57def2b1"}`
  evidence: `{"cosine_similarity": 0.075834096804, "hint_id": "modal-synthesis-42790dd7a272c4e5", "priority": 0.265186189274, "reconstruction_loss": 0.265186189274, "sample_id": "us-code-26-6050K-56a1d5c4fe56333e"}`
  evidence: `{"cosine_similarity": 0.073927575852, "hint_id": "modal-synthesis-5ff892c611a1e1d1", "priority": 0.360615913058, "reconstruction_loss": 0.360615913058, "sample_id": "us-code-42-9859c.-fad0b07ea51f0884"}`
  evidence: `{"cosine_similarity": 0.125281249312, "hint_id": "modal-synthesis-e94fb51fb1e40285", "priority": 0.410853891586, "reconstruction_loss": 0.410853891586, "sample_id": "us-code-15-657j-e294377a6f05ac13"}`
- `program-d8caf43103250e50` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a5ee428cc25dcab7` score `0.994403`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.080216945513, "hint_id": "modal-synthesis-046ccbe0c6ddc0b9", "priority": 0.439415729232, "reconstruction_loss": 0.439415729232, "sample_id": "us-code-22-8531-63f348cd55efab76"}`
  evidence: `{"cosine_similarity": -0.892975106008, "hint_id": "modal-synthesis-7193b2acc9911b5d", "priority": 0.849499525127, "reconstruction_loss": 0.849499525127, "sample_id": "us-code-12-4712-617af0840f42a51f"}`
  evidence: `{"cosine_similarity": 0.029946293324, "hint_id": "modal-synthesis-adc44c562919ef41", "priority": 0.400142211084, "reconstruction_loss": 0.400142211084, "sample_id": "us-code-8-1535-ab9da61d11ff19b2"}`
  evidence: `{"cosine_similarity": 0.083833112865, "hint_id": "modal-synthesis-b98f3253f7d9290a", "priority": 0.231554081492, "reconstruction_loss": 0.231554081492, "sample_id": "us-code-7-518b-429aff14e8db1068"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
