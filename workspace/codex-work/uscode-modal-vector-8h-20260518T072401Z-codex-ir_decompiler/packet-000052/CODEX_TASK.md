# packet-000052

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000052/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000052/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000052-20260518_122448

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-80b6894ed97e25f4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-80b6894ed97e25f4` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.09777035824, "hint_id": "modal-synthesis-253a7d8bda88b677", "priority": 0.496569795265, "reconstruction_loss": 0.496569795265, "sample_id": "us-code-42-3797cc-445d9bb6c7d68792"}`
  evidence: `{"cosine_similarity": 0.219748051273, "hint_id": "modal-synthesis-6ffff1931f3f6de0", "priority": 0.3542224818, "reconstruction_loss": 0.3542224818, "sample_id": "us-code-7-285-dc4b831efb3052da"}`
  evidence: `{"cosine_similarity": -0.245968259541, "hint_id": "modal-synthesis-7aaf7115283d184d", "priority": 0.760404438052, "reconstruction_loss": 0.760404438052, "sample_id": "us-code-28-2322-25d8930c51b5f4f8"}`
  evidence: `{"cosine_similarity": 0.031698938522, "hint_id": "modal-synthesis-e39cbb3ab59fa76f", "priority": 0.51790522551, "reconstruction_loss": 0.51790522551, "sample_id": "us-code-15-649b-8dfcb3fb05dd4cea"}`
- `program-661ebbbcc1446a46` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-80b6894ed97e25f4` score `0.9943`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.22960545871, "hint_id": "modal-synthesis-8a846177709e2b1f", "priority": 0.303356486104, "reconstruction_loss": 0.303356486104, "sample_id": "us-code-48-338 to 338g.-c2b1aeb76673fe26"}`
  evidence: `{"cosine_similarity": 0.658603428402, "hint_id": "modal-synthesis-93d7cae4c4bd1b0b", "priority": 0.193427509167, "reconstruction_loss": 0.193427509167, "sample_id": "us-code-18-492-dda4957e0939c34f"}`
  evidence: `{"cosine_similarity": 0.34129868906, "hint_id": "modal-synthesis-be7094952b6ce314", "priority": 0.345840653586, "reconstruction_loss": 0.345840653586, "sample_id": "us-code-36-230307-9b4115dfe3f6ee62"}`
  evidence: `{"cosine_similarity": -0.239260016105, "hint_id": "modal-synthesis-d2dee340c306ce7c", "priority": 0.638199039813, "reconstruction_loss": 0.638199039813, "sample_id": "us-code-26-741-bddc56288e87db29"}`
- `program-f701644b8b542a24` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-80b6894ed97e25f4` score `0.994177`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.329262755337, "hint_id": "modal-synthesis-51e1e2dba3e6cc3e", "priority": 0.197844854345, "reconstruction_loss": 0.197844854345, "sample_id": "us-code-25-564m-dee77e626d5d85a3"}`
  evidence: `{"cosine_similarity": -0.635744023742, "hint_id": "modal-synthesis-7b3eb260a93627f8", "priority": 0.776976462585, "reconstruction_loss": 0.776976462585, "sample_id": "us-code-42-6932.-4c8798ac1bdcb191"}`
  evidence: `{"cosine_similarity": -0.093410327162, "hint_id": "modal-synthesis-92ab6e1b46ec87e6", "priority": 0.355006179563, "reconstruction_loss": 0.355006179563, "sample_id": "us-code-25-51-b0f49682f9dfa228"}`
  evidence: `{"cosine_similarity": -0.22914181215, "hint_id": "modal-synthesis-df7ec9d5850255b9", "priority": 0.434722412709, "reconstruction_loss": 0.434722412709, "sample_id": "us-code-26-6671-0699b447cf6fa07d"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
