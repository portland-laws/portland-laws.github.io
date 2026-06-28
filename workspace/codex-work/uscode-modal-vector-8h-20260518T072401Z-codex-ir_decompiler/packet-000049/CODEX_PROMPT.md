# packet-000049

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000049/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000049/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000049-20260518_120429

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-08326e4a8ba01923` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-08326e4a8ba01923` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.022341642065, "hint_id": "modal-synthesis-6435f7b9afb1d816", "priority": 0.509775266069, "reconstruction_loss": 0.509775266069, "sample_id": "us-code-42-15208.-aec488d546c39fc6"}`
  evidence: `{"cosine_similarity": -0.123645320008, "hint_id": "modal-synthesis-6beb9b02d4ec10eb", "priority": 0.505320433928, "reconstruction_loss": 0.505320433928, "sample_id": "us-code-25-414-425141361dbb72f9"}`
  evidence: `{"cosine_similarity": -0.489768528804, "hint_id": "modal-synthesis-7f1481df3a7ba41d", "priority": 1.036934917036, "reconstruction_loss": 1.036934917036, "sample_id": "us-code-42-9922.-6a2850121a24ddc0"}`
  evidence: `{"cosine_similarity": 0.486925391109, "hint_id": "modal-synthesis-90f3227febfdcf99", "priority": 0.265369410555, "reconstruction_loss": 0.265369410555, "sample_id": "us-code-42-13384.-c1019817b4fc691f"}`
- `program-4e9035257303f27f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-08326e4a8ba01923` score `0.994789`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.517165647577, "hint_id": "modal-synthesis-492c5b4d7b2acae6", "priority": 0.291446790609, "reconstruction_loss": 0.291446790609, "sample_id": "us-code-42-16092.-a56ba67c3bcab0b8"}`
  evidence: `{"cosine_similarity": 0.485999458648, "hint_id": "modal-synthesis-5193e85a4b9d9acd", "priority": 0.204671694544, "reconstruction_loss": 0.204671694544, "sample_id": "us-code-33-741-6af99be469b97863"}`
  evidence: `{"cosine_similarity": -0.46509485212, "hint_id": "modal-synthesis-7c967c5c223f11f1", "priority": 0.487950161311, "reconstruction_loss": 0.487950161311, "sample_id": "us-code-43-1470.-845d9dceb9d264ab"}`
  evidence: `{"cosine_similarity": 0.146943617895, "hint_id": "modal-synthesis-99862bfb52616d38", "priority": 0.310702160803, "reconstruction_loss": 0.310702160803, "sample_id": "us-code-10-8669-847a57d070221b74"}`
