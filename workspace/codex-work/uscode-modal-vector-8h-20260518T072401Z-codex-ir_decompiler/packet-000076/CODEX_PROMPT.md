# packet-000076

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000076/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000076/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000076-20260518_150835

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-a96abcf6e952318e` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a96abcf6e952318e` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.062112103201, "hint_id": "modal-synthesis-02fb6f962a6ed3b6", "priority": 0.459959902889, "reconstruction_loss": 0.459959902889, "sample_id": "us-code-15-9803-adbc3a3791b318b1"}`
  evidence: `{"cosine_similarity": -0.451998908924, "hint_id": "modal-synthesis-486af5d87383dc17", "priority": 0.610981674092, "reconstruction_loss": 0.610981674092, "sample_id": "us-code-19-1618-247239ad48941cec"}`
  evidence: `{"cosine_similarity": -0.314912140866, "hint_id": "modal-synthesis-bb478c35c7f927d3", "priority": 0.621524523716, "reconstruction_loss": 0.621524523716, "sample_id": "us-code-42-1962b-f1f3e0bbb4bb8130"}`
  evidence: `{"cosine_similarity": 0.27374416098, "hint_id": "modal-synthesis-cc36243f68c34a19", "priority": 0.33900705814, "reconstruction_loss": 0.33900705814, "sample_id": "us-code-49-6305.-48c2ddcbfba65b1e"}`
- `program-df16fff3f3b1ca43` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a96abcf6e952318e` score `0.9946`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.623514170483, "hint_id": "modal-synthesis-1e72e2316d121f76", "priority": 0.617817809074, "reconstruction_loss": 0.617817809074, "sample_id": "us-code-42-5106a-5c8fc2119faf1226"}`
  evidence: `{"cosine_similarity": 0.121594448676, "hint_id": "modal-synthesis-6a7edc3bbf6feb29", "priority": 0.38323619421, "reconstruction_loss": 0.38323619421, "sample_id": "us-code-22-1755-0ba575065f3913b3"}`
  evidence: `{"cosine_similarity": -0.074569823744, "hint_id": "modal-synthesis-c9365ac62895c771", "priority": 0.460128123576, "reconstruction_loss": 0.460128123576, "sample_id": "us-code-38-7102-02446fe38c5410ee"}`
  evidence: `{"cosine_similarity": 0.376880360981, "hint_id": "modal-synthesis-d7f8732dd68c6e9b", "priority": 0.311319823398, "reconstruction_loss": 0.311319823398, "sample_id": "us-code-48-1972.-95dcfe572f4e6d3b"}`
- `program-c5b608d5fde9a3e1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a96abcf6e952318e` score `0.994077`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.563458699928, "hint_id": "modal-synthesis-0bd794e5efa445d1", "priority": 0.644034927538, "reconstruction_loss": 0.644034927538, "sample_id": "us-code-29-631-ada12c62e2345a19"}`
  evidence: `{"cosine_similarity": 0.288730199535, "hint_id": "modal-synthesis-1335f34565a579ca", "priority": 0.537576524808, "reconstruction_loss": 0.537576524808, "sample_id": "us-code-15-1351-e4750baa15608d66"}`
  evidence: `{"cosine_similarity": -0.067022371268, "hint_id": "modal-synthesis-af3a9886f81824bb", "priority": 0.383109598886, "reconstruction_loss": 0.383109598886, "sample_id": "us-code-42-3106.-d4b878d6124ed4ea"}`
  evidence: `{"cosine_similarity": 0.442646483699, "hint_id": "modal-synthesis-f311ebf1dc5f2784", "priority": 0.267088288485, "reconstruction_loss": 0.267088288485, "sample_id": "us-code-26-4906-3894cbba24ff1d86"}`

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
- `program-a96abcf6e952318e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a96abcf6e952318e` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.507868289709`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-1962b-f1f3e0bbb4bb8130, us-code-19-1618-247239ad48941cec, us-code-15-9803-adbc3a3791b318b1, us-code-49-6305.-48c2ddcbfba65b1e`
  evidence: `{"cosine_similarity": 0.062112103201, "hint_id": "modal-synthesis-02fb6f962a6ed3b6", "priority": 0.459959902889, "reconstruction_loss": 0.459959902889, "sample_id": "us-code-15-9803-adbc3a3791b318b1"}`
  evidence: `{"cosine_similarity": -0.451998908924, "hint_id": "modal-synthesis-486af5d87383dc17", "priority": 0.610981674092, "reconstruction_loss": 0.610981674092, "sample_id": "us-code-19-1618-247239ad48941cec"}`
  evidence: `{"cosine_similarity": -0.314912140866, "hint_id": "modal-synthesis-bb478c35c7f927d3", "priority": 0.621524523716, "reconstruction_loss": 0.621524523716, "sample_id": "us-code-42-1962b-f1f3e0bbb4bb8130"}`
  evidence: `{"cosine_similarity": 0.27374416098, "hint_id": "modal-synthesis-cc36243f68c34a19", "priority": 0.33900705814, "reconstruction_loss": 0.33900705814, "sample_id": "us-code-49-6305.-48c2ddcbfba65b1e"}`
