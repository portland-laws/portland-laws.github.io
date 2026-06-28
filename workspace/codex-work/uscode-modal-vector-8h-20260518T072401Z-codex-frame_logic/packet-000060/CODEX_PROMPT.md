# packet-000060

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000060/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000060/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000060-20260518_153202

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-d7b896720a050a4c` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-d7b896720a050a4c` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-2e9948cca17dc16b", "priority": 0.863282190566, "sample_id": "us-code-51-60604.-82ff42829bbdeb0f"}`
  evidence: `{"hint_id": "modal-synthesis-46351072fa83eef4", "priority": 0.332509516781, "sample_id": "us-code-20-6111-6077986049984507"}`
  evidence: `{"hint_id": "modal-synthesis-4abb29066d219d10", "priority": 0.407340628107, "sample_id": "us-code-22-1643m-5242bf8f9ab76629"}`
  evidence: `{"hint_id": "modal-synthesis-786013fcbaee423c", "priority": 0.468636621947, "sample_id": "us-code-42-14041a-880d93707d48f95b"}`
- `program-4cea3afcfc69ea06` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-d7b896720a050a4c` score `0.993914`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-19d5611a57a09d6e", "priority": 0.418711070831, "sample_id": "us-code-42-16616-68a38d45f443c269"}`
  evidence: `{"hint_id": "modal-synthesis-2816e8e865b27f48", "priority": 0.368451827725, "sample_id": "us-code-3-4-a7eca1aa946379a7"}`
  evidence: `{"hint_id": "modal-synthesis-9ccd6548ca03142e", "priority": 0.590016238099, "sample_id": "us-code-42-13493.-04325ff575ddbe2d"}`
  evidence: `{"hint_id": "modal-synthesis-a093fac2cbd7a93b", "priority": 0.443156360435, "sample_id": "us-code-22-502-8391025895e1c668"}`
- `program-86f591348d9c5397` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-d7b896720a050a4c` score `0.993064`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-29d4155d6dad2cc6", "priority": 0.205142422293, "sample_id": "us-code-18-1966-88802ff0ce21894d"}`
  evidence: `{"hint_id": "modal-synthesis-a4567980d3855866", "priority": 0.215632146928, "sample_id": "us-code-19-26-080fd37d9883d2c5"}`
  evidence: `{"hint_id": "modal-synthesis-d0333155543ed3ca", "priority": 0.54430626008, "sample_id": "us-code-22-4316-b24128e438629db7"}`
  evidence: `{"hint_id": "modal-synthesis-d05a9502d9fa9bea", "priority": 0.33241382884, "sample_id": "us-code-20-241d-6425f6dd457124bb"}`

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
- `program-d7b896720a050a4c`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-d7b896720a050a4c` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.51794223935`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-51-60604.-82ff42829bbdeb0f, us-code-42-14041a-880d93707d48f95b, us-code-22-1643m-5242bf8f9ab76629, us-code-20-6111-6077986049984507`
  evidence: `{"hint_id": "modal-synthesis-2e9948cca17dc16b", "priority": 0.863282190566, "sample_id": "us-code-51-60604.-82ff42829bbdeb0f"}`
  evidence: `{"hint_id": "modal-synthesis-46351072fa83eef4", "priority": 0.332509516781, "sample_id": "us-code-20-6111-6077986049984507"}`
  evidence: `{"hint_id": "modal-synthesis-4abb29066d219d10", "priority": 0.407340628107, "sample_id": "us-code-22-1643m-5242bf8f9ab76629"}`
  evidence: `{"hint_id": "modal-synthesis-786013fcbaee423c", "priority": 0.468636621947, "sample_id": "us-code-42-14041a-880d93707d48f95b"}`
- `program-4cea3afcfc69ea06`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-d7b896720a050a4c` score `0.993914`
  loss: `autoencoder_residual_cluster` = `0.455083874272`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-13493.-04325ff575ddbe2d, us-code-22-502-8391025895e1c668, us-code-42-16616-68a38d45f443c269, us-code-3-4-a7eca1aa946379a7`
  evidence: `{"hint_id": "modal-synthesis-19d5611a57a09d6e", "priority": 0.418711070831, "sample_id": "us-code-42-16616-68a38d45f443c269"}`
  evidence: `{"hint_id": "modal-synthesis-2816e8e865b27f48", "priority": 0.368451827725, "sample_id": "us-code-3-4-a7eca1aa946379a7"}`
  evidence: `{"hint_id": "modal-synthesis-9ccd6548ca03142e", "priority": 0.590016238099, "sample_id": "us-code-42-13493.-04325ff575ddbe2d"}`
  evidence: `{"hint_id": "modal-synthesis-a093fac2cbd7a93b", "priority": 0.443156360435, "sample_id": "us-code-22-502-8391025895e1c668"}`
- `program-86f591348d9c5397`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-d7b896720a050a4c` score `0.993064`
  loss: `autoencoder_residual_cluster` = `0.324373664535`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-22-4316-b24128e438629db7, us-code-20-241d-6425f6dd457124bb, us-code-19-26-080fd37d9883d2c5, us-code-18-1966-88802ff0ce21894d`
  evidence: `{"hint_id": "modal-synthesis-29d4155d6dad2cc6", "priority": 0.205142422293, "sample_id": "us-code-18-1966-88802ff0ce21894d"}`
  evidence: `{"hint_id": "modal-synthesis-a4567980d3855866", "priority": 0.215632146928, "sample_id": "us-code-19-26-080fd37d9883d2c5"}`
  evidence: `{"hint_id": "modal-synthesis-d0333155543ed3ca", "priority": 0.54430626008, "sample_id": "us-code-22-4316-b24128e438629db7"}`
  evidence: `{"hint_id": "modal-synthesis-d05a9502d9fa9bea", "priority": 0.33241382884, "sample_id": "us-code-20-241d-6425f6dd457124bb"}`
