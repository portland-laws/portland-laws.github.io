# packet-000027

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000027/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000027/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000027-20260518_101843

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-8d901316cf6571d8` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-8d901316cf6571d8` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-a60f5748b0d5e79c", "priority": 0.765890502144, "sample_id": "us-code-10-247-2178e10f8388afbd"}`
  evidence: `{"hint_id": "modal-synthesis-b652274803fb8717", "priority": 0.387742482595, "sample_id": "us-code-28-92-e1782fae7ceb7d0d"}`
  evidence: `{"hint_id": "modal-synthesis-c11fec25cd9b3778", "priority": 0.581404516111, "sample_id": "us-code-36-150510-8508360bb4174d31"}`
  evidence: `{"hint_id": "modal-synthesis-d0f8e7bbbc1e1f7c", "priority": 0.542363827503, "sample_id": "us-code-52-10305.-bdcb0d70692f2c2d"}`
- `program-7c04cc5806620bda` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-8d901316cf6571d8` score `0.993296`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-3c824c5b3930f47f", "priority": 0.576041570117, "sample_id": "us-code-26-3201-bd4f34df4d869df4"}`
  evidence: `{"hint_id": "modal-synthesis-551e797846eacad3", "priority": 0.526349126079, "sample_id": "us-code-13-303-bcfda0ce2292fef5"}`
  evidence: `{"hint_id": "modal-synthesis-e040bf2ec57a8920", "priority": 0.432653281983, "sample_id": "us-code-19-3702-fb4c53c1694c688a"}`
  evidence: `{"hint_id": "modal-synthesis-e6057db365054e1b", "priority": 0.477755204574, "sample_id": "us-code-7-7311-017c4d8b52982ca1"}`
- `program-90a2279cf63c5847` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-8d901316cf6571d8` score `0.993214`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-762e559b84a88288", "priority": 0.497515983542, "sample_id": "us-code-50-4404.-6d49b3d0dad76216"}`
  evidence: `{"hint_id": "modal-synthesis-976bcc26bbdadb31", "priority": 0.399033690718, "sample_id": "us-code-38-1713-e735515303a49cfa"}`
  evidence: `{"hint_id": "modal-synthesis-dc1b418a51e52910", "priority": 0.197526194208, "sample_id": "us-code-26-4241-60de6f4e807ab1a0"}`
  evidence: `{"hint_id": "modal-synthesis-ec09e717171db042", "priority": 0.407150683423, "sample_id": "us-code-25-992-2ec4bf6af06b8e98"}`

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
- `program-8d901316cf6571d8`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-8d901316cf6571d8` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.569350332088`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-10-247-2178e10f8388afbd, us-code-36-150510-8508360bb4174d31, us-code-52-10305.-bdcb0d70692f2c2d, us-code-28-92-e1782fae7ceb7d0d`
  evidence: `{"hint_id": "modal-synthesis-a60f5748b0d5e79c", "priority": 0.765890502144, "sample_id": "us-code-10-247-2178e10f8388afbd"}`
  evidence: `{"hint_id": "modal-synthesis-b652274803fb8717", "priority": 0.387742482595, "sample_id": "us-code-28-92-e1782fae7ceb7d0d"}`
  evidence: `{"hint_id": "modal-synthesis-c11fec25cd9b3778", "priority": 0.581404516111, "sample_id": "us-code-36-150510-8508360bb4174d31"}`
  evidence: `{"hint_id": "modal-synthesis-d0f8e7bbbc1e1f7c", "priority": 0.542363827503, "sample_id": "us-code-52-10305.-bdcb0d70692f2c2d"}`
- `program-7c04cc5806620bda`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-8d901316cf6571d8` score `0.993296`
  loss: `autoencoder_residual_cluster` = `0.503199795688`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-26-3201-bd4f34df4d869df4, us-code-13-303-bcfda0ce2292fef5, us-code-7-7311-017c4d8b52982ca1, us-code-19-3702-fb4c53c1694c688a`
  evidence: `{"hint_id": "modal-synthesis-3c824c5b3930f47f", "priority": 0.576041570117, "sample_id": "us-code-26-3201-bd4f34df4d869df4"}`
  evidence: `{"hint_id": "modal-synthesis-551e797846eacad3", "priority": 0.526349126079, "sample_id": "us-code-13-303-bcfda0ce2292fef5"}`
  evidence: `{"hint_id": "modal-synthesis-e040bf2ec57a8920", "priority": 0.432653281983, "sample_id": "us-code-19-3702-fb4c53c1694c688a"}`
  evidence: `{"hint_id": "modal-synthesis-e6057db365054e1b", "priority": 0.477755204574, "sample_id": "us-code-7-7311-017c4d8b52982ca1"}`
- `program-90a2279cf63c5847`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-8d901316cf6571d8` score `0.993214`
  loss: `autoencoder_residual_cluster` = `0.375306637973`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-50-4404.-6d49b3d0dad76216, us-code-25-992-2ec4bf6af06b8e98, us-code-38-1713-e735515303a49cfa, us-code-26-4241-60de6f4e807ab1a0`
  evidence: `{"hint_id": "modal-synthesis-762e559b84a88288", "priority": 0.497515983542, "sample_id": "us-code-50-4404.-6d49b3d0dad76216"}`
  evidence: `{"hint_id": "modal-synthesis-976bcc26bbdadb31", "priority": 0.399033690718, "sample_id": "us-code-38-1713-e735515303a49cfa"}`
  evidence: `{"hint_id": "modal-synthesis-dc1b418a51e52910", "priority": 0.197526194208, "sample_id": "us-code-26-4241-60de6f4e807ab1a0"}`
  evidence: `{"hint_id": "modal-synthesis-ec09e717171db042", "priority": 0.407150683423, "sample_id": "us-code-25-992-2ec4bf6af06b8e98"}`
