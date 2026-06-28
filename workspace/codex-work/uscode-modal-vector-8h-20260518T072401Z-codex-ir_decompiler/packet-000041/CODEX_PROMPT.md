# packet-000041

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000041/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000041/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000041-20260518_112445

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-56133592c7047777` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-56133592c7047777` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.250961641077, "hint_id": "modal-synthesis-0cebb4e68525011e", "priority": 0.429321524033, "reconstruction_loss": 0.429321524033, "sample_id": "us-code-5-6384-8b50e16be95927f5"}`
  evidence: `{"cosine_similarity": -0.353905427283, "hint_id": "modal-synthesis-2f6e53fc00f9bfd6", "priority": 0.878819708818, "reconstruction_loss": 0.878819708818, "sample_id": "us-code-26-6503-4c2f54aaf561a1a1"}`
  evidence: `{"cosine_similarity": -0.779367383197, "hint_id": "modal-synthesis-8f94a3058bb3b480", "priority": 0.38652989852, "reconstruction_loss": 0.38652989852, "sample_id": "us-code-5-5348-f0250f870668e53f"}`
  evidence: `{"cosine_similarity": 0.112554037381, "hint_id": "modal-synthesis-aff3c37259955e02", "priority": 0.451945455978, "reconstruction_loss": 0.451945455978, "sample_id": "us-code-25-450-c265a65e885d4655"}`
- `program-33cbe96f65f7b676` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-56133592c7047777` score `0.994778`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.045538459661, "hint_id": "modal-synthesis-0dfd91a257362e58", "priority": 0.551922854071, "reconstruction_loss": 0.551922854071, "sample_id": "us-code-25-713e-f5468e8e88aa95d6"}`
  evidence: `{"cosine_similarity": 0.861862613557, "hint_id": "modal-synthesis-4d9040301196ce05", "priority": 0.052268820818, "reconstruction_loss": 0.052268820818, "sample_id": "us-code-21-142-2c50b2ab20c5d7f5"}`
  evidence: `{"cosine_similarity": -0.365581778965, "hint_id": "modal-synthesis-6cc806bc6dd74265", "priority": 0.600829625918, "reconstruction_loss": 0.600829625918, "sample_id": "us-code-26-6719-ea0f82e69386f683"}`
  evidence: `{"cosine_similarity": 0.068279365609, "hint_id": "modal-synthesis-d6cc210dc8fc2ad5", "priority": 0.280861034507, "reconstruction_loss": 0.280861034507, "sample_id": "us-code-25-2306-65a3453df451879a"}`
- `program-796b75535ab2bf0e` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-56133592c7047777` score `0.993983`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.510151065508, "hint_id": "modal-synthesis-03afacc21d043eb5", "priority": 0.597834789628, "reconstruction_loss": 0.597834789628, "sample_id": "us-code-42-3335.-e5ddcbd4ee65a9c4"}`
  evidence: `{"cosine_similarity": 0.734430857363, "hint_id": "modal-synthesis-49e1dc48f1d6487d", "priority": 0.099275944379, "reconstruction_loss": 0.099275944379, "sample_id": "us-code-25-754-c1ead712ac1c961c"}`
  evidence: `{"cosine_similarity": -0.221057450454, "hint_id": "modal-synthesis-88b616cdfa16702c", "priority": 0.485333765948, "reconstruction_loss": 0.485333765948, "sample_id": "us-code-40-1305-279dd19310a0d986"}`
  evidence: `{"cosine_similarity": -0.479385748633, "hint_id": "modal-synthesis-fac30f4e65e7a1b7", "priority": 0.417023964725, "reconstruction_loss": 0.417023964725, "sample_id": "us-code-23-120-3fdb20d0f3bec252"}`

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
- `program-56133592c7047777`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-56133592c7047777` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.536654146837`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-6503-4c2f54aaf561a1a1, us-code-25-450-c265a65e885d4655, us-code-5-6384-8b50e16be95927f5, us-code-5-5348-f0250f870668e53f`
  evidence: `{"cosine_similarity": -0.250961641077, "hint_id": "modal-synthesis-0cebb4e68525011e", "priority": 0.429321524033, "reconstruction_loss": 0.429321524033, "sample_id": "us-code-5-6384-8b50e16be95927f5"}`
  evidence: `{"cosine_similarity": -0.353905427283, "hint_id": "modal-synthesis-2f6e53fc00f9bfd6", "priority": 0.878819708818, "reconstruction_loss": 0.878819708818, "sample_id": "us-code-26-6503-4c2f54aaf561a1a1"}`
  evidence: `{"cosine_similarity": -0.779367383197, "hint_id": "modal-synthesis-8f94a3058bb3b480", "priority": 0.38652989852, "reconstruction_loss": 0.38652989852, "sample_id": "us-code-5-5348-f0250f870668e53f"}`
  evidence: `{"cosine_similarity": 0.112554037381, "hint_id": "modal-synthesis-aff3c37259955e02", "priority": 0.451945455978, "reconstruction_loss": 0.451945455978, "sample_id": "us-code-25-450-c265a65e885d4655"}`
