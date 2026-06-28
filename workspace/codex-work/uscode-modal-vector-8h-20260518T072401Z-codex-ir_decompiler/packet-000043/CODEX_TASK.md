# packet-000043

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000043/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000043/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000043-20260518_113358

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b00d051b4203e2fc` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b00d051b4203e2fc` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.29431010412, "hint_id": "modal-synthesis-13bfa15cab632f14", "priority": 0.730877191751, "reconstruction_loss": 0.730877191751, "sample_id": "us-code-20-1087j-0490e47d7295e7cf"}`
  evidence: `{"cosine_similarity": 0.339719682755, "hint_id": "modal-synthesis-8a9cb5262660e914", "priority": 0.440448773375, "reconstruction_loss": 0.440448773375, "sample_id": "us-code-16-460l-11-86a79c62827d6197"}`
  evidence: `{"cosine_similarity": -0.075161584547, "hint_id": "modal-synthesis-bf16375874b9daf1", "priority": 0.406830986477, "reconstruction_loss": 0.406830986477, "sample_id": "us-code-42-1437q.-fd99198f04945241"}`
  evidence: `{"cosine_similarity": -0.454981301749, "hint_id": "modal-synthesis-c0f70e4f4fa6a22c", "priority": 0.546089550232, "reconstruction_loss": 0.546089550232, "sample_id": "us-code-38-3902-37f2f91f0bd50c67"}`
- `program-ea4b54b78d806545` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b00d051b4203e2fc` score `0.994358`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.564991074594, "hint_id": "modal-synthesis-3a7a6152dad9e538", "priority": 0.539604607644, "reconstruction_loss": 0.539604607644, "sample_id": "us-code-42-12314.-f250378025962578"}`
  evidence: `{"cosine_similarity": -0.230802844859, "hint_id": "modal-synthesis-5328399584bd0542", "priority": 0.394933069044, "reconstruction_loss": 0.394933069044, "sample_id": "us-code-15-3602-93078b4432f6e586"}`
  evidence: `{"cosine_similarity": -0.218439912669, "hint_id": "modal-synthesis-81a3b3497dec135b", "priority": 0.399525488113, "reconstruction_loss": 0.399525488113, "sample_id": "us-code-46-2118.-46c89025e4ffff33"}`
  evidence: `{"cosine_similarity": 0.349524549756, "hint_id": "modal-synthesis-b7365a877c40cf34", "priority": 0.301243646946, "reconstruction_loss": 0.301243646946, "sample_id": "us-code-25-2706-e7765cee1ab260c9"}`
- `program-e3ae972ab98ff83f` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b00d051b4203e2fc` score `0.99433`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.473352575208, "hint_id": "modal-synthesis-0d61b139901efc47", "priority": 0.32384748889, "reconstruction_loss": 0.32384748889, "sample_id": "us-code-22-1631g-76465af846ae83c5"}`
  evidence: `{"cosine_similarity": -0.489394547606, "hint_id": "modal-synthesis-8d1e6ff344e9b26f", "priority": 0.62759126106, "reconstruction_loss": 0.62759126106, "sample_id": "us-code-42-6862.-0536fcc366ee4b48"}`
  evidence: `{"cosine_similarity": 0.049554690779, "hint_id": "modal-synthesis-9dce4485193f1205", "priority": 0.343360976559, "reconstruction_loss": 0.343360976559, "sample_id": "us-code-12-1231-ba6e0509cf64961b"}`
  evidence: `{"cosine_similarity": -0.347873675028, "hint_id": "modal-synthesis-d2fb1d6e1f4af891", "priority": 0.679720377117, "reconstruction_loss": 0.679720377117, "sample_id": "us-code-42-12896.-2aeee9502d28172d"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
