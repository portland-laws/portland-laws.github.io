# packet-000007

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000007/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000007/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000007-20260518_073309

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b97a51e39405db7d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b97a51e39405db7d` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.14929550996, "hint_id": "modal-synthesis-15f1c6bc2982da47", "priority": 0.537501052335, "reconstruction_loss": 0.537501052335, "sample_id": "us-code-42-4104c.-bd287c7c45a3de65"}`
  evidence: `{"cosine_similarity": -0.474920291379, "hint_id": "modal-synthesis-52dd2eed4e7a29c7", "priority": 0.691797963032, "reconstruction_loss": 0.691797963032, "sample_id": "us-code-23-173-ccdec7fdb8dc3d0a"}`
  evidence: `{"cosine_similarity": -0.246905204381, "hint_id": "modal-synthesis-5c8f2217b50ad353", "priority": 0.873564766616, "reconstruction_loss": 0.873564766616, "sample_id": "us-code-22-290n-0c52774a7cfafab5"}`
  evidence: `{"cosine_similarity": 0.035160607894, "hint_id": "modal-synthesis-ebbfec70ccc83286", "priority": 0.363854349593, "reconstruction_loss": 0.363854349593, "sample_id": "us-code-43-1181i.-e187d4207221870b"}`
- `program-a64ea0719053e01e` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b97a51e39405db7d` score `0.994739`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.293465853753, "hint_id": "modal-synthesis-303a2af79a873ddf", "priority": 0.257647251324, "reconstruction_loss": 0.257647251324, "sample_id": "us-code-7-473a-02a85f2b18cfe8ee"}`
  evidence: `{"cosine_similarity": 0.640810805549, "hint_id": "modal-synthesis-312b138185b3d088", "priority": 0.139077152974, "reconstruction_loss": 0.139077152974, "sample_id": "us-code-7-3125-7e90453fbb54b8b5"}`
  evidence: `{"cosine_similarity": 0.52589381931, "hint_id": "modal-synthesis-3dd9b313b4107775", "priority": 0.293663259958, "reconstruction_loss": 0.293663259958, "sample_id": "us-code-42-11924.-096a2b2493c6c5cf"}`
  evidence: `{"cosine_similarity": 0.024033188537, "hint_id": "modal-synthesis-a33d33e3baaa4971", "priority": 0.482134546018, "reconstruction_loss": 0.482134546018, "sample_id": "us-code-26-45N-50d302a360db7728"}`
