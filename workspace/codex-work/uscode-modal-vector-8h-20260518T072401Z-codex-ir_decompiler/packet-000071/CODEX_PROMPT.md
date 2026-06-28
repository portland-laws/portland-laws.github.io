# packet-000071

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000071/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000071/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000071-20260518_142259

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-59470f629f688a56` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-59470f629f688a56` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.236918717947, "hint_id": "modal-synthesis-62812ac6666dfdfb", "priority": 0.644613894247, "reconstruction_loss": 0.644613894247, "sample_id": "us-code-38-1112-f0e24cbe38ce5fe1"}`
  evidence: `{"cosine_similarity": 0.763611455839, "hint_id": "modal-synthesis-7db474fd986f1cb5", "priority": 0.24384640413, "reconstruction_loss": 0.24384640413, "sample_id": "us-code-7-3410-0c5ab5858b832fa2"}`
  evidence: `{"cosine_similarity": 0.494557755107, "hint_id": "modal-synthesis-8a5fea5e9baf85ee", "priority": 0.321942796497, "reconstruction_loss": 0.321942796497, "sample_id": "us-code-10-445-51be3a57b68adc2a"}`
  evidence: `{"cosine_similarity": -0.490676650836, "hint_id": "modal-synthesis-b3428eb0f8be066b", "priority": 0.723310006342, "reconstruction_loss": 0.723310006342, "sample_id": "us-code-42-6249b.-bff099cb6a65aca9"}`
- `program-22411718a98588a9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-59470f629f688a56` score `0.993662`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.432624047609, "hint_id": "modal-synthesis-7969098b166fbd1a", "priority": 0.437919052434, "reconstruction_loss": 0.437919052434, "sample_id": "us-code-50-31 to 39.-36a4389acae72564"}`
  evidence: `{"cosine_similarity": -0.752301724341, "hint_id": "modal-synthesis-a049a96e22a3774d", "priority": 0.467777112972, "reconstruction_loss": 0.467777112972, "sample_id": "us-code-18-113-96ad4d69f55e5310"}`
  evidence: `{"cosine_similarity": 0.131346083662, "hint_id": "modal-synthesis-f0ebccc13c41d4c7", "priority": 0.335294450336, "reconstruction_loss": 0.335294450336, "sample_id": "us-code-43-315m-5b5794858e94b004"}`
  evidence: `{"cosine_similarity": -0.175344320562, "hint_id": "modal-synthesis-fc0581eb1d447eee", "priority": 0.544288175511, "reconstruction_loss": 0.544288175511, "sample_id": "us-code-50-3352e.-f6ee437367ffa0d0"}`
- `program-8e9e6ddab881b8e1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-59470f629f688a56` score `0.993569`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.052735118198, "hint_id": "modal-synthesis-4012de1096265d2e", "priority": 0.346189355063, "reconstruction_loss": 0.346189355063, "sample_id": "us-code-47-332.-81ee7dd52fd33a88"}`
  evidence: `{"cosine_similarity": 0.232510781455, "hint_id": "modal-synthesis-b4b9a683f1e659f4", "priority": 0.387677206211, "reconstruction_loss": 0.387677206211, "sample_id": "us-code-38-7623-b7954ba3754d620e"}`
  evidence: `{"cosine_similarity": -0.056942563045, "hint_id": "modal-synthesis-d6929cea4ef00381", "priority": 0.473411487838, "reconstruction_loss": 0.473411487838, "sample_id": "us-code-29-703-8699ac3daa592f5e"}`
  evidence: `{"cosine_similarity": -0.167679121927, "hint_id": "modal-synthesis-fba36416c9d65569", "priority": 0.264149641629, "reconstruction_loss": 0.264149641629, "sample_id": "us-code-5-4119-be0c2eafe549c521"}`

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
- `program-59470f629f688a56`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-59470f629f688a56` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.483428275304`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-6249b.-bff099cb6a65aca9, us-code-38-1112-f0e24cbe38ce5fe1, us-code-10-445-51be3a57b68adc2a, us-code-7-3410-0c5ab5858b832fa2`
  evidence: `{"cosine_similarity": -0.236918717947, "hint_id": "modal-synthesis-62812ac6666dfdfb", "priority": 0.644613894247, "reconstruction_loss": 0.644613894247, "sample_id": "us-code-38-1112-f0e24cbe38ce5fe1"}`
  evidence: `{"cosine_similarity": 0.763611455839, "hint_id": "modal-synthesis-7db474fd986f1cb5", "priority": 0.24384640413, "reconstruction_loss": 0.24384640413, "sample_id": "us-code-7-3410-0c5ab5858b832fa2"}`
  evidence: `{"cosine_similarity": 0.494557755107, "hint_id": "modal-synthesis-8a5fea5e9baf85ee", "priority": 0.321942796497, "reconstruction_loss": 0.321942796497, "sample_id": "us-code-10-445-51be3a57b68adc2a"}`
  evidence: `{"cosine_similarity": -0.490676650836, "hint_id": "modal-synthesis-b3428eb0f8be066b", "priority": 0.723310006342, "reconstruction_loss": 0.723310006342, "sample_id": "us-code-42-6249b.-bff099cb6a65aca9"}`