- `program-33cbe96f65f7b676`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-56133592c7047777` score `0.994778`
  loss: `autoencoder_residual_cluster` = `0.371470583829`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-6719-ea0f82e69386f683, us-code-25-713e-f5468e8e88aa95d6, us-code-25-2306-65a3453df451879a, us-code-21-142-2c50b2ab20c5d7f5`
  evidence: `{"cosine_similarity": 0.045538459661, "hint_id": "modal-synthesis-0dfd91a257362e58", "priority": 0.551922854071, "reconstruction_loss": 0.551922854071, "sample_id": "us-code-25-713e-f5468e8e88aa95d6"}`
  evidence: `{"cosine_similarity": 0.861862613557, "hint_id": "modal-synthesis-4d9040301196ce05", "priority": 0.052268820818, "reconstruction_loss": 0.052268820818, "sample_id": "us-code-21-142-2c50b2ab20c5d7f5"}`
  evidence: `{"cosine_similarity": -0.365581778965, "hint_id": "modal-synthesis-6cc806bc6dd74265", "priority": 0.600829625918, "reconstruction_loss": 0.600829625918, "sample_id": "us-code-26-6719-ea0f82e69386f683"}`
  evidence: `{"cosine_similarity": 0.068279365609, "hint_id": "modal-synthesis-d6cc210dc8fc2ad5", "priority": 0.280861034507, "reconstruction_loss": 0.280861034507, "sample_id": "us-code-25-2306-65a3453df451879a"}`
- `program-796b75535ab2bf0e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-56133592c7047777` score `0.993983`
  loss: `autoencoder_residual_cluster` = `0.39986711617`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-3335.-e5ddcbd4ee65a9c4, us-code-40-1305-279dd19310a0d986, us-code-23-120-3fdb20d0f3bec252, us-code-25-754-c1ead712ac1c961c`
  evidence: `{"cosine_similarity": -0.510151065508, "hint_id": "modal-synthesis-03afacc21d043eb5", "priority": 0.597834789628, "reconstruction_loss": 0.597834789628, "sample_id": "us-code-42-3335.-e5ddcbd4ee65a9c4"}`
  evidence: `{"cosine_similarity": 0.734430857363, "hint_id": "modal-synthesis-49e1dc48f1d6487d", "priority": 0.099275944379, "reconstruction_loss": 0.099275944379, "sample_id": "us-code-25-754-c1ead712ac1c961c"}`
  evidence: `{"cosine_similarity": -0.221057450454, "hint_id": "modal-synthesis-88b616cdfa16702c", "priority": 0.485333765948, "reconstruction_loss": 0.485333765948, "sample_id": "us-code-40-1305-279dd19310a0d986"}`
  evidence: `{"cosine_similarity": -0.479385748633, "hint_id": "modal-synthesis-fac30f4e65e7a1b7", "priority": 0.417023964725, "reconstruction_loss": 0.417023964725, "sample_id": "us-code-23-120-3fdb20d0f3bec252"}`
