# packet-000019

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000019/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000019/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000019-20260518_091328

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-0a11bc6e75c96393` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0a11bc6e75c96393` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-0459506ade72a650", "priority": 0.374594393628, "sample_id": "us-code-21-379b-5e629c71113704b5"}`
  evidence: `{"hint_id": "modal-synthesis-125856a6d3439ef0", "priority": 0.500509866075, "sample_id": "us-code-49-1118.-f4102ab4b6cd739e"}`
  evidence: `{"hint_id": "modal-synthesis-aa85d2596a19a3aa", "priority": 0.915013144968, "sample_id": "us-code-16-5406-587a7f4a245f3c13"}`
  evidence: `{"hint_id": "modal-synthesis-c6f23c3cb375c65e", "priority": 0.61108186828, "sample_id": "us-code-12-5481-6a21da15cca2730b"}`
- `program-66b2334a5c32265f` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0a11bc6e75c96393` score `0.99541`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-55b723c419c0c154", "priority": 0.286161086793, "sample_id": "us-code-2-1341-0953371178320b06"}`
  evidence: `{"hint_id": "modal-synthesis-e719b547c433a9a1", "priority": 0.313993343963, "sample_id": "us-code-42-1500c-3cf28446a4418c3b"}`
  evidence: `{"hint_id": "modal-synthesis-f75e03ace38d5097", "priority": 0.304307755491, "sample_id": "us-code-42-3797aa-a1bd6223a0df015d"}`
  evidence: `{"hint_id": "modal-synthesis-fa49020bf6f83534", "priority": 0.605454270093, "sample_id": "us-code-26-6688-faa4a47aed02ba86"}`
- `program-264a8117e19d196a` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0a11bc6e75c96393` score `0.99522`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-731e965732c7bbc8", "priority": 0.38185294257, "sample_id": "us-code-20-1472-805b4875835f483a"}`
  evidence: `{"hint_id": "modal-synthesis-a9ffa02fd79f951a", "priority": 0.763102469369, "sample_id": "us-code-16-460iii-4-aa834016adcc86bf"}`
  evidence: `{"hint_id": "modal-synthesis-d86265528b962a76", "priority": 0.197936754336, "sample_id": "us-code-18-706-4dd528404c310241"}`
  evidence: `{"hint_id": "modal-synthesis-e98313bb654b0221", "priority": 0.361404616071, "sample_id": "us-code-16-824o-484f99e8978d7c55"}`

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
- `program-0a11bc6e75c96393`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0a11bc6e75c96393` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.600299818238`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-16-5406-587a7f4a245f3c13, us-code-12-5481-6a21da15cca2730b, us-code-49-1118.-f4102ab4b6cd739e, us-code-21-379b-5e629c71113704b5`
  evidence: `{"hint_id": "modal-synthesis-0459506ade72a650", "priority": 0.374594393628, "sample_id": "us-code-21-379b-5e629c71113704b5"}`
  evidence: `{"hint_id": "modal-synthesis-125856a6d3439ef0", "priority": 0.500509866075, "sample_id": "us-code-49-1118.-f4102ab4b6cd739e"}`
  evidence: `{"hint_id": "modal-synthesis-aa85d2596a19a3aa", "priority": 0.915013144968, "sample_id": "us-code-16-5406-587a7f4a245f3c13"}`
  evidence: `{"hint_id": "modal-synthesis-c6f23c3cb375c65e", "priority": 0.61108186828, "sample_id": "us-code-12-5481-6a21da15cca2730b"}`
- `program-66b2334a5c32265f`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0a11bc6e75c96393` score `0.99541`
  loss: `autoencoder_residual_cluster` = `0.377479114085`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-26-6688-faa4a47aed02ba86, us-code-42-1500c-3cf28446a4418c3b, us-code-42-3797aa-a1bd6223a0df015d, us-code-2-1341-0953371178320b06`
  evidence: `{"hint_id": "modal-synthesis-55b723c419c0c154", "priority": 0.286161086793, "sample_id": "us-code-2-1341-0953371178320b06"}`
  evidence: `{"hint_id": "modal-synthesis-e719b547c433a9a1", "priority": 0.313993343963, "sample_id": "us-code-42-1500c-3cf28446a4418c3b"}`
  evidence: `{"hint_id": "modal-synthesis-f75e03ace38d5097", "priority": 0.304307755491, "sample_id": "us-code-42-3797aa-a1bd6223a0df015d"}`
  evidence: `{"hint_id": "modal-synthesis-fa49020bf6f83534", "priority": 0.605454270093, "sample_id": "us-code-26-6688-faa4a47aed02ba86"}`
- `program-264a8117e19d196a`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-0a11bc6e75c96393` score `0.99522`
  loss: `autoencoder_residual_cluster` = `0.426074195587`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-16-460iii-4-aa834016adcc86bf, us-code-20-1472-805b4875835f483a, us-code-16-824o-484f99e8978d7c55, us-code-18-706-4dd528404c310241`
  evidence: `{"hint_id": "modal-synthesis-731e965732c7bbc8", "priority": 0.38185294257, "sample_id": "us-code-20-1472-805b4875835f483a"}`
  evidence: `{"hint_id": "modal-synthesis-a9ffa02fd79f951a", "priority": 0.763102469369, "sample_id": "us-code-16-460iii-4-aa834016adcc86bf"}`
  evidence: `{"hint_id": "modal-synthesis-d86265528b962a76", "priority": 0.197936754336, "sample_id": "us-code-18-706-4dd528404c310241"}`
  evidence: `{"hint_id": "modal-synthesis-e98313bb654b0221", "priority": 0.361404616071, "sample_id": "us-code-16-824o-484f99e8978d7c55"}`
