# packet-000045

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000045/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000045/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000045-20260518_114634

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-aa4d1af825ebd1fb` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-aa4d1af825ebd1fb` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.09992262332, "hint_id": "modal-synthesis-24bc782e0ef1771e", "priority": 0.396393682917, "reconstruction_loss": 0.396393682917, "sample_id": "us-code-19-12-27bf6d26b2be162a"}`
  evidence: `{"cosine_similarity": -0.14593272022, "hint_id": "modal-synthesis-487122695004f30f", "priority": 0.528820104377, "reconstruction_loss": 0.528820104377, "sample_id": "us-code-45-431 to 447.-35f4b8b4ddbbb9e4"}`
  evidence: `{"cosine_similarity": -0.396274401575, "hint_id": "modal-synthesis-63362b9209fcb7ed", "priority": 0.555675680924, "reconstruction_loss": 0.555675680924, "sample_id": "us-code-6-972-b04dbcb626413138"}`
  evidence: `{"cosine_similarity": -0.306656813535, "hint_id": "modal-synthesis-ee1e8e5fc4d735eb", "priority": 0.627137927104, "reconstruction_loss": 0.627137927104, "sample_id": "us-code-7-2250-97062bb3e59aaede"}`
- `program-abfdafa01a6f7c65` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-aa4d1af825ebd1fb` score `0.995426`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.531092330114, "hint_id": "modal-synthesis-49e0c3601519a690", "priority": 0.854037437007, "reconstruction_loss": 0.854037437007, "sample_id": "us-code-10-1403-54dc83878b550e61"}`
  evidence: `{"cosine_similarity": 0.295551845618, "hint_id": "modal-synthesis-754f24c97aa18a13", "priority": 0.282835220751, "reconstruction_loss": 0.282835220751, "sample_id": "us-code-42-7274k.-3425917266957c3a"}`
  evidence: `{"cosine_similarity": -0.419416153943, "hint_id": "modal-synthesis-7efe81dcf62aaf12", "priority": 0.342615153292, "reconstruction_loss": 0.342615153292, "sample_id": "us-code-40-3311-a10ba2bec7527468"}`
  evidence: `{"cosine_similarity": 0.173264663536, "hint_id": "modal-synthesis-e820b260e4917b77", "priority": 0.26172824075, "reconstruction_loss": 0.26172824075, "sample_id": "us-code-21-356b-f17ebc571cf92c17"}`
- `program-6e912c685f081063` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-aa4d1af825ebd1fb` score `0.994265`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.044113241331, "hint_id": "modal-synthesis-2837fd8a39b7db7b", "priority": 0.413778579455, "reconstruction_loss": 0.413778579455, "sample_id": "us-code-6-1154-42d0dd5ec5341bfd"}`
  evidence: `{"cosine_similarity": -0.246286507282, "hint_id": "modal-synthesis-61e55a572736d6e4", "priority": 0.744687968606, "reconstruction_loss": 0.744687968606, "sample_id": "us-code-10-186-420e6415d46dc17d"}`
  evidence: `{"cosine_similarity": 0.175679818982, "hint_id": "modal-synthesis-993f29e9d1a2f369", "priority": 0.393206087093, "reconstruction_loss": 0.393206087093, "sample_id": "us-code-44-1305.-63681ee5004ef4e4"}`
  evidence: `{"cosine_similarity": -0.239154693704, "hint_id": "modal-synthesis-eb0bd23dcbdbf4d5", "priority": 0.544141867966, "reconstruction_loss": 0.544141867966, "sample_id": "us-code-38-3323-8d1776565a6d5ff4"}`

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
- `program-aa4d1af825ebd1fb`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-aa4d1af825ebd1fb` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.52700684883`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-2250-97062bb3e59aaede, us-code-6-972-b04dbcb626413138, us-code-45-431 to 447.-35f4b8b4ddbbb9e4, us-code-19-12-27bf6d26b2be162a`
  evidence: `{"cosine_similarity": 0.09992262332, "hint_id": "modal-synthesis-24bc782e0ef1771e", "priority": 0.396393682917, "reconstruction_loss": 0.396393682917, "sample_id": "us-code-19-12-27bf6d26b2be162a"}`
  evidence: `{"cosine_similarity": -0.14593272022, "hint_id": "modal-synthesis-487122695004f30f", "priority": 0.528820104377, "reconstruction_loss": 0.528820104377, "sample_id": "us-code-45-431 to 447.-35f4b8b4ddbbb9e4"}`
  evidence: `{"cosine_similarity": -0.396274401575, "hint_id": "modal-synthesis-63362b9209fcb7ed", "priority": 0.555675680924, "reconstruction_loss": 0.555675680924, "sample_id": "us-code-6-972-b04dbcb626413138"}`
  evidence: `{"cosine_similarity": -0.306656813535, "hint_id": "modal-synthesis-ee1e8e5fc4d735eb", "priority": 0.627137927104, "reconstruction_loss": 0.627137927104, "sample_id": "us-code-7-2250-97062bb3e59aaede"}`
