# packet-000017

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000017/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000017/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000017-20260518_085309

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-db1c984534b900a2` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db1c984534b900a2` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.555290303938, "hint_id": "modal-synthesis-6fa76513f80a64e3", "priority": 0.810080344498, "reconstruction_loss": 0.810080344498, "sample_id": "us-code-7-6807-8b07fd1cc236bb34"}`
  evidence: `{"cosine_similarity": -0.363232220195, "hint_id": "modal-synthesis-70d77028494d4876", "priority": 0.604384433046, "reconstruction_loss": 0.604384433046, "sample_id": "us-code-22-2352-0a855e3845cf880c"}`
  evidence: `{"cosine_similarity": -0.289491744863, "hint_id": "modal-synthesis-86b89a7cfcf49447", "priority": 0.560957688813, "reconstruction_loss": 0.560957688813, "sample_id": "us-code-12-2181-352a48b58c4681cd"}`
  evidence: `{"cosine_similarity": 0.249335463163, "hint_id": "modal-synthesis-d2703a20c4150a48", "priority": 0.429917966844, "reconstruction_loss": 0.429917966844, "sample_id": "us-code-46-60501.-d2e0cc2bf85badf2"}`
- `program-4821c0fc8a502aa4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db1c984534b900a2` score `0.994953`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.001439977935, "hint_id": "modal-synthesis-43293203720941ed", "priority": 0.493185632382, "reconstruction_loss": 0.493185632382, "sample_id": "us-code-26-6071-40357f1b21882f9e"}`
  evidence: `{"cosine_similarity": 0.536941848245, "hint_id": "modal-synthesis-8e21c68f968fad42", "priority": 0.343027098781, "reconstruction_loss": 0.343027098781, "sample_id": "us-code-48-750.-646cac86322e0f43"}`
  evidence: `{"cosine_similarity": -0.452277523087, "hint_id": "modal-synthesis-be5ef7f07eaafb6e", "priority": 0.611143621452, "reconstruction_loss": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
  evidence: `{"cosine_similarity": 0.298022150172, "hint_id": "modal-synthesis-f6e587297f82b2fc", "priority": 0.364586517302, "reconstruction_loss": 0.364586517302, "sample_id": "us-code-16-3865a-9ba00676060af2a4"}`
- `program-1631c0a5a6ea0d17` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db1c984534b900a2` score `0.994815`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.023558460322, "hint_id": "modal-synthesis-0901257cf091c9e6", "priority": 0.468636621947, "reconstruction_loss": 0.468636621947, "sample_id": "us-code-42-14041a-880d93707d48f95b"}`
  evidence: `{"cosine_similarity": 0.306515372927, "hint_id": "modal-synthesis-abdbdc19956583b3", "priority": 0.407340628107, "reconstruction_loss": 0.407340628107, "sample_id": "us-code-22-1643m-5242bf8f9ab76629"}`
  evidence: `{"cosine_similarity": -0.689783129866, "hint_id": "modal-synthesis-cc64f00e4e445e1b", "priority": 0.863282190566, "reconstruction_loss": 0.863282190566, "sample_id": "us-code-51-60604.-82ff42829bbdeb0f"}`
  evidence: `{"cosine_similarity": -0.030890662305, "hint_id": "modal-synthesis-dd846b372b8a01f1", "priority": 0.332509516781, "reconstruction_loss": 0.332509516781, "sample_id": "us-code-20-6111-6077986049984507"}`

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
- `program-db1c984534b900a2`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db1c984534b900a2` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.6013351083`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-6807-8b07fd1cc236bb34, us-code-22-2352-0a855e3845cf880c, us-code-12-2181-352a48b58c4681cd, us-code-46-60501.-d2e0cc2bf85badf2`
  evidence: `{"cosine_similarity": -0.555290303938, "hint_id": "modal-synthesis-6fa76513f80a64e3", "priority": 0.810080344498, "reconstruction_loss": 0.810080344498, "sample_id": "us-code-7-6807-8b07fd1cc236bb34"}`
  evidence: `{"cosine_similarity": -0.363232220195, "hint_id": "modal-synthesis-70d77028494d4876", "priority": 0.604384433046, "reconstruction_loss": 0.604384433046, "sample_id": "us-code-22-2352-0a855e3845cf880c"}`
  evidence: `{"cosine_similarity": -0.289491744863, "hint_id": "modal-synthesis-86b89a7cfcf49447", "priority": 0.560957688813, "reconstruction_loss": 0.560957688813, "sample_id": "us-code-12-2181-352a48b58c4681cd"}`
  evidence: `{"cosine_similarity": 0.249335463163, "hint_id": "modal-synthesis-d2703a20c4150a48", "priority": 0.429917966844, "reconstruction_loss": 0.429917966844, "sample_id": "us-code-46-60501.-d2e0cc2bf85badf2"}`
- `program-4821c0fc8a502aa4`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db1c984534b900a2` score `0.994953`
  loss: `autoencoder_residual_cluster` = `0.452985717479`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-15-1717a-f876cffa460ff996, us-code-26-6071-40357f1b21882f9e, us-code-16-3865a-9ba00676060af2a4, us-code-48-750.-646cac86322e0f43`
  evidence: `{"cosine_similarity": -0.001439977935, "hint_id": "modal-synthesis-43293203720941ed", "priority": 0.493185632382, "reconstruction_loss": 0.493185632382, "sample_id": "us-code-26-6071-40357f1b21882f9e"}`
  evidence: `{"cosine_similarity": 0.536941848245, "hint_id": "modal-synthesis-8e21c68f968fad42", "priority": 0.343027098781, "reconstruction_loss": 0.343027098781, "sample_id": "us-code-48-750.-646cac86322e0f43"}`
  evidence: `{"cosine_similarity": -0.452277523087, "hint_id": "modal-synthesis-be5ef7f07eaafb6e", "priority": 0.611143621452, "reconstruction_loss": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
  evidence: `{"cosine_similarity": 0.298022150172, "hint_id": "modal-synthesis-f6e587297f82b2fc", "priority": 0.364586517302, "reconstruction_loss": 0.364586517302, "sample_id": "us-code-16-3865a-9ba00676060af2a4"}`
- `program-1631c0a5a6ea0d17`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-db1c984534b900a2` score `0.994815`
  loss: `autoencoder_residual_cluster` = `0.51794223935`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-51-60604.-82ff42829bbdeb0f, us-code-42-14041a-880d93707d48f95b, us-code-22-1643m-5242bf8f9ab76629, us-code-20-6111-6077986049984507`
  evidence: `{"cosine_similarity": 0.023558460322, "hint_id": "modal-synthesis-0901257cf091c9e6", "priority": 0.468636621947, "reconstruction_loss": 0.468636621947, "sample_id": "us-code-42-14041a-880d93707d48f95b"}`
  evidence: `{"cosine_similarity": 0.306515372927, "hint_id": "modal-synthesis-abdbdc19956583b3", "priority": 0.407340628107, "reconstruction_loss": 0.407340628107, "sample_id": "us-code-22-1643m-5242bf8f9ab76629"}`
  evidence: `{"cosine_similarity": -0.689783129866, "hint_id": "modal-synthesis-cc64f00e4e445e1b", "priority": 0.863282190566, "reconstruction_loss": 0.863282190566, "sample_id": "us-code-51-60604.-82ff42829bbdeb0f"}`
  evidence: `{"cosine_similarity": -0.030890662305, "hint_id": "modal-synthesis-dd846b372b8a01f1", "priority": 0.332509516781, "reconstruction_loss": 0.332509516781, "sample_id": "us-code-20-6111-6077986049984507"}`
