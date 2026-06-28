# packet-000062

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000062/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000062/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000062-20260518_132601

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-7e5bbab2c74bcdba` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7e5bbab2c74bcdba` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.530885033723, "hint_id": "modal-synthesis-43648eb876511fa2", "priority": 0.543984351894, "reconstruction_loss": 0.543984351894, "sample_id": "us-code-7-1601-18d79058ec62df0c"}`
  evidence: `{"cosine_similarity": -0.189713551663, "hint_id": "modal-synthesis-51d2a0e86a778e56", "priority": 0.531278873574, "reconstruction_loss": 0.531278873574, "sample_id": "us-code-42-300mm-43adce4bd63cace4"}`
  evidence: `{"cosine_similarity": -0.183443422263, "hint_id": "modal-synthesis-a7d1229efc9c5c63", "priority": 0.643896578846, "reconstruction_loss": 0.643896578846, "sample_id": "us-code-25-2304-d4d8eb30520feb87"}`
  evidence: `{"cosine_similarity": 0.458909100852, "hint_id": "modal-synthesis-d8821418f00ed3d4", "priority": 0.228104538652, "reconstruction_loss": 0.228104538652, "sample_id": "us-code-14-106-8639a9da63c4feb5"}`
- `program-2ab42d87e96510d0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7e5bbab2c74bcdba` score `0.995485`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.379021558416, "hint_id": "modal-synthesis-2298c84ac9bae83e", "priority": 0.416811160384, "reconstruction_loss": 0.416811160384, "sample_id": "us-code-16-21b-61e0152089ecceab"}`
  evidence: `{"cosine_similarity": 0.52257782878, "hint_id": "modal-synthesis-963cbd6bb511b2d0", "priority": 0.233722898811, "reconstruction_loss": 0.233722898811, "sample_id": "us-code-12-1748-1cc1d3995cd60d6a"}`
  evidence: `{"cosine_similarity": -0.125911920367, "hint_id": "modal-synthesis-a5f97042640b20cf", "priority": 0.489986816386, "reconstruction_loss": 0.489986816386, "sample_id": "us-code-20-80p-06682e02b637e48d"}`
  evidence: `{"cosine_similarity": -0.335869799928, "hint_id": "modal-synthesis-d1a37ba0277c21d9", "priority": 0.472318733419, "reconstruction_loss": 0.472318733419, "sample_id": "us-code-33-4103-5f28ff96e5da5eab"}`
