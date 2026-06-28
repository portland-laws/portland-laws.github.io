# packet-000065

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000065/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000065/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000065-20260518_134458

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b09df07de9683ac5` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b09df07de9683ac5` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.210121318247, "hint_id": "modal-synthesis-110cf7c13d84e5a1", "priority": 0.448540062305, "reconstruction_loss": 0.448540062305, "sample_id": "us-code-42-300gg-4b317252931e0967"}`
  evidence: `{"cosine_similarity": 0.494735039852, "hint_id": "modal-synthesis-7a83d4d750949ee2", "priority": 0.412419713932, "reconstruction_loss": 0.412419713932, "sample_id": "us-code-33-764-90bd06dc53b17d8e"}`
  evidence: `{"cosine_similarity": -0.003055179366, "hint_id": "modal-synthesis-b80496b618a1ce70", "priority": 0.574960461232, "reconstruction_loss": 0.574960461232, "sample_id": "us-code-25-1701-7ba72eb6960a502e"}`
  evidence: `{"cosine_similarity": -0.262389978123, "hint_id": "modal-synthesis-d94fcff6bcbbe1ed", "priority": 0.499651638599, "reconstruction_loss": 0.499651638599, "sample_id": "us-code-46-7109.-e0e5c9b6db3c8f64"}`
- `program-8ab6825a30521285` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b09df07de9683ac5` score `0.993466`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.439808342069, "hint_id": "modal-synthesis-21247bcecfeff53b", "priority": 0.332961004346, "reconstruction_loss": 0.332961004346, "sample_id": "us-code-41-3903-2f89a64325114fd0"}`
  evidence: `{"cosine_similarity": 0.292608064588, "hint_id": "modal-synthesis-2197ae988dff4910", "priority": 0.28895500273, "reconstruction_loss": 0.28895500273, "sample_id": "us-code-42-1583.-9e33f9b4f5ee068e"}`
  evidence: `{"cosine_similarity": 0.612902950296, "hint_id": "modal-synthesis-5204d9ba0319f983", "priority": 0.117867162318, "reconstruction_loss": 0.117867162318, "sample_id": "us-code-43-950.-b77ec793b2d96659"}`
  evidence: `{"cosine_similarity": -0.123507437363, "hint_id": "modal-synthesis-fa2876ded70ccb0a", "priority": 0.401885536137, "reconstruction_loss": 0.401885536137, "sample_id": "us-code-12-2147-a344e811e0974a4c"}`
- `program-bcf608b316b02e32` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b09df07de9683ac5` score `0.993412`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.061519366856, "hint_id": "modal-synthesis-1291024884aa1c45", "priority": 0.295949495167, "reconstruction_loss": 0.295949495167, "sample_id": "us-code-10-2512-1117c7c942280690"}`
  evidence: `{"cosine_similarity": -0.099934180343, "hint_id": "modal-synthesis-19c0398a7b716362", "priority": 0.519914196065, "reconstruction_loss": 0.519914196065, "sample_id": "us-code-10-8676-4f9d0cd6e98aa619"}`
  evidence: `{"cosine_similarity": -0.635006393559, "hint_id": "modal-synthesis-2088ef7914960a7c", "priority": 0.377164962444, "reconstruction_loss": 0.377164962444, "sample_id": "us-code-38-1723-b049061d923362b1"}`
  evidence: `{"cosine_similarity": 0.081182478097, "hint_id": "modal-synthesis-fe86dee1b06430a3", "priority": 0.498445302624, "reconstruction_loss": 0.498445302624, "sample_id": "us-code-18-203-c9486394d6acc318"}`

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
- `program-b09df07de9683ac5`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b09df07de9683ac5` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.483892969017`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-1701-7ba72eb6960a502e, us-code-46-7109.-e0e5c9b6db3c8f64, us-code-42-300gg-4b317252931e0967, us-code-33-764-90bd06dc53b17d8e`
  evidence: `{"cosine_similarity": -0.210121318247, "hint_id": "modal-synthesis-110cf7c13d84e5a1", "priority": 0.448540062305, "reconstruction_loss": 0.448540062305, "sample_id": "us-code-42-300gg-4b317252931e0967"}`
  evidence: `{"cosine_similarity": 0.494735039852, "hint_id": "modal-synthesis-7a83d4d750949ee2", "priority": 0.412419713932, "reconstruction_loss": 0.412419713932, "sample_id": "us-code-33-764-90bd06dc53b17d8e"}`
  evidence: `{"cosine_similarity": -0.003055179366, "hint_id": "modal-synthesis-b80496b618a1ce70", "priority": 0.574960461232, "reconstruction_loss": 0.574960461232, "sample_id": "us-code-25-1701-7ba72eb6960a502e"}`
  evidence: `{"cosine_similarity": -0.262389978123, "hint_id": "modal-synthesis-d94fcff6bcbbe1ed", "priority": 0.499651638599, "reconstruction_loss": 0.499651638599, "sample_id": "us-code-46-7109.-e0e5c9b6db3c8f64"}`