- `program-d6221d24385b804c` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b97a51e39405db7d` score `0.994417`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.303653591498, "hint_id": "modal-synthesis-16b51d8158bfd725", "priority": 0.399033690718, "reconstruction_loss": 0.399033690718, "sample_id": "us-code-38-1713-e735515303a49cfa"}`
  evidence: `{"cosine_similarity": -0.189142929136, "hint_id": "modal-synthesis-3019b7379c642c3a", "priority": 0.497515983542, "reconstruction_loss": 0.497515983542, "sample_id": "us-code-50-4404.-6d49b3d0dad76216"}`
  evidence: `{"cosine_similarity": 0.502267127394, "hint_id": "modal-synthesis-48647f721091a38e", "priority": 0.197526194208, "reconstruction_loss": 0.197526194208, "sample_id": "us-code-26-4241-60de6f4e807ab1a0"}`
  evidence: `{"cosine_similarity": 0.324437910033, "hint_id": "modal-synthesis-f3914d07d504b9c7", "priority": 0.407150683423, "reconstruction_loss": 0.407150683423, "sample_id": "us-code-25-992-2ec4bf6af06b8e98"}`

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
- `program-b97a51e39405db7d`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b97a51e39405db7d` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.616679532894`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-22-290n-0c52774a7cfafab5, us-code-23-173-ccdec7fdb8dc3d0a, us-code-42-4104c.-bd287c7c45a3de65, us-code-43-1181i.-e187d4207221870b`
  evidence: `{"cosine_similarity": -0.14929550996, "hint_id": "modal-synthesis-15f1c6bc2982da47", "priority": 0.537501052335, "reconstruction_loss": 0.537501052335, "sample_id": "us-code-42-4104c.-bd287c7c45a3de65"}`
  evidence: `{"cosine_similarity": -0.474920291379, "hint_id": "modal-synthesis-52dd2eed4e7a29c7", "priority": 0.691797963032, "reconstruction_loss": 0.691797963032, "sample_id": "us-code-23-173-ccdec7fdb8dc3d0a"}`
  evidence: `{"cosine_similarity": -0.246905204381, "hint_id": "modal-synthesis-5c8f2217b50ad353", "priority": 0.873564766616, "reconstruction_loss": 0.873564766616, "sample_id": "us-code-22-290n-0c52774a7cfafab5"}`
  evidence: `{"cosine_similarity": 0.035160607894, "hint_id": "modal-synthesis-ebbfec70ccc83286", "priority": 0.363854349593, "reconstruction_loss": 0.363854349593, "sample_id": "us-code-43-1181i.-e187d4207221870b"}`
- `program-a64ea0719053e01e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b97a51e39405db7d` score `0.994739`
  loss: `autoencoder_residual_cluster` = `0.293130552569`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-45N-50d302a360db7728, us-code-42-11924.-096a2b2493c6c5cf, us-code-7-473a-02a85f2b18cfe8ee, us-code-7-3125-7e90453fbb54b8b5`
  evidence: `{"cosine_similarity": 0.293465853753, "hint_id": "modal-synthesis-303a2af79a873ddf", "priority": 0.257647251324, "reconstruction_loss": 0.257647251324, "sample_id": "us-code-7-473a-02a85f2b18cfe8ee"}`
  evidence: `{"cosine_similarity": 0.640810805549, "hint_id": "modal-synthesis-312b138185b3d088", "priority": 0.139077152974, "reconstruction_loss": 0.139077152974, "sample_id": "us-code-7-3125-7e90453fbb54b8b5"}`
  evidence: `{"cosine_similarity": 0.52589381931, "hint_id": "modal-synthesis-3dd9b313b4107775", "priority": 0.293663259958, "reconstruction_loss": 0.293663259958, "sample_id": "us-code-42-11924.-096a2b2493c6c5cf"}`
  evidence: `{"cosine_similarity": 0.024033188537, "hint_id": "modal-synthesis-a33d33e3baaa4971", "priority": 0.482134546018, "reconstruction_loss": 0.482134546018, "sample_id": "us-code-26-45N-50d302a360db7728"}`
- `program-d6221d24385b804c`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b97a51e39405db7d` score `0.994417`
  loss: `autoencoder_residual_cluster` = `0.375306637973`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-50-4404.-6d49b3d0dad76216, us-code-25-992-2ec4bf6af06b8e98, us-code-38-1713-e735515303a49cfa, us-code-26-4241-60de6f4e807ab1a0`
  evidence: `{"cosine_similarity": 0.303653591498, "hint_id": "modal-synthesis-16b51d8158bfd725", "priority": 0.399033690718, "reconstruction_loss": 0.399033690718, "sample_id": "us-code-38-1713-e735515303a49cfa"}`
  evidence: `{"cosine_similarity": -0.189142929136, "hint_id": "modal-synthesis-3019b7379c642c3a", "priority": 0.497515983542, "reconstruction_loss": 0.497515983542, "sample_id": "us-code-50-4404.-6d49b3d0dad76216"}`
  evidence: `{"cosine_similarity": 0.502267127394, "hint_id": "modal-synthesis-48647f721091a38e", "priority": 0.197526194208, "reconstruction_loss": 0.197526194208, "sample_id": "us-code-26-4241-60de6f4e807ab1a0"}`
  evidence: `{"cosine_similarity": 0.324437910033, "hint_id": "modal-synthesis-f3914d07d504b9c7", "priority": 0.407150683423, "reconstruction_loss": 0.407150683423, "sample_id": "us-code-25-992-2ec4bf6af06b8e98"}`
