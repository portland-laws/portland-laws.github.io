# packet-000008

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000008/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000008/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000008-20260518_074213

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b77dcca10df6fa1a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b77dcca10df6fa1a` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.224117601701, "hint_id": "modal-synthesis-224d47005cb073a8", "priority": 0.613339194781, "reconstruction_loss": 0.613339194781, "sample_id": "us-code-19-1314-bd33afe54812874e"}`
  evidence: `{"cosine_similarity": -0.245148737806, "hint_id": "modal-synthesis-50ff07de56101f1f", "priority": 0.68991249785, "reconstruction_loss": 0.68991249785, "sample_id": "us-code-1-8-2ceb596400901ed0"}`
  evidence: `{"cosine_similarity": -0.231175511211, "hint_id": "modal-synthesis-879a2aca21ccdb51", "priority": 0.566626393353, "reconstruction_loss": 0.566626393353, "sample_id": "us-code-20-1704-6ecd3a95620cd45e"}`
  evidence: `{"cosine_similarity": -0.104902127395, "hint_id": "modal-synthesis-b6ac6ef46df8d576", "priority": 0.594264865749, "reconstruction_loss": 0.594264865749, "sample_id": "us-code-16-3125-f6a333e379f8ec22"}`
- `program-827ba2718b4658ae` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b77dcca10df6fa1a` score `0.995465`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.250257345178, "hint_id": "modal-synthesis-62f5ffc4753d6116", "priority": 0.439500787146, "reconstruction_loss": 0.439500787146, "sample_id": "us-code-28-3007-ebdcf624ebdbde57"}`
  evidence: `{"cosine_similarity": -0.824190084612, "hint_id": "modal-synthesis-a00b65461b956d1b", "priority": 0.68156284602, "reconstruction_loss": 0.68156284602, "sample_id": "us-code-20-511-104cc47b35d7a0b9"}`
  evidence: `{"cosine_similarity": 0.508427160071, "hint_id": "modal-synthesis-b80179de663fc4cd", "priority": 0.175229307282, "reconstruction_loss": 0.175229307282, "sample_id": "us-code-42-17082.-0ccf7de21d15ced3"}`
  evidence: `{"cosine_similarity": -0.35897444905, "hint_id": "modal-synthesis-f970b4efc4f66e18", "priority": 0.640025554882, "reconstruction_loss": 0.640025554882, "sample_id": "us-code-22-7210-22dd426d03f9669a"}`