- `program-8ab6825a30521285`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b09df07de9683ac5` score `0.993466`
  loss: `autoencoder_residual_cluster` = `0.285417176383`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-12-2147-a344e811e0974a4c, us-code-41-3903-2f89a64325114fd0, us-code-42-1583.-9e33f9b4f5ee068e, us-code-43-950.-b77ec793b2d96659`
  evidence: `{"cosine_similarity": 0.439808342069, "hint_id": "modal-synthesis-21247bcecfeff53b", "priority": 0.332961004346, "reconstruction_loss": 0.332961004346, "sample_id": "us-code-41-3903-2f89a64325114fd0"}`
  evidence: `{"cosine_similarity": 0.292608064588, "hint_id": "modal-synthesis-2197ae988dff4910", "priority": 0.28895500273, "reconstruction_loss": 0.28895500273, "sample_id": "us-code-42-1583.-9e33f9b4f5ee068e"}`
  evidence: `{"cosine_similarity": 0.612902950296, "hint_id": "modal-synthesis-5204d9ba0319f983", "priority": 0.117867162318, "reconstruction_loss": 0.117867162318, "sample_id": "us-code-43-950.-b77ec793b2d96659"}`
  evidence: `{"cosine_similarity": -0.123507437363, "hint_id": "modal-synthesis-fa2876ded70ccb0a", "priority": 0.401885536137, "reconstruction_loss": 0.401885536137, "sample_id": "us-code-12-2147-a344e811e0974a4c"}`
- `program-bcf608b316b02e32`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b09df07de9683ac5` score `0.993412`
  loss: `autoencoder_residual_cluster` = `0.422868489075`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-10-8676-4f9d0cd6e98aa619, us-code-18-203-c9486394d6acc318, us-code-38-1723-b049061d923362b1, us-code-10-2512-1117c7c942280690`
  evidence: `{"cosine_similarity": 0.061519366856, "hint_id": "modal-synthesis-1291024884aa1c45", "priority": 0.295949495167, "reconstruction_loss": 0.295949495167, "sample_id": "us-code-10-2512-1117c7c942280690"}`
  evidence: `{"cosine_similarity": -0.099934180343, "hint_id": "modal-synthesis-19c0398a7b716362", "priority": 0.519914196065, "reconstruction_loss": 0.519914196065, "sample_id": "us-code-10-8676-4f9d0cd6e98aa619"}`
  evidence: `{"cosine_similarity": -0.635006393559, "hint_id": "modal-synthesis-2088ef7914960a7c", "priority": 0.377164962444, "reconstruction_loss": 0.377164962444, "sample_id": "us-code-38-1723-b049061d923362b1"}`
  evidence: `{"cosine_similarity": 0.081182478097, "hint_id": "modal-synthesis-fe86dee1b06430a3", "priority": 0.498445302624, "reconstruction_loss": 0.498445302624, "sample_id": "us-code-18-203-c9486394d6acc318"}`