- `program-abfdafa01a6f7c65`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-aa4d1af825ebd1fb` score `0.995426`
  loss: `autoencoder_residual_cluster` = `0.43530401295`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-10-1403-54dc83878b550e61, us-code-40-3311-a10ba2bec7527468, us-code-42-7274k.-3425917266957c3a, us-code-21-356b-f17ebc571cf92c17`
  evidence: `{"cosine_similarity": -0.531092330114, "hint_id": "modal-synthesis-49e0c3601519a690", "priority": 0.854037437007, "reconstruction_loss": 0.854037437007, "sample_id": "us-code-10-1403-54dc83878b550e61"}`
  evidence: `{"cosine_similarity": 0.295551845618, "hint_id": "modal-synthesis-754f24c97aa18a13", "priority": 0.282835220751, "reconstruction_loss": 0.282835220751, "sample_id": "us-code-42-7274k.-3425917266957c3a"}`
  evidence: `{"cosine_similarity": -0.419416153943, "hint_id": "modal-synthesis-7efe81dcf62aaf12", "priority": 0.342615153292, "reconstruction_loss": 0.342615153292, "sample_id": "us-code-40-3311-a10ba2bec7527468"}`
  evidence: `{"cosine_similarity": 0.173264663536, "hint_id": "modal-synthesis-e820b260e4917b77", "priority": 0.26172824075, "reconstruction_loss": 0.26172824075, "sample_id": "us-code-21-356b-f17ebc571cf92c17"}`
- `program-6e912c685f081063`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-aa4d1af825ebd1fb` score `0.994265`
  loss: `autoencoder_residual_cluster` = `0.52395362578`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-10-186-420e6415d46dc17d, us-code-38-3323-8d1776565a6d5ff4, us-code-6-1154-42d0dd5ec5341bfd, us-code-44-1305.-63681ee5004ef4e4`
  evidence: `{"cosine_similarity": 0.044113241331, "hint_id": "modal-synthesis-2837fd8a39b7db7b", "priority": 0.413778579455, "reconstruction_loss": 0.413778579455, "sample_id": "us-code-6-1154-42d0dd5ec5341bfd"}`
  evidence: `{"cosine_similarity": -0.246286507282, "hint_id": "modal-synthesis-61e55a572736d6e4", "priority": 0.744687968606, "reconstruction_loss": 0.744687968606, "sample_id": "us-code-10-186-420e6415d46dc17d"}`
  evidence: `{"cosine_similarity": 0.175679818982, "hint_id": "modal-synthesis-993f29e9d1a2f369", "priority": 0.393206087093, "reconstruction_loss": 0.393206087093, "sample_id": "us-code-44-1305.-63681ee5004ef4e4"}`
  evidence: `{"cosine_similarity": -0.239154693704, "hint_id": "modal-synthesis-eb0bd23dcbdbf4d5", "priority": 0.544141867966, "reconstruction_loss": 0.544141867966, "sample_id": "us-code-38-3323-8d1776565a6d5ff4"}`