- `program-b68e7b0d25196295` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7e5bbab2c74bcdba` score `0.995392`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.663280891098, "hint_id": "modal-synthesis-0a6a9db180ede3a2", "priority": 0.122832171493, "reconstruction_loss": 0.122832171493, "sample_id": "us-code-7-2357-3ff09e85daf4e503"}`
  evidence: `{"cosine_similarity": 0.009599587122, "hint_id": "modal-synthesis-6a5d090570a1d285", "priority": 0.343742785631, "reconstruction_loss": 0.343742785631, "sample_id": "us-code-16-1362-270abf70f7e548bf"}`
  evidence: `{"cosine_similarity": -0.172867736339, "hint_id": "modal-synthesis-94f3db791427f332", "priority": 0.494597578237, "reconstruction_loss": 0.494597578237, "sample_id": "us-code-22-283ff-89fc462eb51d9107"}`
  evidence: `{"cosine_similarity": 0.59047820555, "hint_id": "modal-synthesis-a45f21a5bfecdf87", "priority": 0.127409960208, "reconstruction_loss": 0.127409960208, "sample_id": "us-code-10-5512-4b2abf3c72275212"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Treat the packet's program_synthesis_scope metadata as the AST/write-scope boundary; keep edits inside that lane unless a test requires a small adjacent change.
When multiple TODOs are present, treat their semantic_bundle_key or vector_bundle metadata as evidence for one generalized compiler/decompiler/frame improvement over one-off sample fixes.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-7e5bbab2c74bcdba`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7e5bbab2c74bcdba` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.486816085742`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-2304-d4d8eb30520feb87, us-code-7-1601-18d79058ec62df0c, us-code-42-300mm-43adce4bd63cace4, us-code-14-106-8639a9da63c4feb5`
  evidence: `{"cosine_similarity": -0.530885033723, "hint_id": "modal-synthesis-43648eb876511fa2", "priority": 0.543984351894, "reconstruction_loss": 0.543984351894, "sample_id": "us-code-7-1601-18d79058ec62df0c"}`
  evidence: `{"cosine_similarity": -0.189713551663, "hint_id": "modal-synthesis-51d2a0e86a778e56", "priority": 0.531278873574, "reconstruction_loss": 0.531278873574, "sample_id": "us-code-42-300mm-43adce4bd63cace4"}`
  evidence: `{"cosine_similarity": -0.183443422263, "hint_id": "modal-synthesis-a7d1229efc9c5c63", "priority": 0.643896578846, "reconstruction_loss": 0.643896578846, "sample_id": "us-code-25-2304-d4d8eb30520feb87"}`
  evidence: `{"cosine_similarity": 0.458909100852, "hint_id": "modal-synthesis-d8821418f00ed3d4", "priority": 0.228104538652, "reconstruction_loss": 0.228104538652, "sample_id": "us-code-14-106-8639a9da63c4feb5"}`
- `program-2ab42d87e96510d0`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7e5bbab2c74bcdba` score `0.995485`
  loss: `autoencoder_residual_cluster` = `0.40320990225`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-20-80p-06682e02b637e48d, us-code-33-4103-5f28ff96e5da5eab, us-code-16-21b-61e0152089ecceab, us-code-12-1748-1cc1d3995cd60d6a`
  evidence: `{"cosine_similarity": 0.379021558416, "hint_id": "modal-synthesis-2298c84ac9bae83e", "priority": 0.416811160384, "reconstruction_loss": 0.416811160384, "sample_id": "us-code-16-21b-61e0152089ecceab"}`
  evidence: `{"cosine_similarity": 0.52257782878, "hint_id": "modal-synthesis-963cbd6bb511b2d0", "priority": 0.233722898811, "reconstruction_loss": 0.233722898811, "sample_id": "us-code-12-1748-1cc1d3995cd60d6a"}`
  evidence: `{"cosine_similarity": -0.125911920367, "hint_id": "modal-synthesis-a5f97042640b20cf", "priority": 0.489986816386, "reconstruction_loss": 0.489986816386, "sample_id": "us-code-20-80p-06682e02b637e48d"}`
  evidence: `{"cosine_similarity": -0.335869799928, "hint_id": "modal-synthesis-d1a37ba0277c21d9", "priority": 0.472318733419, "reconstruction_loss": 0.472318733419, "sample_id": "us-code-33-4103-5f28ff96e5da5eab"}`
- `program-b68e7b0d25196295`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-7e5bbab2c74bcdba` score `0.995392`
  loss: `autoencoder_residual_cluster` = `0.272145623892`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-22-283ff-89fc462eb51d9107, us-code-16-1362-270abf70f7e548bf, us-code-10-5512-4b2abf3c72275212, us-code-7-2357-3ff09e85daf4e503`
  evidence: `{"cosine_similarity": 0.663280891098, "hint_id": "modal-synthesis-0a6a9db180ede3a2", "priority": 0.122832171493, "reconstruction_loss": 0.122832171493, "sample_id": "us-code-7-2357-3ff09e85daf4e503"}`
  evidence: `{"cosine_similarity": 0.009599587122, "hint_id": "modal-synthesis-6a5d090570a1d285", "priority": 0.343742785631, "reconstruction_loss": 0.343742785631, "sample_id": "us-code-16-1362-270abf70f7e548bf"}`
  evidence: `{"cosine_similarity": -0.172867736339, "hint_id": "modal-synthesis-94f3db791427f332", "priority": 0.494597578237, "reconstruction_loss": 0.494597578237, "sample_id": "us-code-22-283ff-89fc462eb51d9107"}`
  evidence: `{"cosine_similarity": 0.59047820555, "hint_id": "modal-synthesis-a45f21a5bfecdf87", "priority": 0.127409960208, "reconstruction_loss": 0.127409960208, "sample_id": "us-code-10-5512-4b2abf3c72275212"}`
