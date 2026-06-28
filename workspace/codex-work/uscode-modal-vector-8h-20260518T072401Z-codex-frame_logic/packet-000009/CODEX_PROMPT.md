# packet-000009

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000009/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000009/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000009-20260518_075130

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-54364add167a0591` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-54364add167a0591` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-10b5f5d5b66a15a4", "priority": 0.700534426581, "sample_id": "us-code-20-6692-a93d8062b79e3918"}`
  evidence: `{"hint_id": "modal-synthesis-64739db0be1d56cc", "priority": 0.540225108428, "sample_id": "us-code-42-13705.-6104fe4efa445f77"}`
  evidence: `{"hint_id": "modal-synthesis-7fdc50848d322251", "priority": 0.629973055709, "sample_id": "us-code-49-30308.-3dcdf369e9002109"}`
  evidence: `{"hint_id": "modal-synthesis-995f208a3df7f2bf", "priority": 0.574389187781, "sample_id": "us-code-20-4451-c336bf3b2714e1af"}`
- `program-bd0fbe7d2f5e2471` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-54364add167a0591` score `0.994635`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-075e38e12f6be84d", "priority": 0.505966614873, "sample_id": "us-code-30-1264-7adfeffcc1753ff0"}`
  evidence: `{"hint_id": "modal-synthesis-24edd7e69ffc7756", "priority": 0.87682197794, "sample_id": "us-code-16-460x-9-908f36f6fcd27905"}`
  evidence: `{"hint_id": "modal-synthesis-a6cf63857ef77ed6", "priority": 0.313039082509, "sample_id": "us-code-21-360ll-11684335ce2f2caa"}`
  evidence: `{"hint_id": "modal-synthesis-d9f5854b2171649d", "priority": 0.282584580137, "sample_id": "us-code-49-10904.-4e57a60d8b4c8369"}`
- `program-1962da648b1b5f60` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-54364add167a0591` score `0.994632`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-24b776d25c8c6d46", "priority": 0.462307748481, "sample_id": "us-code-26-4972-1f4aeead9cb8d7a4"}`
  evidence: `{"hint_id": "modal-synthesis-7714b9010eb37d45", "priority": 0.585431913016, "sample_id": "us-code-29-3222-cd9982a1ebd83367"}`
  evidence: `{"hint_id": "modal-synthesis-89907934da81b279", "priority": 0.248122808396, "sample_id": "us-code-16-460eee-2-151f071e709ab648"}`
  evidence: `{"hint_id": "modal-synthesis-da0062873a23dfdd", "priority": 0.627443526617, "sample_id": "us-code-5-1203-c9451c6b0e587874"}`

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
- `program-54364add167a0591`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-54364add167a0591` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.611280444625`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-20-6692-a93d8062b79e3918, us-code-49-30308.-3dcdf369e9002109, us-code-20-4451-c336bf3b2714e1af, us-code-42-13705.-6104fe4efa445f77`
  evidence: `{"hint_id": "modal-synthesis-10b5f5d5b66a15a4", "priority": 0.700534426581, "sample_id": "us-code-20-6692-a93d8062b79e3918"}`
  evidence: `{"hint_id": "modal-synthesis-64739db0be1d56cc", "priority": 0.540225108428, "sample_id": "us-code-42-13705.-6104fe4efa445f77"}`
  evidence: `{"hint_id": "modal-synthesis-7fdc50848d322251", "priority": 0.629973055709, "sample_id": "us-code-49-30308.-3dcdf369e9002109"}`
  evidence: `{"hint_id": "modal-synthesis-995f208a3df7f2bf", "priority": 0.574389187781, "sample_id": "us-code-20-4451-c336bf3b2714e1af"}`
- `program-bd0fbe7d2f5e2471`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-54364add167a0591` score `0.994635`
  loss: `autoencoder_residual_cluster` = `0.494603063865`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-16-460x-9-908f36f6fcd27905, us-code-30-1264-7adfeffcc1753ff0, us-code-21-360ll-11684335ce2f2caa, us-code-49-10904.-4e57a60d8b4c8369`
  evidence: `{"hint_id": "modal-synthesis-075e38e12f6be84d", "priority": 0.505966614873, "sample_id": "us-code-30-1264-7adfeffcc1753ff0"}`
  evidence: `{"hint_id": "modal-synthesis-24edd7e69ffc7756", "priority": 0.87682197794, "sample_id": "us-code-16-460x-9-908f36f6fcd27905"}`
  evidence: `{"hint_id": "modal-synthesis-a6cf63857ef77ed6", "priority": 0.313039082509, "sample_id": "us-code-21-360ll-11684335ce2f2caa"}`
  evidence: `{"hint_id": "modal-synthesis-d9f5854b2171649d", "priority": 0.282584580137, "sample_id": "us-code-49-10904.-4e57a60d8b4c8369"}`
- `program-1962da648b1b5f60`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-54364add167a0591` score `0.994632`
  loss: `autoencoder_residual_cluster` = `0.480826499127`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-5-1203-c9451c6b0e587874, us-code-29-3222-cd9982a1ebd83367, us-code-26-4972-1f4aeead9cb8d7a4, us-code-16-460eee-2-151f071e709ab648`
  evidence: `{"hint_id": "modal-synthesis-24b776d25c8c6d46", "priority": 0.462307748481, "sample_id": "us-code-26-4972-1f4aeead9cb8d7a4"}`
  evidence: `{"hint_id": "modal-synthesis-7714b9010eb37d45", "priority": 0.585431913016, "sample_id": "us-code-29-3222-cd9982a1ebd83367"}`
  evidence: `{"hint_id": "modal-synthesis-89907934da81b279", "priority": 0.248122808396, "sample_id": "us-code-16-460eee-2-151f071e709ab648"}`
  evidence: `{"hint_id": "modal-synthesis-da0062873a23dfdd", "priority": 0.627443526617, "sample_id": "us-code-5-1203-c9451c6b0e587874"}`
