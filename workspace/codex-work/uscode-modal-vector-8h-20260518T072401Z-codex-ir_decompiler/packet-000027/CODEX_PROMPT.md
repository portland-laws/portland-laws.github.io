# packet-000027

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000027/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000027/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000027-20260518_095515

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-5bdae7a60f9d2b96` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5bdae7a60f9d2b96` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.507634907963, "hint_id": "modal-synthesis-0d9bd565c37c7b0d", "priority": 0.811240465462, "reconstruction_loss": 0.811240465462, "sample_id": "us-code-7-7656-ba2dced7f1b0e6ea"}`
  evidence: `{"cosine_similarity": -0.215085161584, "hint_id": "modal-synthesis-3180bc4e6dbbffcc", "priority": 0.553565291655, "reconstruction_loss": 0.553565291655, "sample_id": "us-code-8-71-ba23a2579e9f7282"}`
  evidence: `{"cosine_similarity": 0.210641059967, "hint_id": "modal-synthesis-a561dcfa538099ed", "priority": 0.544003350188, "reconstruction_loss": 0.544003350188, "sample_id": "us-code-4-123-d46eff3eecad7d48"}`
  evidence: `{"cosine_similarity": 0.118061115489, "hint_id": "modal-synthesis-f317ebd1dd610230", "priority": 0.398374588049, "reconstruction_loss": 0.398374588049, "sample_id": "us-code-12-326-cdc87a23656b98e3"}`
- `program-d9995c26ab961f14` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5bdae7a60f9d2b96` score `0.994429`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.00670287987, "hint_id": "modal-synthesis-56fe8d067ed24bd0", "priority": 0.531616624168, "reconstruction_loss": 0.531616624168, "sample_id": "us-code-20-1161g-1138cf6719917569"}`
  evidence: `{"cosine_similarity": 0.2108468917, "hint_id": "modal-synthesis-662322d5ca206ebc", "priority": 0.464547129917, "reconstruction_loss": 0.464547129917, "sample_id": "us-code-7-1343-c22132889e741876"}`
  evidence: `{"cosine_similarity": -0.698271602219, "hint_id": "modal-synthesis-be3ede673d42a973", "priority": 0.724591869556, "reconstruction_loss": 0.724591869556, "sample_id": "us-code-35-387-3d8538a1b163795f"}`
  evidence: `{"cosine_similarity": 0.324338417448, "hint_id": "modal-synthesis-d3ffdf7f24195595", "priority": 0.272722512221, "reconstruction_loss": 0.272722512221, "sample_id": "us-code-25-967-707b30343b0c16a9"}`
- `program-4acd4c205b9d8e1f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5bdae7a60f9d2b96` score `0.993946`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.787869760834, "hint_id": "modal-synthesis-38caed3acf42ea60", "priority": 0.681441718616, "reconstruction_loss": 0.681441718616, "sample_id": "us-code-10-2546-873c497168523deb"}`
  evidence: `{"cosine_similarity": 0.346076957344, "hint_id": "modal-synthesis-610072fd504a93e1", "priority": 0.380652075722, "reconstruction_loss": 0.380652075722, "sample_id": "us-code-36-153104-8699a435855fe672"}`
  evidence: `{"cosine_similarity": -0.247352495974, "hint_id": "modal-synthesis-769610b333358b3e", "priority": 0.560695907203, "reconstruction_loss": 0.560695907203, "sample_id": "us-code-15-272b-c6006312ede01b88"}`
  evidence: `{"cosine_similarity": -0.357229097891, "hint_id": "modal-synthesis-ec452879147c6e17", "priority": 0.634589551317, "reconstruction_loss": 0.634589551317, "sample_id": "us-code-14-2160-0cce9d4a2895dfca"}`

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
- `program-5bdae7a60f9d2b96`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5bdae7a60f9d2b96` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.576795923838`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-7656-ba2dced7f1b0e6ea, us-code-8-71-ba23a2579e9f7282, us-code-4-123-d46eff3eecad7d48, us-code-12-326-cdc87a23656b98e3`
  evidence: `{"cosine_similarity": -0.507634907963, "hint_id": "modal-synthesis-0d9bd565c37c7b0d", "priority": 0.811240465462, "reconstruction_loss": 0.811240465462, "sample_id": "us-code-7-7656-ba2dced7f1b0e6ea"}`
  evidence: `{"cosine_similarity": -0.215085161584, "hint_id": "modal-synthesis-3180bc4e6dbbffcc", "priority": 0.553565291655, "reconstruction_loss": 0.553565291655, "sample_id": "us-code-8-71-ba23a2579e9f7282"}`
  evidence: `{"cosine_similarity": 0.210641059967, "hint_id": "modal-synthesis-a561dcfa538099ed", "priority": 0.544003350188, "reconstruction_loss": 0.544003350188, "sample_id": "us-code-4-123-d46eff3eecad7d48"}`
  evidence: `{"cosine_similarity": 0.118061115489, "hint_id": "modal-synthesis-f317ebd1dd610230", "priority": 0.398374588049, "reconstruction_loss": 0.398374588049, "sample_id": "us-code-12-326-cdc87a23656b98e3"}`
- `program-d9995c26ab961f14`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5bdae7a60f9d2b96` score `0.994429`
  loss: `autoencoder_residual_cluster` = `0.498369533965`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-35-387-3d8538a1b163795f, us-code-20-1161g-1138cf6719917569, us-code-7-1343-c22132889e741876, us-code-25-967-707b30343b0c16a9`
  evidence: `{"cosine_similarity": -0.00670287987, "hint_id": "modal-synthesis-56fe8d067ed24bd0", "priority": 0.531616624168, "reconstruction_loss": 0.531616624168, "sample_id": "us-code-20-1161g-1138cf6719917569"}`
  evidence: `{"cosine_similarity": 0.2108468917, "hint_id": "modal-synthesis-662322d5ca206ebc", "priority": 0.464547129917, "reconstruction_loss": 0.464547129917, "sample_id": "us-code-7-1343-c22132889e741876"}`
  evidence: `{"cosine_similarity": -0.698271602219, "hint_id": "modal-synthesis-be3ede673d42a973", "priority": 0.724591869556, "reconstruction_loss": 0.724591869556, "sample_id": "us-code-35-387-3d8538a1b163795f"}`
  evidence: `{"cosine_similarity": 0.324338417448, "hint_id": "modal-synthesis-d3ffdf7f24195595", "priority": 0.272722512221, "reconstruction_loss": 0.272722512221, "sample_id": "us-code-25-967-707b30343b0c16a9"}`
- `program-4acd4c205b9d8e1f`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5bdae7a60f9d2b96` score `0.993946`
  loss: `autoencoder_residual_cluster` = `0.564344813215`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-10-2546-873c497168523deb, us-code-14-2160-0cce9d4a2895dfca, us-code-15-272b-c6006312ede01b88, us-code-36-153104-8699a435855fe672`
  evidence: `{"cosine_similarity": -0.787869760834, "hint_id": "modal-synthesis-38caed3acf42ea60", "priority": 0.681441718616, "reconstruction_loss": 0.681441718616, "sample_id": "us-code-10-2546-873c497168523deb"}`
  evidence: `{"cosine_similarity": 0.346076957344, "hint_id": "modal-synthesis-610072fd504a93e1", "priority": 0.380652075722, "reconstruction_loss": 0.380652075722, "sample_id": "us-code-36-153104-8699a435855fe672"}`
  evidence: `{"cosine_similarity": -0.247352495974, "hint_id": "modal-synthesis-769610b333358b3e", "priority": 0.560695907203, "reconstruction_loss": 0.560695907203, "sample_id": "us-code-15-272b-c6006312ede01b88"}`
  evidence: `{"cosine_similarity": -0.357229097891, "hint_id": "modal-synthesis-ec452879147c6e17", "priority": 0.634589551317, "reconstruction_loss": 0.634589551317, "sample_id": "us-code-14-2160-0cce9d4a2895dfca"}`
