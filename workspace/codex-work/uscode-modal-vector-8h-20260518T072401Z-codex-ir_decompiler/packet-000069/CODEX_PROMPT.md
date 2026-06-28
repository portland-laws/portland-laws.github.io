# packet-000069

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000069/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000069/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000069-20260518_140942

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-6b8ec95430b09bb3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-6b8ec95430b09bb3` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.291472474256, "hint_id": "modal-synthesis-7d9106b64dfd0f00", "priority": 0.628234444837, "reconstruction_loss": 0.628234444837, "sample_id": "us-code-12-213-081d3cef966243ca"}`
  evidence: `{"cosine_similarity": 0.322911305764, "hint_id": "modal-synthesis-a402efc39e56f94e", "priority": 0.456208844573, "reconstruction_loss": 0.456208844573, "sample_id": "us-code-10-10105-00b52237542cec4d"}`
  evidence: `{"cosine_similarity": 0.413819428881, "hint_id": "modal-synthesis-d3fab2a072a99d60", "priority": 0.33616526163, "reconstruction_loss": 0.33616526163, "sample_id": "us-code-12-481-171d4218676b2212"}`
  evidence: `{"cosine_similarity": -0.326409582917, "hint_id": "modal-synthesis-ef505e0d8df55399", "priority": 0.509892692552, "reconstruction_loss": 0.509892692552, "sample_id": "us-code-7-8205-6f5032626018a8d4"}`
- `program-0e18b89ccb28aad9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-6b8ec95430b09bb3` score `0.993997`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.361252961173, "hint_id": "modal-synthesis-7dba140e8b9d3357", "priority": 0.363643548568, "reconstruction_loss": 0.363643548568, "sample_id": "us-code-25-306-1944ff0eba733e77"}`
  evidence: `{"cosine_similarity": 0.249446812579, "hint_id": "modal-synthesis-bd0990c190713b83", "priority": 0.44898853344, "reconstruction_loss": 0.44898853344, "sample_id": "us-code-44-1502.-23b3f63cbeedb21a"}`
  evidence: `{"cosine_similarity": 0.035504849646, "hint_id": "modal-synthesis-e236fa3cf3cba8c0", "priority": 0.354119867722, "reconstruction_loss": 0.354119867722, "sample_id": "us-code-34-10449-0defc8f00cf4acb9"}`
  evidence: `{"cosine_similarity": 0.233848980778, "hint_id": "modal-synthesis-ff9739265c46fbb4", "priority": 0.408964221075, "reconstruction_loss": 0.408964221075, "sample_id": "us-code-12-2274-acf8675579937124"}`
- `program-42a2cc1857d4d3a2` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-6b8ec95430b09bb3` score `0.993489`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.33548732658, "hint_id": "modal-synthesis-0ae4347827d01106", "priority": 0.23689535816, "reconstruction_loss": 0.23689535816, "sample_id": "us-code-40-6305-5b0e33304fcd53d0"}`
  evidence: `{"cosine_similarity": 0.447297972625, "hint_id": "modal-synthesis-32647b7c090c3441", "priority": 0.336649388413, "reconstruction_loss": 0.336649388413, "sample_id": "us-code-2-4902-4d34314a6576830a"}`
  evidence: `{"cosine_similarity": -0.344508145962, "hint_id": "modal-synthesis-bb26cee159b9994e", "priority": 0.526843652555, "reconstruction_loss": 0.526843652555, "sample_id": "us-code-16-3502-d7f71abda6773ac6"}`
  evidence: `{"cosine_similarity": -0.308520141347, "hint_id": "modal-synthesis-e2d7c740977efd00", "priority": 0.577507032732, "reconstruction_loss": 0.577507032732, "sample_id": "us-code-12-1735a-906e91e94a432045"}`

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
- `program-6b8ec95430b09bb3`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-6b8ec95430b09bb3` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.482625310898`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-12-213-081d3cef966243ca, us-code-7-8205-6f5032626018a8d4, us-code-10-10105-00b52237542cec4d, us-code-12-481-171d4218676b2212`
  evidence: `{"cosine_similarity": -0.291472474256, "hint_id": "modal-synthesis-7d9106b64dfd0f00", "priority": 0.628234444837, "reconstruction_loss": 0.628234444837, "sample_id": "us-code-12-213-081d3cef966243ca"}`
  evidence: `{"cosine_similarity": 0.322911305764, "hint_id": "modal-synthesis-a402efc39e56f94e", "priority": 0.456208844573, "reconstruction_loss": 0.456208844573, "sample_id": "us-code-10-10105-00b52237542cec4d"}`
  evidence: `{"cosine_similarity": 0.413819428881, "hint_id": "modal-synthesis-d3fab2a072a99d60", "priority": 0.33616526163, "reconstruction_loss": 0.33616526163, "sample_id": "us-code-12-481-171d4218676b2212"}`
  evidence: `{"cosine_similarity": -0.326409582917, "hint_id": "modal-synthesis-ef505e0d8df55399", "priority": 0.509892692552, "reconstruction_loss": 0.509892692552, "sample_id": "us-code-7-8205-6f5032626018a8d4"}`
