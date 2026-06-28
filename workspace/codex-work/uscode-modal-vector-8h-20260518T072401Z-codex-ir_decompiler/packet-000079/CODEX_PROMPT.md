# packet-000079

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000079/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000079/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000079-20260518_153213

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-02b8ad33e93a6db4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-02b8ad33e93a6db4` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.564983309931, "hint_id": "modal-synthesis-a415bd92b36581bf", "priority": 0.588941731362, "reconstruction_loss": 0.588941731362, "sample_id": "us-code-5-9002-1c2ba40d178aa81a"}`
  evidence: `{"cosine_similarity": 0.409806154476, "hint_id": "modal-synthesis-dcf0878777c14bca", "priority": 0.321417397872, "reconstruction_loss": 0.321417397872, "sample_id": "us-code-47-1457.-04440790685b2dec"}`
  evidence: `{"cosine_similarity": 0.066557094496, "hint_id": "modal-synthesis-e008b7f5025fd12b", "priority": 0.530168307011, "reconstruction_loss": 0.530168307011, "sample_id": "us-code-54-302301.-a36391e5bb095b0b"}`
  evidence: `{"cosine_similarity": 0.006166498917, "hint_id": "modal-synthesis-ed96182127e4b7ca", "priority": 0.406989029297, "reconstruction_loss": 0.406989029297, "sample_id": "us-code-43-616tttt to 616yyyy.-1e019a04fbdab0cb"}`
- `program-fadc9393881b00ef` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-02b8ad33e93a6db4` score `0.990268`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.551179145898, "hint_id": "modal-synthesis-14e4b2905c289e04", "priority": 0.30641594231, "reconstruction_loss": 0.30641594231, "sample_id": "us-code-38-3521-38b11c27b1e95c79"}`
  evidence: `{"cosine_similarity": -0.147096191105, "hint_id": "modal-synthesis-3b9e5194ef299a7d", "priority": 0.487710282651, "reconstruction_loss": 0.487710282651, "sample_id": "us-code-36-80303-f96e6e38a0da30ca"}`
  evidence: `{"cosine_similarity": -0.657790822988, "hint_id": "modal-synthesis-de1ec036e5fe159d", "priority": 0.518244754445, "reconstruction_loss": 0.518244754445, "sample_id": "us-code-42-8771 to 8780.-08cca7111531eedf"}`
  evidence: `{"cosine_similarity": 0.488366178569, "hint_id": "modal-synthesis-f9e627eae08c8642", "priority": 0.233614074285, "reconstruction_loss": 0.233614074285, "sample_id": "us-code-50-731 to 739.-7ae8581aaecc734e"}`