- `program-22411718a98588a9`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-59470f629f688a56` score `0.993662`
  loss: `autoencoder_residual_cluster` = `0.446319697813`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-50-3352e.-f6ee437367ffa0d0, us-code-18-113-96ad4d69f55e5310, us-code-50-31 to 39.-36a4389acae72564, us-code-43-315m-5b5794858e94b004`
  evidence: `{"cosine_similarity": 0.432624047609, "hint_id": "modal-synthesis-7969098b166fbd1a", "priority": 0.437919052434, "reconstruction_loss": 0.437919052434, "sample_id": "us-code-50-31 to 39.-36a4389acae72564"}`
  evidence: `{"cosine_similarity": -0.752301724341, "hint_id": "modal-synthesis-a049a96e22a3774d", "priority": 0.467777112972, "reconstruction_loss": 0.467777112972, "sample_id": "us-code-18-113-96ad4d69f55e5310"}`
  evidence: `{"cosine_similarity": 0.131346083662, "hint_id": "modal-synthesis-f0ebccc13c41d4c7", "priority": 0.335294450336, "reconstruction_loss": 0.335294450336, "sample_id": "us-code-43-315m-5b5794858e94b004"}`
  evidence: `{"cosine_similarity": -0.175344320562, "hint_id": "modal-synthesis-fc0581eb1d447eee", "priority": 0.544288175511, "reconstruction_loss": 0.544288175511, "sample_id": "us-code-50-3352e.-f6ee437367ffa0d0"}`
- `program-8e9e6ddab881b8e1`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-59470f629f688a56` score `0.993569`
  loss: `autoencoder_residual_cluster` = `0.367856922685`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-29-703-8699ac3daa592f5e, us-code-38-7623-b7954ba3754d620e, us-code-47-332.-81ee7dd52fd33a88, us-code-5-4119-be0c2eafe549c521`
  evidence: `{"cosine_similarity": -0.052735118198, "hint_id": "modal-synthesis-4012de1096265d2e", "priority": 0.346189355063, "reconstruction_loss": 0.346189355063, "sample_id": "us-code-47-332.-81ee7dd52fd33a88"}`
  evidence: `{"cosine_similarity": 0.232510781455, "hint_id": "modal-synthesis-b4b9a683f1e659f4", "priority": 0.387677206211, "reconstruction_loss": 0.387677206211, "sample_id": "us-code-38-7623-b7954ba3754d620e"}`
  evidence: `{"cosine_similarity": -0.056942563045, "hint_id": "modal-synthesis-d6929cea4ef00381", "priority": 0.473411487838, "reconstruction_loss": 0.473411487838, "sample_id": "us-code-29-703-8699ac3daa592f5e"}`
  evidence: `{"cosine_similarity": -0.167679121927, "hint_id": "modal-synthesis-fba36416c9d65569", "priority": 0.264149641629, "reconstruction_loss": 0.264149641629, "sample_id": "us-code-5-4119-be0c2eafe549c521"}`
