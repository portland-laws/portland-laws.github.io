# packet-000034

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000034/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000034/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000034-20260518_104523

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-226683292cd35ada` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-226683292cd35ada` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.062063428511, "hint_id": "modal-synthesis-641f0591498ef26b", "priority": 0.703709565362, "reconstruction_loss": 0.703709565362, "sample_id": "us-code-16-777a-2ca4c69bcbe1a8b3"}`
  evidence: `{"cosine_similarity": 0.491170063409, "hint_id": "modal-synthesis-9188224e99457a01", "priority": 0.302883456411, "reconstruction_loss": 0.302883456411, "sample_id": "us-code-7-2003-27c1ec4e1aed3a5d"}`
  evidence: `{"cosine_similarity": -0.556952020285, "hint_id": "modal-synthesis-9865fc920ea60e64", "priority": 0.768638471881, "reconstruction_loss": 0.768638471881, "sample_id": "us-code-19-3739-6e360277ed8b3b1e"}`
  evidence: `{"cosine_similarity": -0.3734874889, "hint_id": "modal-synthesis-9d227d7ef70eb1d1", "priority": 0.783689130069, "reconstruction_loss": 0.783689130069, "sample_id": "us-code-19-2482-1a04330fa0b745bf"}`
- `program-c60ccbedc425457d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-226683292cd35ada` score `0.994276`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.121694592989, "hint_id": "modal-synthesis-3e1cbf8ecab4501a", "priority": 0.498936333848, "reconstruction_loss": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
  evidence: `{"cosine_similarity": -0.171453224395, "hint_id": "modal-synthesis-64f9077abb3a8dde", "priority": 0.576251032019, "reconstruction_loss": 0.576251032019, "sample_id": "us-code-7-1421c-82918530eda35172"}`
  evidence: `{"cosine_similarity": 0.264299780717, "hint_id": "modal-synthesis-96d84f08e4146d82", "priority": 0.338255731335, "reconstruction_loss": 0.338255731335, "sample_id": "us-code-25-201-359bc39e3fbde5c1"}`
  evidence: `{"cosine_similarity": 0.733907242571, "hint_id": "modal-synthesis-bfd1f84f4ca62881", "priority": 0.109517878796, "reconstruction_loss": 0.109517878796, "sample_id": "us-code-15-1508-311f3665421d344f"}`
- `program-f05232614444e3bf` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-226683292cd35ada` score `0.994246`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.29352003265, "hint_id": "modal-synthesis-1ef24e4fface640d", "priority": 0.505307243327, "reconstruction_loss": 0.505307243327, "sample_id": "us-code-15-683-b968efff8e3c29ac"}`
  evidence: `{"cosine_similarity": 0.345326581089, "hint_id": "modal-synthesis-3a77c3734463f900", "priority": 0.401867230737, "reconstruction_loss": 0.401867230737, "sample_id": "us-code-38-8123-63b5bc605b6d367d"}`
  evidence: `{"cosine_similarity": -0.201258519579, "hint_id": "modal-synthesis-7e58c561d42a104f", "priority": 0.593694439096, "reconstruction_loss": 0.593694439096, "sample_id": "us-code-18-593-0948f88285a030f1"}`
  evidence: `{"cosine_similarity": 0.078910887856, "hint_id": "modal-synthesis-a3a333f8864512ee", "priority": 0.395520352889, "reconstruction_loss": 0.395520352889, "sample_id": "us-code-18-2424-e098965751d46fc4"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
