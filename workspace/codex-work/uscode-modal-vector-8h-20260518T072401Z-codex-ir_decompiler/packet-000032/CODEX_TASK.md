# packet-000032

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000032/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000032/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000032-20260518_103537

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b355f7ea1e731af3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b355f7ea1e731af3` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.4879802583, "hint_id": "modal-synthesis-6281443a3819c333", "priority": 0.776246209057, "reconstruction_loss": 0.776246209057, "sample_id": "us-code-29-557a-ee90e6ac530776f2"}`
  evidence: `{"cosine_similarity": -0.287443939812, "hint_id": "modal-synthesis-6d8e63d9e18933ab", "priority": 0.752849233989, "reconstruction_loss": 0.752849233989, "sample_id": "us-code-2-5571-bfeba45d205fd273"}`
  evidence: `{"cosine_similarity": 0.06782798554, "hint_id": "modal-synthesis-8927cd27c530c339", "priority": 0.403199456297, "reconstruction_loss": 0.403199456297, "sample_id": "us-code-20-1125-6e491dcbc82b5ae1"}`
  evidence: `{"cosine_similarity": 0.059688276632, "hint_id": "modal-synthesis-c641b158ef184bcd", "priority": 0.288978097554, "reconstruction_loss": 0.288978097554, "sample_id": "us-code-2-65e-e4e1d206526f6c42"}`
- `program-af22c0e989b1385c` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b355f7ea1e731af3` score `0.995224`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.220486535581, "hint_id": "modal-synthesis-49c6638c5deb480c", "priority": 0.403161013854, "reconstruction_loss": 0.403161013854, "sample_id": "us-code-50-2568.-393b91010bbff8d4"}`
  evidence: `{"cosine_similarity": -0.468764795292, "hint_id": "modal-synthesis-8d6f2005b0d8d555", "priority": 0.579481542537, "reconstruction_loss": 0.579481542537, "sample_id": "us-code-36-21507-7fdd5bc25bd26aca"}`
  evidence: `{"cosine_similarity": 0.026550509731, "hint_id": "modal-synthesis-93d8f181a47bc557", "priority": 0.54328354306, "reconstruction_loss": 0.54328354306, "sample_id": "us-code-36-70302-5fbaf4d14557ae37"}`
  evidence: `{"cosine_similarity": 0.010450109745, "hint_id": "modal-synthesis-cef6488978612320", "priority": 0.479150192723, "reconstruction_loss": 0.479150192723, "sample_id": "us-code-2-4122-7a3d09258d54094d"}`
- `program-ff8a4466aeed48a0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b355f7ea1e731af3` score `0.995055`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.604527046143, "hint_id": "modal-synthesis-2cc647926e8904cf", "priority": 0.1442341099, "reconstruction_loss": 0.1442341099, "sample_id": "us-code-22-7102-41ca8d49fc8e7d7b"}`
  evidence: `{"cosine_similarity": -0.416800405638, "hint_id": "modal-synthesis-8711233350076652", "priority": 0.637344526343, "reconstruction_loss": 0.637344526343, "sample_id": "us-code-6-427-32579d5c418cca1b"}`
  evidence: `{"cosine_similarity": 0.126970157443, "hint_id": "modal-synthesis-9bb92c79ca5314fa", "priority": 0.363735159489, "reconstruction_loss": 0.363735159489, "sample_id": "us-code-16-973r-3b4cfef4ca21c7db"}`
  evidence: `{"cosine_similarity": 0.21214783333, "hint_id": "modal-synthesis-9ce98f8bb9132615", "priority": 0.389398374429, "reconstruction_loss": 0.389398374429, "sample_id": "us-code-44-731.-0e92fb9cf6b137c3"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
