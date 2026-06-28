# packet-000014

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000014/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/packet-000014/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-packet-smoke-20260518T071033Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000014-20260518_071102

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-5779fe0d92060c37` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5779fe0d92060c37` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.623260157897, "hint_id": "modal-synthesis-a56c8d09f1b5a478", "priority": 0.291857326462, "reconstruction_loss": 0.291857326462, "sample_id": "us-code-38-5319-5304ffaedccf083f"}`
  evidence: `{"cosine_similarity": -0.002577020317, "hint_id": "modal-synthesis-d96d65af1264c82d", "priority": 0.475018200831, "reconstruction_loss": 0.475018200831, "sample_id": "us-code-26-6403-ec645fcbda259907"}`
  evidence: `{"cosine_similarity": 0.099422186577, "hint_id": "modal-synthesis-f06296368efcaecb", "priority": 0.400672918879, "reconstruction_loss": 0.400672918879, "sample_id": "us-code-42-1395w-745a0a8249ece403"}`
  evidence: `{"cosine_similarity": -0.630119112778, "hint_id": "modal-synthesis-fb719110f2b0502f", "priority": 0.765790968868, "reconstruction_loss": 0.765790968868, "sample_id": "us-code-7-2153-deb8e23300430df9"}`
- `program-d6d88d8df413137b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5779fe0d92060c37` score `0.73261`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.544911213566, "hint_id": "modal-synthesis-bbf5eb00535eb366", "priority": 0.282904350197, "reconstruction_loss": 0.282904350197, "sample_id": "us-code-2-149a-fb43ab8a1db5b475"}`
  evidence: `{"cosine_similarity": 0.414772919162, "hint_id": "modal-synthesis-e3f2128b47c88ae1", "priority": 0.379192046405, "reconstruction_loss": 0.379192046405, "sample_id": "us-code-20-1070a-31-a5557d79e0f05fab"}`
  evidence: `{"cosine_similarity": 0.141739533857, "hint_id": "modal-synthesis-f132acfd5b28289e", "priority": 0.471645178796, "reconstruction_loss": 0.471645178796, "sample_id": "us-code-19-1522-c9f523c29b6f60ec"}`
  evidence: `{"cosine_similarity": -0.020851807248, "hint_id": "modal-synthesis-fcf0d795be63a4f6", "priority": 0.391388445642, "reconstruction_loss": 0.391388445642, "sample_id": "us-code-42-3789p.-e9f782ad4a060674"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
