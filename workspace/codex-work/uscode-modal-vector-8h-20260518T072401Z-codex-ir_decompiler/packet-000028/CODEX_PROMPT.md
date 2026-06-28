# packet-000028

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000028/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000028/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000028-20260518_100545

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-beb36fa91fac5b08` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-beb36fa91fac5b08` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.092993429547, "hint_id": "modal-synthesis-08264af15150e5e1", "priority": 0.722192477168, "reconstruction_loss": 0.722192477168, "sample_id": "us-code-7-8001-888b549ffe7be041"}`
  evidence: `{"cosine_similarity": -0.170583990324, "hint_id": "modal-synthesis-534badd5563e640e", "priority": 0.453976474134, "reconstruction_loss": 0.453976474134, "sample_id": "us-code-12-375b-0abdc31778e5a7b0"}`
  evidence: `{"cosine_similarity": -0.318079354273, "hint_id": "modal-synthesis-99d952eb343ab153", "priority": 0.806399136334, "reconstruction_loss": 0.806399136334, "sample_id": "us-code-2-190l-01dd1648c5b1588c"}`
  evidence: `{"cosine_similarity": 0.340635837007, "hint_id": "modal-synthesis-fe20c836c79fe037", "priority": 0.32193545497, "reconstruction_loss": 0.32193545497, "sample_id": "us-code-16-284c-92b024a7d53f3c4c"}`
- `program-8cd4655c6195ac52` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-beb36fa91fac5b08` score `0.994816`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.198814965708, "hint_id": "modal-synthesis-255695f382fc6002", "priority": 0.37211834481, "reconstruction_loss": 0.37211834481, "sample_id": "us-code-26-5418-5688898c7ffe5041"}`
  evidence: `{"cosine_similarity": -0.110590952029, "hint_id": "modal-synthesis-500532cf6bf6a9ff", "priority": 0.556066993199, "reconstruction_loss": 0.556066993199, "sample_id": "us-code-2-60e-3-49bb3eb4baff92b8"}`
  evidence: `{"cosine_similarity": -0.03156391995, "hint_id": "modal-synthesis-892f21f6f36a39f7", "priority": 0.40337185715, "reconstruction_loss": 0.40337185715, "sample_id": "us-code-2-127-eb6cb4046d2a98a5"}`
  evidence: `{"cosine_similarity": -0.548535224951, "hint_id": "modal-synthesis-d77b41c1a42e343e", "priority": 0.511419425734, "reconstruction_loss": 0.511419425734, "sample_id": "us-code-6-103a-4735651082e4b538"}`
- `program-616bb2d98cfd3657` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-beb36fa91fac5b08` score `0.994784`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.33748881744, "hint_id": "modal-synthesis-30f49597a7c372f1", "priority": 0.394285854336, "reconstruction_loss": 0.394285854336, "sample_id": "us-code-16-460bbb-5-f9ee2abbb63c7093"}`
  evidence: `{"cosine_similarity": 0.056575700579, "hint_id": "modal-synthesis-3ee6336cd1af7a4c", "priority": 0.251153215744, "reconstruction_loss": 0.251153215744, "sample_id": "us-code-12-4229-ffe0ece425152d37"}`
  evidence: `{"cosine_similarity": -0.801520852395, "hint_id": "modal-synthesis-6aa1ec02876847e8", "priority": 1.029570387034, "reconstruction_loss": 1.029570387034, "sample_id": "us-code-16-4243-46cb78f9658a7f0d"}`
  evidence: `{"cosine_similarity": 0.33563733113, "hint_id": "modal-synthesis-e48c608edc56a764", "priority": 0.312539480619, "reconstruction_loss": 0.312539480619, "sample_id": "us-code-25-1680c-f95acbe3205ef557"}`

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
- `program-beb36fa91fac5b08`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-beb36fa91fac5b08` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.576125885651`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-2-190l-01dd1648c5b1588c, us-code-7-8001-888b549ffe7be041, us-code-12-375b-0abdc31778e5a7b0, us-code-16-284c-92b024a7d53f3c4c`
  evidence: `{"cosine_similarity": -0.092993429547, "hint_id": "modal-synthesis-08264af15150e5e1", "priority": 0.722192477168, "reconstruction_loss": 0.722192477168, "sample_id": "us-code-7-8001-888b549ffe7be041"}`
  evidence: `{"cosine_similarity": -0.170583990324, "hint_id": "modal-synthesis-534badd5563e640e", "priority": 0.453976474134, "reconstruction_loss": 0.453976474134, "sample_id": "us-code-12-375b-0abdc31778e5a7b0"}`
  evidence: `{"cosine_similarity": -0.318079354273, "hint_id": "modal-synthesis-99d952eb343ab153", "priority": 0.806399136334, "reconstruction_loss": 0.806399136334, "sample_id": "us-code-2-190l-01dd1648c5b1588c"}`
  evidence: `{"cosine_similarity": 0.340635837007, "hint_id": "modal-synthesis-fe20c836c79fe037", "priority": 0.32193545497, "reconstruction_loss": 0.32193545497, "sample_id": "us-code-16-284c-92b024a7d53f3c4c"}`
