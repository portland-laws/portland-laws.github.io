# packet-000036

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000036/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000036/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000036-20260518_105657

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-0472b2b2e8284920` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0472b2b2e8284920` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.588873601317, "hint_id": "modal-synthesis-2d061cb85741a6d4", "priority": 0.700526111718, "reconstruction_loss": 0.700526111718, "sample_id": "us-code-26-545-e844f7e70e47bdb2"}`
  evidence: `{"cosine_similarity": -0.281625933848, "hint_id": "modal-synthesis-68b6626685dd8a08", "priority": 0.674168666564, "reconstruction_loss": 0.674168666564, "sample_id": "us-code-43-945a.-ffbb2568c7c9e046"}`
  evidence: `{"cosine_similarity": 0.259659211422, "hint_id": "modal-synthesis-739ca07bd9378a3c", "priority": 0.272708100078, "reconstruction_loss": 0.272708100078, "sample_id": "us-code-16-460aa-6-7ec22a0841ca5cd9"}`
  evidence: `{"cosine_similarity": -0.239020853765, "hint_id": "modal-synthesis-83846a474af1db78", "priority": 0.534965274118, "reconstruction_loss": 0.534965274118, "sample_id": "us-code-43-210.-ceab38cde0568989"}`
- `program-7095df61ab39ec12` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0472b2b2e8284920` score `0.995684`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.210920967642, "hint_id": "modal-synthesis-10b89f137514c8ac", "priority": 0.361404616071, "reconstruction_loss": 0.361404616071, "sample_id": "us-code-16-824o-484f99e8978d7c55"}`
  evidence: `{"cosine_similarity": -0.271378327707, "hint_id": "modal-synthesis-66720f69ab6ccd29", "priority": 0.763102469369, "reconstruction_loss": 0.763102469369, "sample_id": "us-code-16-460iii-4-aa834016adcc86bf"}`
  evidence: `{"cosine_similarity": -0.060831413738, "hint_id": "modal-synthesis-688c1bf3559df9f5", "priority": 0.38185294257, "reconstruction_loss": 0.38185294257, "sample_id": "us-code-20-1472-805b4875835f483a"}`
  evidence: `{"cosine_similarity": 0.421574929837, "hint_id": "modal-synthesis-f385cc4e0dc355f9", "priority": 0.197936754336, "reconstruction_loss": 0.197936754336, "sample_id": "us-code-18-706-4dd528404c310241"}`
- `program-c2e1c787c5c8f7af` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0472b2b2e8284920` score `0.995635`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.048544889529, "hint_id": "modal-synthesis-3e33616de433b882", "priority": 0.471817526644, "reconstruction_loss": 0.471817526644, "sample_id": "us-code-19-1671a-8cd716bcc93cd7ef"}`
  evidence: `{"cosine_similarity": -0.12185288031, "hint_id": "modal-synthesis-5f2ace3371243cf7", "priority": 0.390570987729, "reconstruction_loss": 0.390570987729, "sample_id": "us-code-10-2851-be006a5e0fb36ac2"}`
  evidence: `{"cosine_similarity": -0.142128219936, "hint_id": "modal-synthesis-813467187206884f", "priority": 0.665584767773, "reconstruction_loss": 0.665584767773, "sample_id": "us-code-43-617t.-8a859da74ac1439f"}`
  evidence: `{"cosine_similarity": -0.139388233457, "hint_id": "modal-synthesis-f6a0c7b93ec818c1", "priority": 0.469504197936, "reconstruction_loss": 0.469504197936, "sample_id": "us-code-22-5952-8438638659244d8a"}`

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
- `program-0472b2b2e8284920`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0472b2b2e8284920` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.545592038119`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-545-e844f7e70e47bdb2, us-code-43-945a.-ffbb2568c7c9e046, us-code-43-210.-ceab38cde0568989, us-code-16-460aa-6-7ec22a0841ca5cd9`
  evidence: `{"cosine_similarity": -0.588873601317, "hint_id": "modal-synthesis-2d061cb85741a6d4", "priority": 0.700526111718, "reconstruction_loss": 0.700526111718, "sample_id": "us-code-26-545-e844f7e70e47bdb2"}`
  evidence: `{"cosine_similarity": -0.281625933848, "hint_id": "modal-synthesis-68b6626685dd8a08", "priority": 0.674168666564, "reconstruction_loss": 0.674168666564, "sample_id": "us-code-43-945a.-ffbb2568c7c9e046"}`
  evidence: `{"cosine_similarity": 0.259659211422, "hint_id": "modal-synthesis-739ca07bd9378a3c", "priority": 0.272708100078, "reconstruction_loss": 0.272708100078, "sample_id": "us-code-16-460aa-6-7ec22a0841ca5cd9"}`
  evidence: `{"cosine_similarity": -0.239020853765, "hint_id": "modal-synthesis-83846a474af1db78", "priority": 0.534965274118, "reconstruction_loss": 0.534965274118, "sample_id": "us-code-43-210.-ceab38cde0568989"}`
