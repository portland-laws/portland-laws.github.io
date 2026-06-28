# packet-000049

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000049/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000049/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000049-20260518_135829

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-4842a8da379627b6` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4842a8da379627b6` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-3651739775b22848", "priority": 0.225202568903, "sample_id": "us-code-15-2057b-7aef94f132ebd139"}`
  evidence: `{"hint_id": "modal-synthesis-6179792c4cdeb364", "priority": 0.511042531006, "sample_id": "us-code-22-1643e-0a884e2cb66bbe1a"}`
  evidence: `{"hint_id": "modal-synthesis-9caac87ff08be24a", "priority": 0.350469465262, "sample_id": "us-code-42-7572.-af6a8ab17a492b46"}`
  evidence: `{"hint_id": "modal-synthesis-be55dafae6619b96", "priority": 1.119277838482, "sample_id": "us-code-54-101920.-2a8a1acc9abc25ac"}`
- `program-fa530f28a67e1705` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4842a8da379627b6` score `0.994199`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-32e7547aa08fb56c", "priority": 0.540469298418, "sample_id": "us-code-5-3346-ca5aa0d4985f9d91"}`
  evidence: `{"hint_id": "modal-synthesis-71f11a5af1e93d9d", "priority": 0.528981288918, "sample_id": "us-code-15-7704-5f3f0287e06eb49f"}`
  evidence: `{"hint_id": "modal-synthesis-8827e4e681884eaa", "priority": 0.287484286895, "sample_id": "us-code-38-1720D-93b4ea776e53aa1a"}`
  evidence: `{"hint_id": "modal-synthesis-cbefef49ac67d899", "priority": 0.399149744893, "sample_id": "us-code-15-1681v-7645f91f20487c09"}`
- `program-2d84e663d2005454` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4842a8da379627b6` score `0.994172`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-27e01a2e4bd0c764", "priority": 0.291446790609, "sample_id": "us-code-42-16092.-a56ba67c3bcab0b8"}`
  evidence: `{"hint_id": "modal-synthesis-33db755bf4d0b705", "priority": 0.310702160803, "sample_id": "us-code-10-8669-847a57d070221b74"}`
  evidence: `{"hint_id": "modal-synthesis-395254ddc8b67df0", "priority": 0.487950161311, "sample_id": "us-code-43-1470.-845d9dceb9d264ab"}`
  evidence: `{"hint_id": "modal-synthesis-a9b9c29cc9465233", "priority": 0.204671694544, "sample_id": "us-code-33-741-6af99be469b97863"}`

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
- `program-4842a8da379627b6`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4842a8da379627b6` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.551498100913`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-54-101920.-2a8a1acc9abc25ac, us-code-22-1643e-0a884e2cb66bbe1a, us-code-42-7572.-af6a8ab17a492b46, us-code-15-2057b-7aef94f132ebd139`
  evidence: `{"hint_id": "modal-synthesis-3651739775b22848", "priority": 0.225202568903, "sample_id": "us-code-15-2057b-7aef94f132ebd139"}`
  evidence: `{"hint_id": "modal-synthesis-6179792c4cdeb364", "priority": 0.511042531006, "sample_id": "us-code-22-1643e-0a884e2cb66bbe1a"}`
  evidence: `{"hint_id": "modal-synthesis-9caac87ff08be24a", "priority": 0.350469465262, "sample_id": "us-code-42-7572.-af6a8ab17a492b46"}`
  evidence: `{"hint_id": "modal-synthesis-be55dafae6619b96", "priority": 1.119277838482, "sample_id": "us-code-54-101920.-2a8a1acc9abc25ac"}`
- `program-fa530f28a67e1705`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4842a8da379627b6` score `0.994199`
  loss: `autoencoder_residual_cluster` = `0.439021154781`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-5-3346-ca5aa0d4985f9d91, us-code-15-7704-5f3f0287e06eb49f, us-code-15-1681v-7645f91f20487c09, us-code-38-1720D-93b4ea776e53aa1a`
  evidence: `{"hint_id": "modal-synthesis-32e7547aa08fb56c", "priority": 0.540469298418, "sample_id": "us-code-5-3346-ca5aa0d4985f9d91"}`
  evidence: `{"hint_id": "modal-synthesis-71f11a5af1e93d9d", "priority": 0.528981288918, "sample_id": "us-code-15-7704-5f3f0287e06eb49f"}`
  evidence: `{"hint_id": "modal-synthesis-8827e4e681884eaa", "priority": 0.287484286895, "sample_id": "us-code-38-1720D-93b4ea776e53aa1a"}`
  evidence: `{"hint_id": "modal-synthesis-cbefef49ac67d899", "priority": 0.399149744893, "sample_id": "us-code-15-1681v-7645f91f20487c09"}`
- `program-2d84e663d2005454`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4842a8da379627b6` score `0.994172`
  loss: `autoencoder_residual_cluster` = `0.323692701817`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-43-1470.-845d9dceb9d264ab, us-code-10-8669-847a57d070221b74, us-code-42-16092.-a56ba67c3bcab0b8, us-code-33-741-6af99be469b97863`
  evidence: `{"hint_id": "modal-synthesis-27e01a2e4bd0c764", "priority": 0.291446790609, "sample_id": "us-code-42-16092.-a56ba67c3bcab0b8"}`
  evidence: `{"hint_id": "modal-synthesis-33db755bf4d0b705", "priority": 0.310702160803, "sample_id": "us-code-10-8669-847a57d070221b74"}`
  evidence: `{"hint_id": "modal-synthesis-395254ddc8b67df0", "priority": 0.487950161311, "sample_id": "us-code-43-1470.-845d9dceb9d264ab"}`
  evidence: `{"hint_id": "modal-synthesis-a9b9c29cc9465233", "priority": 0.204671694544, "sample_id": "us-code-33-741-6af99be469b97863"}`