- `program-df16fff3f3b1ca43`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a96abcf6e952318e` score `0.9946`
  loss: `autoencoder_residual_cluster` = `0.443125487564`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-5106a-5c8fc2119faf1226, us-code-38-7102-02446fe38c5410ee, us-code-22-1755-0ba575065f3913b3, us-code-48-1972.-95dcfe572f4e6d3b`
  evidence: `{"cosine_similarity": -0.623514170483, "hint_id": "modal-synthesis-1e72e2316d121f76", "priority": 0.617817809074, "reconstruction_loss": 0.617817809074, "sample_id": "us-code-42-5106a-5c8fc2119faf1226"}`
  evidence: `{"cosine_similarity": 0.121594448676, "hint_id": "modal-synthesis-6a7edc3bbf6feb29", "priority": 0.38323619421, "reconstruction_loss": 0.38323619421, "sample_id": "us-code-22-1755-0ba575065f3913b3"}`
  evidence: `{"cosine_similarity": -0.074569823744, "hint_id": "modal-synthesis-c9365ac62895c771", "priority": 0.460128123576, "reconstruction_loss": 0.460128123576, "sample_id": "us-code-38-7102-02446fe38c5410ee"}`
  evidence: `{"cosine_similarity": 0.376880360981, "hint_id": "modal-synthesis-d7f8732dd68c6e9b", "priority": 0.311319823398, "reconstruction_loss": 0.311319823398, "sample_id": "us-code-48-1972.-95dcfe572f4e6d3b"}`
- `program-c5b608d5fde9a3e1`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-a96abcf6e952318e` score `0.994077`
  loss: `autoencoder_residual_cluster` = `0.457952334929`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-29-631-ada12c62e2345a19, us-code-15-1351-e4750baa15608d66, us-code-42-3106.-d4b878d6124ed4ea, us-code-26-4906-3894cbba24ff1d86`
  evidence: `{"cosine_similarity": -0.563458699928, "hint_id": "modal-synthesis-0bd794e5efa445d1", "priority": 0.644034927538, "reconstruction_loss": 0.644034927538, "sample_id": "us-code-29-631-ada12c62e2345a19"}`
  evidence: `{"cosine_similarity": 0.288730199535, "hint_id": "modal-synthesis-1335f34565a579ca", "priority": 0.537576524808, "reconstruction_loss": 0.537576524808, "sample_id": "us-code-15-1351-e4750baa15608d66"}`
  evidence: `{"cosine_similarity": -0.067022371268, "hint_id": "modal-synthesis-af3a9886f81824bb", "priority": 0.383109598886, "reconstruction_loss": 0.383109598886, "sample_id": "us-code-42-3106.-d4b878d6124ed4ea"}`
  evidence: `{"cosine_similarity": 0.442646483699, "hint_id": "modal-synthesis-f311ebf1dc5f2784", "priority": 0.267088288485, "reconstruction_loss": 0.267088288485, "sample_id": "us-code-26-4906-3894cbba24ff1d86"}`
