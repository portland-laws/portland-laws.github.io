# packet-000055

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000055/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000055/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000055-20260518_144737

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-799bf84abd23fcda` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-799bf84abd23fcda` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-33998cbf6a32a94b", "priority": 0.356233867765, "sample_id": "us-code-16-6804-262347e40e3f269e"}`
  evidence: `{"hint_id": "modal-synthesis-77aa1da71a3c8c76", "priority": 0.659413870679, "sample_id": "us-code-43-641.-04c06de9984aabe7"}`
  evidence: `{"hint_id": "modal-synthesis-b6a61b2bbdc96b51", "priority": 0.433218694108, "sample_id": "us-code-21-619-6c53879113090cdf"}`
  evidence: `{"hint_id": "modal-synthesis-ce3a4550802de7f5", "priority": 0.652330473134, "sample_id": "us-code-42-295.-ce0ec4d108b2d50e"}`
- `program-4c4bb1013c761f08` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-799bf84abd23fcda` score `0.994258`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-1649a3fca984e0b8", "priority": 0.490745711775, "sample_id": "us-code-19-3805-5725b663613c136d"}`
  evidence: `{"hint_id": "modal-synthesis-177844659c9e7126", "priority": 0.392018560778, "sample_id": "us-code-50-4515.-5665f6babe528bb9"}`
  evidence: `{"hint_id": "modal-synthesis-39a779cfd87bd227", "priority": 0.381302104733, "sample_id": "us-code-16-470m-5b20cbea12d3e062"}`
  evidence: `{"hint_id": "modal-synthesis-5d8b2d915a9b1b3c", "priority": 0.416723312177, "sample_id": "us-code-7-2225-f88bace0f3d32763"}`
- `program-91c60a457b5e8718` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-799bf84abd23fcda` score `0.993722`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-4e2b199bc6175d54", "priority": 0.443717159942, "sample_id": "us-code-19-129-1fcce33b4dd6fbde"}`
  evidence: `{"hint_id": "modal-synthesis-a1b67317d1e40c0f", "priority": 0.09837576533, "sample_id": "us-code-19-2152-963c4912623d7e46"}`
  evidence: `{"hint_id": "modal-synthesis-fcbc2b7e0ee15e03", "priority": 0.688670428528, "sample_id": "us-code-16-272c-53498b96929c5f7e"}`
  evidence: `{"hint_id": "modal-synthesis-ffeef787e02d89e4", "priority": 0.314992898114, "sample_id": "us-code-19-1613a-a15973dbf00d581e"}`

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
- `program-799bf84abd23fcda`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-799bf84abd23fcda` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.525299226422`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-43-641.-04c06de9984aabe7, us-code-42-295.-ce0ec4d108b2d50e, us-code-21-619-6c53879113090cdf, us-code-16-6804-262347e40e3f269e`
  evidence: `{"hint_id": "modal-synthesis-33998cbf6a32a94b", "priority": 0.356233867765, "sample_id": "us-code-16-6804-262347e40e3f269e"}`
  evidence: `{"hint_id": "modal-synthesis-77aa1da71a3c8c76", "priority": 0.659413870679, "sample_id": "us-code-43-641.-04c06de9984aabe7"}`
  evidence: `{"hint_id": "modal-synthesis-b6a61b2bbdc96b51", "priority": 0.433218694108, "sample_id": "us-code-21-619-6c53879113090cdf"}`
  evidence: `{"hint_id": "modal-synthesis-ce3a4550802de7f5", "priority": 0.652330473134, "sample_id": "us-code-42-295.-ce0ec4d108b2d50e"}`
- `program-4c4bb1013c761f08`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-799bf84abd23fcda` score `0.994258`
  loss: `autoencoder_residual_cluster` = `0.420197422366`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-19-3805-5725b663613c136d, us-code-7-2225-f88bace0f3d32763, us-code-50-4515.-5665f6babe528bb9, us-code-16-470m-5b20cbea12d3e062`
  evidence: `{"hint_id": "modal-synthesis-1649a3fca984e0b8", "priority": 0.490745711775, "sample_id": "us-code-19-3805-5725b663613c136d"}`
  evidence: `{"hint_id": "modal-synthesis-177844659c9e7126", "priority": 0.392018560778, "sample_id": "us-code-50-4515.-5665f6babe528bb9"}`
  evidence: `{"hint_id": "modal-synthesis-39a779cfd87bd227", "priority": 0.381302104733, "sample_id": "us-code-16-470m-5b20cbea12d3e062"}`
  evidence: `{"hint_id": "modal-synthesis-5d8b2d915a9b1b3c", "priority": 0.416723312177, "sample_id": "us-code-7-2225-f88bace0f3d32763"}`
- `program-91c60a457b5e8718`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-799bf84abd23fcda` score `0.993722`
  loss: `autoencoder_residual_cluster` = `0.386439062979`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-16-272c-53498b96929c5f7e, us-code-19-129-1fcce33b4dd6fbde, us-code-19-1613a-a15973dbf00d581e, us-code-19-2152-963c4912623d7e46`
  evidence: `{"hint_id": "modal-synthesis-4e2b199bc6175d54", "priority": 0.443717159942, "sample_id": "us-code-19-129-1fcce33b4dd6fbde"}`
  evidence: `{"hint_id": "modal-synthesis-a1b67317d1e40c0f", "priority": 0.09837576533, "sample_id": "us-code-19-2152-963c4912623d7e46"}`
  evidence: `{"hint_id": "modal-synthesis-fcbc2b7e0ee15e03", "priority": 0.688670428528, "sample_id": "us-code-16-272c-53498b96929c5f7e"}`
  evidence: `{"hint_id": "modal-synthesis-ffeef787e02d89e4", "priority": 0.314992898114, "sample_id": "us-code-19-1613a-a15973dbf00d581e"}`
