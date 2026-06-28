# packet-000006

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000006/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000006/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000006-20260518_072441

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-76a7638a600ec2f0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76a7638a600ec2f0` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.097396205148, "hint_id": "modal-synthesis-311353d315ab9df3", "priority": 0.332670299865, "reconstruction_loss": 0.332670299865, "sample_id": "us-code-28-715-17e4d69b8bcf8ca0"}`
  evidence: `{"cosine_similarity": -0.684880480901, "hint_id": "modal-synthesis-ba196dea113b3d0a", "priority": 0.927671002099, "reconstruction_loss": 0.927671002099, "sample_id": "us-code-41-1908-0e08f1fa2d71abfc"}`
  evidence: `{"cosine_similarity": 0.104110242639, "hint_id": "modal-synthesis-c22ad4e407a040db", "priority": 0.481679767704, "reconstruction_loss": 0.481679767704, "sample_id": "us-code-16-4262-d3b48644065ce57a"}`
  evidence: `{"cosine_similarity": 0.079422284999, "hint_id": "modal-synthesis-dead22048e04382e", "priority": 0.274639597408, "reconstruction_loss": 0.274639597408, "sample_id": "us-code-32-314-6744cb7ec9549d48"}`
- `program-69987e5751c892c9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76a7638a600ec2f0` score `0.985498`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.088547414088, "hint_id": "modal-synthesis-0ce898b057648888", "priority": 0.619429136569, "reconstruction_loss": 0.619429136569, "sample_id": "us-code-29-1863-caa9fbb898b49ba9"}`
  evidence: `{"cosine_similarity": -0.008525584377, "hint_id": "modal-synthesis-9e9890626c4aacc5", "priority": 0.311751356897, "reconstruction_loss": 0.311751356897, "sample_id": "us-code-15-649-2196edd5586b40df"}`
  evidence: `{"cosine_similarity": 0.235896432623, "hint_id": "modal-synthesis-ba88a5c58f4f6c96", "priority": 0.317243178444, "reconstruction_loss": 0.317243178444, "sample_id": "us-code-42-300mm.-80233d6bb1a7d5e4"}`
  evidence: `{"cosine_similarity": 0.108527630017, "hint_id": "modal-synthesis-e60197c7e7d572b8", "priority": 0.314326984364, "reconstruction_loss": 0.314326984364, "sample_id": "us-code-10-8588-eb039524912bce7b"}`

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
- TODO count: `2`

## TODOs
- `program-76a7638a600ec2f0`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76a7638a600ec2f0` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.504165166769`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-41-1908-0e08f1fa2d71abfc, us-code-16-4262-d3b48644065ce57a, us-code-28-715-17e4d69b8bcf8ca0, us-code-32-314-6744cb7ec9549d48`
  evidence: `{"cosine_similarity": 0.097396205148, "hint_id": "modal-synthesis-311353d315ab9df3", "priority": 0.332670299865, "reconstruction_loss": 0.332670299865, "sample_id": "us-code-28-715-17e4d69b8bcf8ca0"}`
  evidence: `{"cosine_similarity": -0.684880480901, "hint_id": "modal-synthesis-ba196dea113b3d0a", "priority": 0.927671002099, "reconstruction_loss": 0.927671002099, "sample_id": "us-code-41-1908-0e08f1fa2d71abfc"}`
  evidence: `{"cosine_similarity": 0.104110242639, "hint_id": "modal-synthesis-c22ad4e407a040db", "priority": 0.481679767704, "reconstruction_loss": 0.481679767704, "sample_id": "us-code-16-4262-d3b48644065ce57a"}`
  evidence: `{"cosine_similarity": 0.079422284999, "hint_id": "modal-synthesis-dead22048e04382e", "priority": 0.274639597408, "reconstruction_loss": 0.274639597408, "sample_id": "us-code-32-314-6744cb7ec9549d48"}`
- `program-69987e5751c892c9`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-76a7638a600ec2f0` score `0.985498`
  loss: `autoencoder_residual_cluster` = `0.390687664068`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-29-1863-caa9fbb898b49ba9, us-code-42-300mm.-80233d6bb1a7d5e4, us-code-10-8588-eb039524912bce7b, us-code-15-649-2196edd5586b40df`
  evidence: `{"cosine_similarity": -0.088547414088, "hint_id": "modal-synthesis-0ce898b057648888", "priority": 0.619429136569, "reconstruction_loss": 0.619429136569, "sample_id": "us-code-29-1863-caa9fbb898b49ba9"}`
  evidence: `{"cosine_similarity": -0.008525584377, "hint_id": "modal-synthesis-9e9890626c4aacc5", "priority": 0.311751356897, "reconstruction_loss": 0.311751356897, "sample_id": "us-code-15-649-2196edd5586b40df"}`
  evidence: `{"cosine_similarity": 0.235896432623, "hint_id": "modal-synthesis-ba88a5c58f4f6c96", "priority": 0.317243178444, "reconstruction_loss": 0.317243178444, "sample_id": "us-code-42-300mm.-80233d6bb1a7d5e4"}`
  evidence: `{"cosine_similarity": 0.108527630017, "hint_id": "modal-synthesis-e60197c7e7d572b8", "priority": 0.314326984364, "reconstruction_loss": 0.314326984364, "sample_id": "us-code-10-8588-eb039524912bce7b"}`