- `program-f3134cccd5f266f5` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b77dcca10df6fa1a` score `0.994677`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.171714101294, "hint_id": "modal-synthesis-1e518d857f8d191c", "priority": 0.3822666995, "reconstruction_loss": 0.3822666995, "sample_id": "us-code-10-2114a-7731b65136262c9f"}`
  evidence: `{"cosine_similarity": -0.533072479689, "hint_id": "modal-synthesis-450f1b7d41f64f5d", "priority": 0.626769366746, "reconstruction_loss": 0.626769366746, "sample_id": "us-code-15-3722a-09a8f44d37ee50f3"}`
  evidence: `{"cosine_similarity": 0.426244025556, "hint_id": "modal-synthesis-477cbbb846fad3c1", "priority": 0.291918562255, "reconstruction_loss": 0.291918562255, "sample_id": "us-code-7-2021-099996bd698b517d"}`
  evidence: `{"cosine_similarity": 0.52962502838, "hint_id": "modal-synthesis-87f26a71b48ed8dd", "priority": 0.266920492, "reconstruction_loss": 0.266920492, "sample_id": "us-code-38-1162-29b14a76022dab46"}`

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
- `program-b77dcca10df6fa1a`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b77dcca10df6fa1a` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.616035737933`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-1-8-2ceb596400901ed0, us-code-19-1314-bd33afe54812874e, us-code-16-3125-f6a333e379f8ec22, us-code-20-1704-6ecd3a95620cd45e`
  evidence: `{"cosine_similarity": -0.224117601701, "hint_id": "modal-synthesis-224d47005cb073a8", "priority": 0.613339194781, "reconstruction_loss": 0.613339194781, "sample_id": "us-code-19-1314-bd33afe54812874e"}`
  evidence: `{"cosine_similarity": -0.245148737806, "hint_id": "modal-synthesis-50ff07de56101f1f", "priority": 0.68991249785, "reconstruction_loss": 0.68991249785, "sample_id": "us-code-1-8-2ceb596400901ed0"}`
  evidence: `{"cosine_similarity": -0.231175511211, "hint_id": "modal-synthesis-879a2aca21ccdb51", "priority": 0.566626393353, "reconstruction_loss": 0.566626393353, "sample_id": "us-code-20-1704-6ecd3a95620cd45e"}`
  evidence: `{"cosine_similarity": -0.104902127395, "hint_id": "modal-synthesis-b6ac6ef46df8d576", "priority": 0.594264865749, "reconstruction_loss": 0.594264865749, "sample_id": "us-code-16-3125-f6a333e379f8ec22"}`
- `program-827ba2718b4658ae`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b77dcca10df6fa1a` score `0.995465`
  loss: `autoencoder_residual_cluster` = `0.484079623832`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-20-511-104cc47b35d7a0b9, us-code-22-7210-22dd426d03f9669a, us-code-28-3007-ebdcf624ebdbde57, us-code-42-17082.-0ccf7de21d15ced3`
  evidence: `{"cosine_similarity": -0.250257345178, "hint_id": "modal-synthesis-62f5ffc4753d6116", "priority": 0.439500787146, "reconstruction_loss": 0.439500787146, "sample_id": "us-code-28-3007-ebdcf624ebdbde57"}`
  evidence: `{"cosine_similarity": -0.824190084612, "hint_id": "modal-synthesis-a00b65461b956d1b", "priority": 0.68156284602, "reconstruction_loss": 0.68156284602, "sample_id": "us-code-20-511-104cc47b35d7a0b9"}`
  evidence: `{"cosine_similarity": 0.508427160071, "hint_id": "modal-synthesis-b80179de663fc4cd", "priority": 0.175229307282, "reconstruction_loss": 0.175229307282, "sample_id": "us-code-42-17082.-0ccf7de21d15ced3"}`
  evidence: `{"cosine_similarity": -0.35897444905, "hint_id": "modal-synthesis-f970b4efc4f66e18", "priority": 0.640025554882, "reconstruction_loss": 0.640025554882, "sample_id": "us-code-22-7210-22dd426d03f9669a"}`
- `program-f3134cccd5f266f5`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b77dcca10df6fa1a` score `0.994677`
  loss: `autoencoder_residual_cluster` = `0.391968780125`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-15-3722a-09a8f44d37ee50f3, us-code-10-2114a-7731b65136262c9f, us-code-7-2021-099996bd698b517d, us-code-38-1162-29b14a76022dab46`
  evidence: `{"cosine_similarity": 0.171714101294, "hint_id": "modal-synthesis-1e518d857f8d191c", "priority": 0.3822666995, "reconstruction_loss": 0.3822666995, "sample_id": "us-code-10-2114a-7731b65136262c9f"}`
  evidence: `{"cosine_similarity": -0.533072479689, "hint_id": "modal-synthesis-450f1b7d41f64f5d", "priority": 0.626769366746, "reconstruction_loss": 0.626769366746, "sample_id": "us-code-15-3722a-09a8f44d37ee50f3"}`
  evidence: `{"cosine_similarity": 0.426244025556, "hint_id": "modal-synthesis-477cbbb846fad3c1", "priority": 0.291918562255, "reconstruction_loss": 0.291918562255, "sample_id": "us-code-7-2021-099996bd698b517d"}`
  evidence: `{"cosine_similarity": 0.52962502838, "hint_id": "modal-synthesis-87f26a71b48ed8dd", "priority": 0.266920492, "reconstruction_loss": 0.266920492, "sample_id": "us-code-38-1162-29b14a76022dab46"}`
