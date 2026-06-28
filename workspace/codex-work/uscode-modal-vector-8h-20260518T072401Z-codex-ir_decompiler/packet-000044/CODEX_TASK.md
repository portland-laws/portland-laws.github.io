# packet-000044

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000044/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000044/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000044-20260518_114141

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-ac82f51235d8d2df` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ac82f51235d8d2df` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.203651817953, "hint_id": "modal-synthesis-0684ffd72c5c4a3d", "priority": 0.449698080106, "reconstruction_loss": 0.449698080106, "sample_id": "us-code-49-1101.-5b11c8dd27846860"}`
  evidence: `{"cosine_similarity": -0.563458699928, "hint_id": "modal-synthesis-0bd794e5efa445d1", "priority": 0.644034927538, "reconstruction_loss": 0.644034927538, "sample_id": "us-code-29-631-ada12c62e2345a19"}`
  evidence: `{"cosine_similarity": -0.224879218243, "hint_id": "modal-synthesis-a7a980dd318fa548", "priority": 0.67369335849, "reconstruction_loss": 0.67369335849, "sample_id": "us-code-34-10406-fcf92c6730957119"}`
  evidence: `{"cosine_similarity": 0.267166219384, "hint_id": "modal-synthesis-dbd6bccf7b3811c3", "priority": 0.349296983082, "reconstruction_loss": 0.349296983082, "sample_id": "us-code-26-6114-e035bcaedd838e57"}`
- `program-9cf74a1ec95ac578` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ac82f51235d8d2df` score `0.994418`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.30668015056, "hint_id": "modal-synthesis-761afc62f426fa40", "priority": 0.310585069823, "reconstruction_loss": 0.310585069823, "sample_id": "us-code-22-2431b-f4a365be66acef89"}`
  evidence: `{"cosine_similarity": -0.611262905306, "hint_id": "modal-synthesis-7ee35e74f53d3511", "priority": 0.605768280273, "reconstruction_loss": 0.605768280273, "sample_id": "us-code-7-612c-ada48da09f936c05"}`
  evidence: `{"cosine_similarity": 0.334759120408, "hint_id": "modal-synthesis-aa6948298cdcf211", "priority": 0.332982710521, "reconstruction_loss": 0.332982710521, "sample_id": "us-code-25-3908-fe9c213b2ea85f64"}`
  evidence: `{"cosine_similarity": -0.360619602626, "hint_id": "modal-synthesis-f83367657c03f37d", "priority": 0.623097677561, "reconstruction_loss": 0.623097677561, "sample_id": "us-code-44-3309.-2ec76a6634ec0104"}`
- `program-c66788f284e5a80f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ac82f51235d8d2df` score `0.993925`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.07666038526, "hint_id": "modal-synthesis-1ef2ee53f937d4ae", "priority": 0.41759590389, "reconstruction_loss": 0.41759590389, "sample_id": "us-code-33-3028-a3b9b6c70b594a03"}`
  evidence: `{"cosine_similarity": 0.357710624671, "hint_id": "modal-synthesis-8df91bc5300a558f", "priority": 0.207723952226, "reconstruction_loss": 0.207723952226, "sample_id": "us-code-25-187-e3e4561504930551"}`
  evidence: `{"cosine_similarity": -0.12941078123, "hint_id": "modal-synthesis-f464836e809d5fac", "priority": 0.422494137488, "reconstruction_loss": 0.422494137488, "sample_id": "us-code-52-21004.-a4e8272d5ceb9266"}`
  evidence: `{"cosine_similarity": -0.515185672099, "hint_id": "modal-synthesis-ff2625a64afc2fa2", "priority": 0.721584569431, "reconstruction_loss": 0.721584569431, "sample_id": "us-code-19-1501-9e1605418730b9c6"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
