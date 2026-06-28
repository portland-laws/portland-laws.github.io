# packet-000042

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000042/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000042/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000042-20260518_125051

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-2ceaa175f5af352f` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-2ceaa175f5af352f` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-6097a323bf1c502c", "priority": 0.848068870366, "sample_id": "us-code-16-41-f7738ea40b878036"}`
  evidence: `{"hint_id": "modal-synthesis-7534f49a9d8e04f2", "priority": 0.163236551087, "sample_id": "us-code-33-2323a-217f5c65f49ef8cd"}`
  evidence: `{"hint_id": "modal-synthesis-dec71d84d4ed2f22", "priority": 0.644735002805, "sample_id": "us-code-39-409-749bcc752db53bbd"}`
  evidence: `{"hint_id": "modal-synthesis-ecd1257b6ad5a294", "priority": 0.488699559906, "sample_id": "us-code-31-5117-b97ad4e89fee3ab5"}`
- `program-efb3d823c376fbe6` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-2ceaa175f5af352f` score `0.993043`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-0c2034a05c682f1a", "priority": 0.370251756829, "sample_id": "us-code-12-3044-d28b2ea8a927ffba"}`
  evidence: `{"hint_id": "modal-synthesis-1d70a894398e4f73", "priority": 0.575590931301, "sample_id": "us-code-31-7506-66ad72e4339d90c2"}`
  evidence: `{"hint_id": "modal-synthesis-601a1fe54470aa7a", "priority": 0.286038567125, "sample_id": "us-code-16-5601-2f669f04bb001a36"}`
  evidence: `{"hint_id": "modal-synthesis-8cd1bb2c465f9a90", "priority": 0.316397036372, "sample_id": "us-code-16-800-9617be70b6be147f"}`
- `program-71e537a1ddc4f0b1` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-2ceaa175f5af352f` score `0.992159`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-455c47ffe4424ce6", "priority": 0.355006179563, "sample_id": "us-code-25-51-b0f49682f9dfa228"}`
  evidence: `{"hint_id": "modal-synthesis-d4ed414a68593ed7", "priority": 0.434722412709, "sample_id": "us-code-26-6671-0699b447cf6fa07d"}`
  evidence: `{"hint_id": "modal-synthesis-f82caf167e36afa4", "priority": 0.197844854345, "sample_id": "us-code-25-564m-dee77e626d5d85a3"}`
  evidence: `{"hint_id": "modal-synthesis-fc4bf13b76d15607", "priority": 0.776976462585, "sample_id": "us-code-42-6932.-4c8798ac1bdcb191"}`

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
- `program-2ceaa175f5af352f`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-2ceaa175f5af352f` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.536184996041`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-16-41-f7738ea40b878036, us-code-39-409-749bcc752db53bbd, us-code-31-5117-b97ad4e89fee3ab5, us-code-33-2323a-217f5c65f49ef8cd`
  evidence: `{"hint_id": "modal-synthesis-6097a323bf1c502c", "priority": 0.848068870366, "sample_id": "us-code-16-41-f7738ea40b878036"}`
  evidence: `{"hint_id": "modal-synthesis-7534f49a9d8e04f2", "priority": 0.163236551087, "sample_id": "us-code-33-2323a-217f5c65f49ef8cd"}`
  evidence: `{"hint_id": "modal-synthesis-dec71d84d4ed2f22", "priority": 0.644735002805, "sample_id": "us-code-39-409-749bcc752db53bbd"}`
  evidence: `{"hint_id": "modal-synthesis-ecd1257b6ad5a294", "priority": 0.488699559906, "sample_id": "us-code-31-5117-b97ad4e89fee3ab5"}`
- `program-efb3d823c376fbe6`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-2ceaa175f5af352f` score `0.993043`
  loss: `autoencoder_residual_cluster` = `0.387069572907`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-31-7506-66ad72e4339d90c2, us-code-12-3044-d28b2ea8a927ffba, us-code-16-800-9617be70b6be147f, us-code-16-5601-2f669f04bb001a36`
  evidence: `{"hint_id": "modal-synthesis-0c2034a05c682f1a", "priority": 0.370251756829, "sample_id": "us-code-12-3044-d28b2ea8a927ffba"}`
  evidence: `{"hint_id": "modal-synthesis-1d70a894398e4f73", "priority": 0.575590931301, "sample_id": "us-code-31-7506-66ad72e4339d90c2"}`
  evidence: `{"hint_id": "modal-synthesis-601a1fe54470aa7a", "priority": 0.286038567125, "sample_id": "us-code-16-5601-2f669f04bb001a36"}`
  evidence: `{"hint_id": "modal-synthesis-8cd1bb2c465f9a90", "priority": 0.316397036372, "sample_id": "us-code-16-800-9617be70b6be147f"}`
- `program-71e537a1ddc4f0b1`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-2ceaa175f5af352f` score `0.992159`
  loss: `autoencoder_residual_cluster` = `0.441137477301`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-42-6932.-4c8798ac1bdcb191, us-code-26-6671-0699b447cf6fa07d, us-code-25-51-b0f49682f9dfa228, us-code-25-564m-dee77e626d5d85a3`
  evidence: `{"hint_id": "modal-synthesis-455c47ffe4424ce6", "priority": 0.355006179563, "sample_id": "us-code-25-51-b0f49682f9dfa228"}`
  evidence: `{"hint_id": "modal-synthesis-d4ed414a68593ed7", "priority": 0.434722412709, "sample_id": "us-code-26-6671-0699b447cf6fa07d"}`
  evidence: `{"hint_id": "modal-synthesis-f82caf167e36afa4", "priority": 0.197844854345, "sample_id": "us-code-25-564m-dee77e626d5d85a3"}`
  evidence: `{"hint_id": "modal-synthesis-fc4bf13b76d15607", "priority": 0.776976462585, "sample_id": "us-code-42-6932.-4c8798ac1bdcb191"}`
