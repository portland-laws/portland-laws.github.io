# packet-000056

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000056/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000056/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000056-20260518_145536

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-055247f996c965a8` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-055247f996c965a8` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-7f53038b3f0d2888", "priority": 0.744687968606, "sample_id": "us-code-10-186-420e6415d46dc17d"}`
  evidence: `{"hint_id": "modal-synthesis-918be45725774bcb", "priority": 0.413778579455, "sample_id": "us-code-6-1154-42d0dd5ec5341bfd"}`
  evidence: `{"hint_id": "modal-synthesis-a1b794bd8b1aa686", "priority": 0.544141867966, "sample_id": "us-code-38-3323-8d1776565a6d5ff4"}`
  evidence: `{"hint_id": "modal-synthesis-d6db69ec12f72943", "priority": 0.393206087093, "sample_id": "us-code-44-1305.-63681ee5004ef4e4"}`
- `program-e3b7cc75b75fbc70` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-055247f996c965a8` score `0.992321`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-35271f655e4be469", "priority": 0.394185320872, "sample_id": "us-code-16-62-ebf83094eb1b1966"}`
  evidence: `{"hint_id": "modal-synthesis-a49bebf1806af83e", "priority": 0.261800525907, "sample_id": "us-code-43-1605.-504689e44c5588b1"}`
  evidence: `{"hint_id": "modal-synthesis-e66e8088167f45d6", "priority": 0.367978796766, "sample_id": "us-code-22-3660-b188f699b2063242"}`
  evidence: `{"hint_id": "modal-synthesis-ffb172f98b8ec4c2", "priority": 0.221777779193, "sample_id": "us-code-10-2642-cc50cbe697b6f291"}`
- `program-7c627f3d8171016a` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-055247f996c965a8` score `0.992135`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-4ab13d8ea073eff4", "priority": 0.424007839448, "sample_id": "us-code-7-1341-45d5b03d9abea474"}`
  evidence: `{"hint_id": "modal-synthesis-c069afdfde651942", "priority": 0.495408562502, "sample_id": "us-code-28-3010-ec7367efc1ef5126"}`
  evidence: `{"hint_id": "modal-synthesis-c7bcfe11201f3c71", "priority": 0.558414263938, "sample_id": "us-code-18-470-b33ab957b2c8c744"}`
  evidence: `{"hint_id": "modal-synthesis-f4d87f268bf13587", "priority": 0.545698180318, "sample_id": "us-code-42-2624 to 2628.-1baa32ea8781e124"}`

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
- `program-055247f996c965a8`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-055247f996c965a8` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.52395362578`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-10-186-420e6415d46dc17d, us-code-38-3323-8d1776565a6d5ff4, us-code-6-1154-42d0dd5ec5341bfd, us-code-44-1305.-63681ee5004ef4e4`
  evidence: `{"hint_id": "modal-synthesis-7f53038b3f0d2888", "priority": 0.744687968606, "sample_id": "us-code-10-186-420e6415d46dc17d"}`
  evidence: `{"hint_id": "modal-synthesis-918be45725774bcb", "priority": 0.413778579455, "sample_id": "us-code-6-1154-42d0dd5ec5341bfd"}`
  evidence: `{"hint_id": "modal-synthesis-a1b794bd8b1aa686", "priority": 0.544141867966, "sample_id": "us-code-38-3323-8d1776565a6d5ff4"}`
  evidence: `{"hint_id": "modal-synthesis-d6db69ec12f72943", "priority": 0.393206087093, "sample_id": "us-code-44-1305.-63681ee5004ef4e4"}`
- `program-e3b7cc75b75fbc70`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-055247f996c965a8` score `0.992321`
  loss: `autoencoder_residual_cluster` = `0.311435605685`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-16-62-ebf83094eb1b1966, us-code-22-3660-b188f699b2063242, us-code-43-1605.-504689e44c5588b1, us-code-10-2642-cc50cbe697b6f291`
  evidence: `{"hint_id": "modal-synthesis-35271f655e4be469", "priority": 0.394185320872, "sample_id": "us-code-16-62-ebf83094eb1b1966"}`
  evidence: `{"hint_id": "modal-synthesis-a49bebf1806af83e", "priority": 0.261800525907, "sample_id": "us-code-43-1605.-504689e44c5588b1"}`
  evidence: `{"hint_id": "modal-synthesis-e66e8088167f45d6", "priority": 0.367978796766, "sample_id": "us-code-22-3660-b188f699b2063242"}`
  evidence: `{"hint_id": "modal-synthesis-ffb172f98b8ec4c2", "priority": 0.221777779193, "sample_id": "us-code-10-2642-cc50cbe697b6f291"}`
- `program-7c627f3d8171016a`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-055247f996c965a8` score `0.992135`
  loss: `autoencoder_residual_cluster` = `0.505882211552`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-18-470-b33ab957b2c8c744, us-code-42-2624 to 2628.-1baa32ea8781e124, us-code-28-3010-ec7367efc1ef5126, us-code-7-1341-45d5b03d9abea474`
  evidence: `{"hint_id": "modal-synthesis-4ab13d8ea073eff4", "priority": 0.424007839448, "sample_id": "us-code-7-1341-45d5b03d9abea474"}`
  evidence: `{"hint_id": "modal-synthesis-c069afdfde651942", "priority": 0.495408562502, "sample_id": "us-code-28-3010-ec7367efc1ef5126"}`
  evidence: `{"hint_id": "modal-synthesis-c7bcfe11201f3c71", "priority": 0.558414263938, "sample_id": "us-code-18-470-b33ab957b2c8c744"}`
  evidence: `{"hint_id": "modal-synthesis-f4d87f268bf13587", "priority": 0.545698180318, "sample_id": "us-code-42-2624 to 2628.-1baa32ea8781e124"}`