- `program-f79f5172c3ffc759` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-02b8ad33e93a6db4` score `0.989422`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.30201521477, "hint_id": "modal-synthesis-108c5179e2c98707", "priority": 0.357164379607, "reconstruction_loss": 0.357164379607, "sample_id": "us-code-43-451a.-087f06b103bc4a63"}`
  evidence: `{"cosine_similarity": 0.432624047609, "hint_id": "modal-synthesis-7969098b166fbd1a", "priority": 0.437919052434, "reconstruction_loss": 0.437919052434, "sample_id": "us-code-50-31 to 39.-36a4389acae72564"}`
  evidence: `{"cosine_similarity": -0.190498986961, "hint_id": "modal-synthesis-c80b2048992e9954", "priority": 0.390925219445, "reconstruction_loss": 0.390925219445, "sample_id": "us-code-22-1084-a27cb8a44b1a0917"}`
  evidence: `{"cosine_similarity": -0.050491962808, "hint_id": "modal-synthesis-e44661c88f983d6c", "priority": 0.597549407203, "reconstruction_loss": 0.597549407203, "sample_id": "us-code-7-2009aa-9-4aae340ae3858487"}`

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
- `program-02b8ad33e93a6db4`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-02b8ad33e93a6db4` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.461879116385`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-5-9002-1c2ba40d178aa81a, us-code-54-302301.-a36391e5bb095b0b, us-code-43-616tttt to 616yyyy.-1e019a04fbdab0cb, us-code-47-1457.-04440790685b2dec`
  evidence: `{"cosine_similarity": -0.564983309931, "hint_id": "modal-synthesis-a415bd92b36581bf", "priority": 0.588941731362, "reconstruction_loss": 0.588941731362, "sample_id": "us-code-5-9002-1c2ba40d178aa81a"}`
  evidence: `{"cosine_similarity": 0.409806154476, "hint_id": "modal-synthesis-dcf0878777c14bca", "priority": 0.321417397872, "reconstruction_loss": 0.321417397872, "sample_id": "us-code-47-1457.-04440790685b2dec"}`
  evidence: `{"cosine_similarity": 0.066557094496, "hint_id": "modal-synthesis-e008b7f5025fd12b", "priority": 0.530168307011, "reconstruction_loss": 0.530168307011, "sample_id": "us-code-54-302301.-a36391e5bb095b0b"}`
  evidence: `{"cosine_similarity": 0.006166498917, "hint_id": "modal-synthesis-ed96182127e4b7ca", "priority": 0.406989029297, "reconstruction_loss": 0.406989029297, "sample_id": "us-code-43-616tttt to 616yyyy.-1e019a04fbdab0cb"}`
- `program-fadc9393881b00ef`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-02b8ad33e93a6db4` score `0.990268`
  loss: `autoencoder_residual_cluster` = `0.386496263423`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-8771 to 8780.-08cca7111531eedf, us-code-36-80303-f96e6e38a0da30ca, us-code-38-3521-38b11c27b1e95c79, us-code-50-731 to 739.-7ae8581aaecc734e`
  evidence: `{"cosine_similarity": 0.551179145898, "hint_id": "modal-synthesis-14e4b2905c289e04", "priority": 0.30641594231, "reconstruction_loss": 0.30641594231, "sample_id": "us-code-38-3521-38b11c27b1e95c79"}`
  evidence: `{"cosine_similarity": -0.147096191105, "hint_id": "modal-synthesis-3b9e5194ef299a7d", "priority": 0.487710282651, "reconstruction_loss": 0.487710282651, "sample_id": "us-code-36-80303-f96e6e38a0da30ca"}`
  evidence: `{"cosine_similarity": -0.657790822988, "hint_id": "modal-synthesis-de1ec036e5fe159d", "priority": 0.518244754445, "reconstruction_loss": 0.518244754445, "sample_id": "us-code-42-8771 to 8780.-08cca7111531eedf"}`
  evidence: `{"cosine_similarity": 0.488366178569, "hint_id": "modal-synthesis-f9e627eae08c8642", "priority": 0.233614074285, "reconstruction_loss": 0.233614074285, "sample_id": "us-code-50-731 to 739.-7ae8581aaecc734e"}`
- `program-f79f5172c3ffc759`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-02b8ad33e93a6db4` score `0.989422`
  loss: `autoencoder_residual_cluster` = `0.445889514672`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-2009aa-9-4aae340ae3858487, us-code-50-31 to 39.-36a4389acae72564, us-code-22-1084-a27cb8a44b1a0917, us-code-43-451a.-087f06b103bc4a63`
  evidence: `{"cosine_similarity": 0.30201521477, "hint_id": "modal-synthesis-108c5179e2c98707", "priority": 0.357164379607, "reconstruction_loss": 0.357164379607, "sample_id": "us-code-43-451a.-087f06b103bc4a63"}`
  evidence: `{"cosine_similarity": 0.432624047609, "hint_id": "modal-synthesis-7969098b166fbd1a", "priority": 0.437919052434, "reconstruction_loss": 0.437919052434, "sample_id": "us-code-50-31 to 39.-36a4389acae72564"}`
  evidence: `{"cosine_similarity": -0.190498986961, "hint_id": "modal-synthesis-c80b2048992e9954", "priority": 0.390925219445, "reconstruction_loss": 0.390925219445, "sample_id": "us-code-22-1084-a27cb8a44b1a0917"}`
  evidence: `{"cosine_similarity": -0.050491962808, "hint_id": "modal-synthesis-e44661c88f983d6c", "priority": 0.597549407203, "reconstruction_loss": 0.597549407203, "sample_id": "us-code-7-2009aa-9-4aae340ae3858487"}`