- `program-0e18b89ccb28aad9`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-6b8ec95430b09bb3` score `0.993997`
  loss: `autoencoder_residual_cluster` = `0.393929042701`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-44-1502.-23b3f63cbeedb21a, us-code-12-2274-acf8675579937124, us-code-25-306-1944ff0eba733e77, us-code-34-10449-0defc8f00cf4acb9`
  evidence: `{"cosine_similarity": 0.361252961173, "hint_id": "modal-synthesis-7dba140e8b9d3357", "priority": 0.363643548568, "reconstruction_loss": 0.363643548568, "sample_id": "us-code-25-306-1944ff0eba733e77"}`
  evidence: `{"cosine_similarity": 0.249446812579, "hint_id": "modal-synthesis-bd0990c190713b83", "priority": 0.44898853344, "reconstruction_loss": 0.44898853344, "sample_id": "us-code-44-1502.-23b3f63cbeedb21a"}`
  evidence: `{"cosine_similarity": 0.035504849646, "hint_id": "modal-synthesis-e236fa3cf3cba8c0", "priority": 0.354119867722, "reconstruction_loss": 0.354119867722, "sample_id": "us-code-34-10449-0defc8f00cf4acb9"}`
  evidence: `{"cosine_similarity": 0.233848980778, "hint_id": "modal-synthesis-ff9739265c46fbb4", "priority": 0.408964221075, "reconstruction_loss": 0.408964221075, "sample_id": "us-code-12-2274-acf8675579937124"}`
- `program-42a2cc1857d4d3a2`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-6b8ec95430b09bb3` score `0.993489`
  loss: `autoencoder_residual_cluster` = `0.419473857965`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-12-1735a-906e91e94a432045, us-code-16-3502-d7f71abda6773ac6, us-code-2-4902-4d34314a6576830a, us-code-40-6305-5b0e33304fcd53d0`
  evidence: `{"cosine_similarity": 0.33548732658, "hint_id": "modal-synthesis-0ae4347827d01106", "priority": 0.23689535816, "reconstruction_loss": 0.23689535816, "sample_id": "us-code-40-6305-5b0e33304fcd53d0"}`
  evidence: `{"cosine_similarity": 0.447297972625, "hint_id": "modal-synthesis-32647b7c090c3441", "priority": 0.336649388413, "reconstruction_loss": 0.336649388413, "sample_id": "us-code-2-4902-4d34314a6576830a"}`
  evidence: `{"cosine_similarity": -0.344508145962, "hint_id": "modal-synthesis-bb26cee159b9994e", "priority": 0.526843652555, "reconstruction_loss": 0.526843652555, "sample_id": "us-code-16-3502-d7f71abda6773ac6"}`
  evidence: `{"cosine_similarity": -0.308520141347, "hint_id": "modal-synthesis-e2d7c740977efd00", "priority": 0.577507032732, "reconstruction_loss": 0.577507032732, "sample_id": "us-code-12-1735a-906e91e94a432045"}`