- `program-42c21429f91982a6` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-08326e4a8ba01923` score `0.994532`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.309862376184, "hint_id": "modal-synthesis-1afcdb764e2e2b34", "priority": 0.392416653563, "reconstruction_loss": 0.392416653563, "sample_id": "us-code-7-1291-cfb67427fb37305d"}`
  evidence: `{"cosine_similarity": 0.048211956391, "hint_id": "modal-synthesis-4b9866bd5ac48d94", "priority": 0.38499322415, "reconstruction_loss": 0.38499322415, "sample_id": "us-code-22-4504-df643192e117d651"}`
  evidence: `{"cosine_similarity": -0.017907317672, "hint_id": "modal-synthesis-59954b9028b9ee24", "priority": 0.670935741555, "reconstruction_loss": 0.670935741555, "sample_id": "us-code-36-20505-b2cd4bd7e9ff3189"}`
  evidence: `{"cosine_similarity": 0.414635142116, "hint_id": "modal-synthesis-983b686917290537", "priority": 0.249196718776, "reconstruction_loss": 0.249196718776, "sample_id": "us-code-50-2589.-4df1e87fe9e5d1f6"}`

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
- `program-08326e4a8ba01923`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-08326e4a8ba01923` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.579350006897`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-9922.-6a2850121a24ddc0, us-code-42-15208.-aec488d546c39fc6, us-code-25-414-425141361dbb72f9, us-code-42-13384.-c1019817b4fc691f`
  evidence: `{"cosine_similarity": 0.022341642065, "hint_id": "modal-synthesis-6435f7b9afb1d816", "priority": 0.509775266069, "reconstruction_loss": 0.509775266069, "sample_id": "us-code-42-15208.-aec488d546c39fc6"}`
  evidence: `{"cosine_similarity": -0.123645320008, "hint_id": "modal-synthesis-6beb9b02d4ec10eb", "priority": 0.505320433928, "reconstruction_loss": 0.505320433928, "sample_id": "us-code-25-414-425141361dbb72f9"}`
  evidence: `{"cosine_similarity": -0.489768528804, "hint_id": "modal-synthesis-7f1481df3a7ba41d", "priority": 1.036934917036, "reconstruction_loss": 1.036934917036, "sample_id": "us-code-42-9922.-6a2850121a24ddc0"}`
  evidence: `{"cosine_similarity": 0.486925391109, "hint_id": "modal-synthesis-90f3227febfdcf99", "priority": 0.265369410555, "reconstruction_loss": 0.265369410555, "sample_id": "us-code-42-13384.-c1019817b4fc691f"}`
- `program-4e9035257303f27f`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-08326e4a8ba01923` score `0.994789`
  loss: `autoencoder_residual_cluster` = `0.323692701817`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-43-1470.-845d9dceb9d264ab, us-code-10-8669-847a57d070221b74, us-code-42-16092.-a56ba67c3bcab0b8, us-code-33-741-6af99be469b97863`
  evidence: `{"cosine_similarity": 0.517165647577, "hint_id": "modal-synthesis-492c5b4d7b2acae6", "priority": 0.291446790609, "reconstruction_loss": 0.291446790609, "sample_id": "us-code-42-16092.-a56ba67c3bcab0b8"}`
  evidence: `{"cosine_similarity": 0.485999458648, "hint_id": "modal-synthesis-5193e85a4b9d9acd", "priority": 0.204671694544, "reconstruction_loss": 0.204671694544, "sample_id": "us-code-33-741-6af99be469b97863"}`
  evidence: `{"cosine_similarity": -0.46509485212, "hint_id": "modal-synthesis-7c967c5c223f11f1", "priority": 0.487950161311, "reconstruction_loss": 0.487950161311, "sample_id": "us-code-43-1470.-845d9dceb9d264ab"}`
  evidence: `{"cosine_similarity": 0.146943617895, "hint_id": "modal-synthesis-99862bfb52616d38", "priority": 0.310702160803, "reconstruction_loss": 0.310702160803, "sample_id": "us-code-10-8669-847a57d070221b74"}`
- `program-42c21429f91982a6`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-08326e4a8ba01923` score `0.994532`
  loss: `autoencoder_residual_cluster` = `0.424385584511`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-36-20505-b2cd4bd7e9ff3189, us-code-7-1291-cfb67427fb37305d, us-code-22-4504-df643192e117d651, us-code-50-2589.-4df1e87fe9e5d1f6`
  evidence: `{"cosine_similarity": 0.309862376184, "hint_id": "modal-synthesis-1afcdb764e2e2b34", "priority": 0.392416653563, "reconstruction_loss": 0.392416653563, "sample_id": "us-code-7-1291-cfb67427fb37305d"}`
  evidence: `{"cosine_similarity": 0.048211956391, "hint_id": "modal-synthesis-4b9866bd5ac48d94", "priority": 0.38499322415, "reconstruction_loss": 0.38499322415, "sample_id": "us-code-22-4504-df643192e117d651"}`
  evidence: `{"cosine_similarity": -0.017907317672, "hint_id": "modal-synthesis-59954b9028b9ee24", "priority": 0.670935741555, "reconstruction_loss": 0.670935741555, "sample_id": "us-code-36-20505-b2cd4bd7e9ff3189"}`
  evidence: `{"cosine_similarity": 0.414635142116, "hint_id": "modal-synthesis-983b686917290537", "priority": 0.249196718776, "reconstruction_loss": 0.249196718776, "sample_id": "us-code-50-2589.-4df1e87fe9e5d1f6"}`
