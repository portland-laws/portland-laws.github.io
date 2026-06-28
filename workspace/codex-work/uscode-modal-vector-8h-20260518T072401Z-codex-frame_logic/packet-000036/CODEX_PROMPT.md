# packet-000036

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000036/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000036/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000036-20260518_113748

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-525bf5333d8bd14d` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-525bf5333d8bd14d` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-35c39b08292ade6c", "priority": 0.544191436109, "sample_id": "us-code-5-408-4c3f3a9c1e2ec77d"}`
  evidence: `{"hint_id": "modal-synthesis-d0c635357951ec93", "priority": 0.799061789987, "sample_id": "us-code-49-44718.-e33d4fe6efe48835"}`
  evidence: `{"hint_id": "modal-synthesis-d8713a39861adadf", "priority": 0.638803195267, "sample_id": "us-code-14-323-84bfe15bba62b796"}`
  evidence: `{"hint_id": "modal-synthesis-e535e61982ca82a1", "priority": 0.259677014082, "sample_id": "us-code-12-359-79de307df5a44e1a"}`
- `program-4b65c0da2fd2a097` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-525bf5333d8bd14d` score `0.992248`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-2249a182e6d1fac6", "priority": 0.445644549679, "sample_id": "us-code-28-2245-d1ea16b1ac50014b"}`
  evidence: `{"hint_id": "modal-synthesis-5a4de7808a618ae8", "priority": 0.683242663074, "sample_id": "us-code-20-6082-6a0e64a86e194aa8"}`
  evidence: `{"hint_id": "modal-synthesis-b7f36339cf2c23f7", "priority": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
  evidence: `{"hint_id": "modal-synthesis-df1698d621960e92", "priority": 0.178369647054, "sample_id": "us-code-7-2143-cbad35cf9d290cf0"}`
- `program-9d978185a2123d46` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-525bf5333d8bd14d` score `0.992118`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-0aefe75629c50ae7", "priority": 0.451945455978, "sample_id": "us-code-25-450-c265a65e885d4655"}`
  evidence: `{"hint_id": "modal-synthesis-747784d65fbf9ccb", "priority": 0.38652989852, "sample_id": "us-code-5-5348-f0250f870668e53f"}`
  evidence: `{"hint_id": "modal-synthesis-b0838741feb90b97", "priority": 0.429321524033, "sample_id": "us-code-5-6384-8b50e16be95927f5"}`
  evidence: `{"hint_id": "modal-synthesis-bddfc3114b0398c5", "priority": 0.878819708818, "sample_id": "us-code-26-6503-4c2f54aaf561a1a1"}`

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
- `program-525bf5333d8bd14d`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-525bf5333d8bd14d` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.560433358861`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-49-44718.-e33d4fe6efe48835, us-code-14-323-84bfe15bba62b796, us-code-5-408-4c3f3a9c1e2ec77d, us-code-12-359-79de307df5a44e1a`
  evidence: `{"hint_id": "modal-synthesis-35c39b08292ade6c", "priority": 0.544191436109, "sample_id": "us-code-5-408-4c3f3a9c1e2ec77d"}`
  evidence: `{"hint_id": "modal-synthesis-d0c635357951ec93", "priority": 0.799061789987, "sample_id": "us-code-49-44718.-e33d4fe6efe48835"}`
  evidence: `{"hint_id": "modal-synthesis-d8713a39861adadf", "priority": 0.638803195267, "sample_id": "us-code-14-323-84bfe15bba62b796"}`
  evidence: `{"hint_id": "modal-synthesis-e535e61982ca82a1", "priority": 0.259677014082, "sample_id": "us-code-12-359-79de307df5a44e1a"}`
- `program-4b65c0da2fd2a097`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-525bf5333d8bd14d` score `0.992248`
  loss: `autoencoder_residual_cluster` = `0.479600120315`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-20-6082-6a0e64a86e194aa8, us-code-15-1717a-f876cffa460ff996, us-code-28-2245-d1ea16b1ac50014b, us-code-7-2143-cbad35cf9d290cf0`
  evidence: `{"hint_id": "modal-synthesis-2249a182e6d1fac6", "priority": 0.445644549679, "sample_id": "us-code-28-2245-d1ea16b1ac50014b"}`
  evidence: `{"hint_id": "modal-synthesis-5a4de7808a618ae8", "priority": 0.683242663074, "sample_id": "us-code-20-6082-6a0e64a86e194aa8"}`
  evidence: `{"hint_id": "modal-synthesis-b7f36339cf2c23f7", "priority": 0.611143621452, "sample_id": "us-code-15-1717a-f876cffa460ff996"}`
  evidence: `{"hint_id": "modal-synthesis-df1698d621960e92", "priority": 0.178369647054, "sample_id": "us-code-7-2143-cbad35cf9d290cf0"}`
- `program-9d978185a2123d46`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-525bf5333d8bd14d` score `0.992118`
  loss: `autoencoder_residual_cluster` = `0.536654146837`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-26-6503-4c2f54aaf561a1a1, us-code-25-450-c265a65e885d4655, us-code-5-6384-8b50e16be95927f5, us-code-5-5348-f0250f870668e53f`
  evidence: `{"hint_id": "modal-synthesis-0aefe75629c50ae7", "priority": 0.451945455978, "sample_id": "us-code-25-450-c265a65e885d4655"}`
  evidence: `{"hint_id": "modal-synthesis-747784d65fbf9ccb", "priority": 0.38652989852, "sample_id": "us-code-5-5348-f0250f870668e53f"}`
  evidence: `{"hint_id": "modal-synthesis-b0838741feb90b97", "priority": 0.429321524033, "sample_id": "us-code-5-6384-8b50e16be95927f5"}`
  evidence: `{"hint_id": "modal-synthesis-bddfc3114b0398c5", "priority": 0.878819708818, "sample_id": "us-code-26-6503-4c2f54aaf561a1a1"}`
