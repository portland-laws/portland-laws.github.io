# packet-000080

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000080/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000080/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000080-20260518_153940

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-f92933cd04df1e07` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f92933cd04df1e07` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 3
  evidence: `{"cosine_similarity": 0.515318854272, "hint_id": "modal-synthesis-03ebbffa0286626d", "priority": 0.336735471121, "reconstruction_loss": 0.336735471121, "sample_id": "us-code-42-4370e.-ddd1f84cd8099640"}`
  evidence: `{"cosine_similarity": -0.324498465044, "hint_id": "modal-synthesis-23dde25ef7e1206c", "priority": 0.755275776585, "reconstruction_loss": 0.755275776585, "sample_id": "us-code-20-2781-494f7b09a487cf62"}`
  evidence: `{"cosine_similarity": 0.409806154476, "hint_id": "modal-synthesis-dcf0878777c14bca", "priority": 0.321417397872, "reconstruction_loss": 0.321417397872, "sample_id": "us-code-47-1457.-04440790685b2dec"}`
- `program-095cef966f4d051d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f92933cd04df1e07` score `0.986065`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.584698758284, "hint_id": "modal-synthesis-269e757de71f2477", "priority": 0.486195541642, "reconstruction_loss": 0.486195541642, "sample_id": "us-code-33-2236-2d2291391528452f"}`
  evidence: `{"cosine_similarity": 0.588575400844, "hint_id": "modal-synthesis-94bd9b17c90e6541", "priority": 0.287409479261, "reconstruction_loss": 0.287409479261, "sample_id": "us-code-22-1156-20d188d5c341c511"}`
  evidence: `{"cosine_similarity": -0.272356932104, "hint_id": "modal-synthesis-be5582670a50fc21", "priority": 0.561860385952, "reconstruction_loss": 0.561860385952, "sample_id": "us-code-7-492-4174ea46ee10e623"}`
  evidence: `{"cosine_similarity": 0.297362583191, "hint_id": "modal-synthesis-fc311358b77fb350", "priority": 0.273667490184, "reconstruction_loss": 0.273667490184, "sample_id": "us-code-18-847-388ed160becc8648"}`
- `program-37def02caa11ff57` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f92933cd04df1e07` score `0.985878`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.161607967017, "hint_id": "modal-synthesis-0197afa6945c96e8", "priority": 0.688670428528, "reconstruction_loss": 0.688670428528, "sample_id": "us-code-16-272c-53498b96929c5f7e"}`
  evidence: `{"cosine_similarity": 0.664860667153, "hint_id": "modal-synthesis-2151239867603315", "priority": 0.09837576533, "reconstruction_loss": 0.09837576533, "sample_id": "us-code-19-2152-963c4912623d7e46"}`
  evidence: `{"cosine_similarity": -0.231583606436, "hint_id": "modal-synthesis-670130a268e01556", "priority": 0.443717159942, "reconstruction_loss": 0.443717159942, "sample_id": "us-code-19-129-1fcce33b4dd6fbde"}`
  evidence: `{"cosine_similarity": 0.007420765856, "hint_id": "modal-synthesis-8702b4d2495ca607", "priority": 0.314992898114, "reconstruction_loss": 0.314992898114, "sample_id": "us-code-19-1613a-a15973dbf00d581e"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