- `program-7095df61ab39ec12`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0472b2b2e8284920` score `0.995684`
  loss: `autoencoder_residual_cluster` = `0.426074195587`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-16-460iii-4-aa834016adcc86bf, us-code-20-1472-805b4875835f483a, us-code-16-824o-484f99e8978d7c55, us-code-18-706-4dd528404c310241`
  evidence: `{"cosine_similarity": 0.210920967642, "hint_id": "modal-synthesis-10b89f137514c8ac", "priority": 0.361404616071, "reconstruction_loss": 0.361404616071, "sample_id": "us-code-16-824o-484f99e8978d7c55"}`
  evidence: `{"cosine_similarity": -0.271378327707, "hint_id": "modal-synthesis-66720f69ab6ccd29", "priority": 0.763102469369, "reconstruction_loss": 0.763102469369, "sample_id": "us-code-16-460iii-4-aa834016adcc86bf"}`
  evidence: `{"cosine_similarity": -0.060831413738, "hint_id": "modal-synthesis-688c1bf3559df9f5", "priority": 0.38185294257, "reconstruction_loss": 0.38185294257, "sample_id": "us-code-20-1472-805b4875835f483a"}`
  evidence: `{"cosine_similarity": 0.421574929837, "hint_id": "modal-synthesis-f385cc4e0dc355f9", "priority": 0.197936754336, "reconstruction_loss": 0.197936754336, "sample_id": "us-code-18-706-4dd528404c310241"}`
- `program-c2e1c787c5c8f7af`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0472b2b2e8284920` score `0.995635`
  loss: `autoencoder_residual_cluster` = `0.499369370021`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-43-617t.-8a859da74ac1439f, us-code-19-1671a-8cd716bcc93cd7ef, us-code-22-5952-8438638659244d8a, us-code-10-2851-be006a5e0fb36ac2`
  evidence: `{"cosine_similarity": -0.048544889529, "hint_id": "modal-synthesis-3e33616de433b882", "priority": 0.471817526644, "reconstruction_loss": 0.471817526644, "sample_id": "us-code-19-1671a-8cd716bcc93cd7ef"}`
  evidence: `{"cosine_similarity": -0.12185288031, "hint_id": "modal-synthesis-5f2ace3371243cf7", "priority": 0.390570987729, "reconstruction_loss": 0.390570987729, "sample_id": "us-code-10-2851-be006a5e0fb36ac2"}`
  evidence: `{"cosine_similarity": -0.142128219936, "hint_id": "modal-synthesis-813467187206884f", "priority": 0.665584767773, "reconstruction_loss": 0.665584767773, "sample_id": "us-code-43-617t.-8a859da74ac1439f"}`
  evidence: `{"cosine_similarity": -0.139388233457, "hint_id": "modal-synthesis-f6a0c7b93ec818c1", "priority": 0.469504197936, "reconstruction_loss": 0.469504197936, "sample_id": "us-code-22-5952-8438638659244d8a"}`
