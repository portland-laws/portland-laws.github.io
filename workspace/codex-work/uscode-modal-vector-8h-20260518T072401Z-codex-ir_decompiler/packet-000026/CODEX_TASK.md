# packet-000026

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000026/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000026/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000026-20260518_095026

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-d509762191bc2364` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d509762191bc2364` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.633046063425, "hint_id": "modal-synthesis-5a2904e6c6a16326", "priority": 0.761675562071, "reconstruction_loss": 0.761675562071, "sample_id": "us-code-38-1925-906b279e597e2247"}`
  evidence: `{"cosine_similarity": -0.389889207147, "hint_id": "modal-synthesis-847681b442bec597", "priority": 0.927786016819, "reconstruction_loss": 0.927786016819, "sample_id": "us-code-42-300t-165b62726b1ad549"}`
  evidence: `{"cosine_similarity": -0.296259368792, "hint_id": "modal-synthesis-8835311c154c6c79", "priority": 0.540543306938, "reconstruction_loss": 0.540543306938, "sample_id": "us-code-16-119-85b9e2b8d0377d7c"}`
  evidence: `{"cosine_similarity": 0.064477700791, "hint_id": "modal-synthesis-adc00e81b9c6b63f", "priority": 0.194716402312, "reconstruction_loss": 0.194716402312, "sample_id": "us-code-42-1857c-8a5d6e801e2be154"}`
- `program-f46734a51afa496d` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d509762191bc2364` score `0.993936`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.209601573717, "hint_id": "modal-synthesis-0e452149efaaac69", "priority": 0.270495533878, "reconstruction_loss": 0.270495533878, "sample_id": "us-code-29-5-49e57ba33262a37b"}`
  evidence: `{"cosine_similarity": 0.491880634961, "hint_id": "modal-synthesis-22eb7120ea2f596a", "priority": 0.254756943444, "reconstruction_loss": 0.254756943444, "sample_id": "us-code-33-873-6c94d70b80c579d5"}`
  evidence: `{"cosine_similarity": -0.112946393583, "hint_id": "modal-synthesis-491a8805e093b378", "priority": 0.621555713621, "reconstruction_loss": 0.621555713621, "sample_id": "us-code-10-2801-622f10a8fc6c8a75"}`
  evidence: `{"cosine_similarity": 0.265693955041, "hint_id": "modal-synthesis-965610b420291db1", "priority": 0.427373678796, "reconstruction_loss": 0.427373678796, "sample_id": "us-code-42-71r.-8ea18fd6693a14dd"}`
- `program-0a54dd3abf334121` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-d509762191bc2364` score `0.993906`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.293307729701, "hint_id": "modal-synthesis-52b6001439c36efd", "priority": 0.80432393267, "reconstruction_loss": 0.80432393267, "sample_id": "us-code-38-8212-d94ada4847de30c9"}`
  evidence: `{"cosine_similarity": -0.315595999335, "hint_id": "modal-synthesis-8a488569f57e949a", "priority": 0.570993262342, "reconstruction_loss": 0.570993262342, "sample_id": "us-code-45-228a to 228c-76599549d4b51395"}`
  evidence: `{"cosine_similarity": 0.149793849391, "hint_id": "modal-synthesis-ce17f8ed63037b46", "priority": 0.377670236313, "reconstruction_loss": 0.377670236313, "sample_id": "us-code-42-7801-b02dfdbdb8b6107c"}`
  evidence: `{"cosine_similarity": 0.143176936513, "hint_id": "modal-synthesis-dbfb488e69bbca2b", "priority": 0.500208771329, "reconstruction_loss": 0.500208771329, "sample_id": "us-code-7-1609-b0db276509114d30"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.