- `program-8cd4655c6195ac52`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-beb36fa91fac5b08` score `0.994816`
  loss: `autoencoder_residual_cluster` = `0.460744155223`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-2-60e-3-49bb3eb4baff92b8, us-code-6-103a-4735651082e4b538, us-code-2-127-eb6cb4046d2a98a5, us-code-26-5418-5688898c7ffe5041`
  evidence: `{"cosine_similarity": 0.198814965708, "hint_id": "modal-synthesis-255695f382fc6002", "priority": 0.37211834481, "reconstruction_loss": 0.37211834481, "sample_id": "us-code-26-5418-5688898c7ffe5041"}`
  evidence: `{"cosine_similarity": -0.110590952029, "hint_id": "modal-synthesis-500532cf6bf6a9ff", "priority": 0.556066993199, "reconstruction_loss": 0.556066993199, "sample_id": "us-code-2-60e-3-49bb3eb4baff92b8"}`
  evidence: `{"cosine_similarity": -0.03156391995, "hint_id": "modal-synthesis-892f21f6f36a39f7", "priority": 0.40337185715, "reconstruction_loss": 0.40337185715, "sample_id": "us-code-2-127-eb6cb4046d2a98a5"}`
  evidence: `{"cosine_similarity": -0.548535224951, "hint_id": "modal-synthesis-d77b41c1a42e343e", "priority": 0.511419425734, "reconstruction_loss": 0.511419425734, "sample_id": "us-code-6-103a-4735651082e4b538"}`
- `program-616bb2d98cfd3657`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-beb36fa91fac5b08` score `0.994784`
  loss: `autoencoder_residual_cluster` = `0.496887234433`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-16-4243-46cb78f9658a7f0d, us-code-16-460bbb-5-f9ee2abbb63c7093, us-code-25-1680c-f95acbe3205ef557, us-code-12-4229-ffe0ece425152d37`
  evidence: `{"cosine_similarity": -0.33748881744, "hint_id": "modal-synthesis-30f49597a7c372f1", "priority": 0.394285854336, "reconstruction_loss": 0.394285854336, "sample_id": "us-code-16-460bbb-5-f9ee2abbb63c7093"}`
  evidence: `{"cosine_similarity": 0.056575700579, "hint_id": "modal-synthesis-3ee6336cd1af7a4c", "priority": 0.251153215744, "reconstruction_loss": 0.251153215744, "sample_id": "us-code-12-4229-ffe0ece425152d37"}`
  evidence: `{"cosine_similarity": -0.801520852395, "hint_id": "modal-synthesis-6aa1ec02876847e8", "priority": 1.029570387034, "reconstruction_loss": 1.029570387034, "sample_id": "us-code-16-4243-46cb78f9658a7f0d"}`
  evidence: `{"cosine_similarity": 0.33563733113, "hint_id": "modal-synthesis-e48c608edc56a764", "priority": 0.312539480619, "reconstruction_loss": 0.312539480619, "sample_id": "us-code-25-1680c-f95acbe3205ef557"}`
